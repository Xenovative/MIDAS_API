"""
Document management routes for RAG functionality
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
import json
import asyncio
from backend.database import get_db
from backend.models import Bot, Document, User
from backend.auth import get_current_user
from backend.vector_store import vector_store
from backend.document_parser import document_parser
from backend.document_splitter import document_splitter
import aiofiles

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUpload(BaseModel):
    bot_id: Optional[str] = None
    conversation_id: Optional[str] = None
    content: str
    filename: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    bot_id: str
    filename: str
    chunk_count: int
    created_at: datetime


class DocumentSearchRequest(BaseModel):
    bot_id: str
    query: str
    top_k: int = 5
    similarity_threshold: float = 0.7


class DocumentSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    similarity: float
    chunk_index: int


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    doc_data: DocumentUpload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document for RAG (bot or conversation level)"""
    # Verify bot access if bot_id provided
    if doc_data.bot_id:
        result = await db.execute(select(Bot).where(Bot.id == doc_data.bot_id))
        bot = result.scalar_one_or_none()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        if bot.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the bot creator can upload documents")
        
        if not bot.use_rag:
            raise HTTPException(status_code=400, detail="RAG is not enabled for this bot")
    
    # Add document to vector store
    try:
        document_id = await vector_store.add_document(
            db=db,
            filename=doc_data.filename,
            content=doc_data.content,
            bot_id=doc_data.bot_id,
            conversation_id=doc_data.conversation_id,
            user_id=current_user.id if not doc_data.bot_id else None
        )
        
        # Fetch the created document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one()
        
        return document
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-file", response_model=DocumentResponse)
async def upload_document_file(
    file: UploadFile = File(...),
    bot_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a text file for RAG (bot or conversation level) - simple version without progress"""
    # Verify bot access if bot_id provided
    if bot_id:
        result = await db.execute(select(Bot).where(Bot.id == bot_id))
        bot = result.scalar_one_or_none()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        if bot.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the bot creator can upload documents")
        
        if not bot.use_rag:
            raise HTTPException(status_code=400, detail="RAG is not enabled for this bot")
    
    # Check if file format is supported
    if not document_parser.is_supported(file.filename):
        supported = ', '.join(document_parser.get_supported_extensions())
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: {supported}"
        )
    
    # Read and parse file content
    try:
        content = await file.read()
        
        # Check file size (warn if > 5MB)
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 5:
            print(f"⚠️  Large file detected: {file_size_mb:.2f}MB - this may take several minutes")
        
        text_content = document_parser.parse_bytes(content, file.filename)
        
        # Check text content size and auto-split if needed
        text_size_mb = len(text_content) / (1024 * 1024)
        
        if text_size_mb > 10:
            raise HTTPException(
                status_code=400, 
                detail=f"Document too large ({text_size_mb:.2f}MB). Maximum size is 10MB. Please split the document into smaller files."
            )
        
        # Auto-split large documents (> 2MB)
        if document_splitter.should_split(text_content):
            print(f"📊 Large document detected ({text_size_mb:.2f}MB) - auto-splitting enabled")
            parts = document_splitter.split_document(text_content, file.filename)
            
            # Upload each part separately
            uploaded_docs = []
            for part in parts:
                try:
                    doc_id = await vector_store.add_document(
                        db=db,
                        filename=part['filename'],
                        content=part['content'],
                        bot_id=bot_id,
                        conversation_id=conversation_id,
                        user_id=current_user.id if not bot_id else None,
                        batch_size=20
                    )
                    uploaded_docs.append(doc_id)
                    print(f"✅ Uploaded part {part['part_number']}/{part['total_parts']}")
                except Exception as e:
                    print(f"❌ Failed to upload part {part['part_number']}: {e}")
                    # Continue with other parts
            
            # Return first document as representative
            if uploaded_docs:
                result = await db.execute(select(Document).where(Document.id == uploaded_docs[0]))
                document = result.scalar_one()
                print(f"✅ All {len(parts)} parts uploaded successfully")
                return document
            else:
                raise HTTPException(status_code=500, detail="Failed to upload any document parts")
        
        # Normal upload for smaller documents
        if text_size_mb > 1:
            print(f"⚠️  Large text content: {text_size_mb:.2f}MB - processing will be slow")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")
    
    # Add document to vector store with batched processing
    try:
        document_id = await vector_store.add_document(
            db=db,
            filename=file.filename,
            content=text_content,
            bot_id=bot_id,
            conversation_id=conversation_id,
            user_id=current_user.id if not bot_id else None,
            batch_size=20  # Process 20 chunks at a time to save memory
        )
        
        # Fetch the created document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one()
        
        return document
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-file-stream")
async def upload_document_file_stream(
    file: UploadFile = File(...),
    bot_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a text file for RAG with progress streaming (SSE)"""
    
    # Use a queue to pass progress updates from callback to generator
    progress_queue = asyncio.Queue()
    
    async def generate_progress():
        try:
            # Verify bot access if bot_id provided
            if bot_id:
                result = await db.execute(select(Bot).where(Bot.id == bot_id))
                bot = result.scalar_one_or_none()
                
                if not bot:
                    yield f"data: {json.dumps({'error': 'Bot not found'})}\n\n"
                    return
                
                if bot.creator_id != current_user.id:
                    yield f"data: {json.dumps({'error': 'Only the bot creator can upload documents'})}\n\n"
                    return
                
                if not bot.use_rag:
                    yield f"data: {json.dumps({'error': 'RAG is not enabled for this bot'})}\n\n"
                    return
            
            # Check if file format is supported
            if not document_parser.is_supported(file.filename):
                supported = ', '.join(document_parser.get_supported_extensions())
                yield f"data: {json.dumps({'error': f'Unsupported file format. Supported: {supported}'})}\n\n"
                return
            
            # Read and parse file content
            print(f"📤 Starting upload: {file.filename}")
            yield f"data: {json.dumps({'progress': 0, 'status': 'Reading file...'})}\n\n"
            
            try:
                content = await file.read()
                print(f"📖 File read: {len(content)} bytes")
                yield f"data: {json.dumps({'progress': 5, 'status': 'Parsing document...'})}\n\n"
                
                text_content = document_parser.parse_bytes(content, file.filename)
                print(f"📝 Document parsed: {len(text_content)} characters")
                yield f"data: {json.dumps({'progress': 10, 'status': 'Document parsed successfully'})}\n\n"
            except ValueError as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                return
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Failed to parse document: {str(e)}'})}\n\n"
                return
            
            # Progress callback for vector store
            async def progress_callback(current, total, status):
                print(f"📊 Progress: {current}% - {status}")  # Console logging
                await progress_queue.put({'progress': current, 'total': total, 'status': status})
            
            # Start upload task
            upload_task = asyncio.create_task(
                vector_store.add_document(
                    db=db,
                    filename=file.filename,
                    content=text_content,
                    bot_id=bot_id,
                    conversation_id=conversation_id,
                    user_id=current_user.id if not bot_id else None,
                    batch_size=20,  # Reduced to save memory
                    progress_callback=progress_callback
                )
            )
            
            # Stream progress updates
            while not upload_task.done():
                try:
                    # Wait for progress update with timeout
                    update = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                    yield f"data: {json.dumps(update)}\n\n"
                except asyncio.TimeoutError:
                    continue
            
            # Drain any remaining updates
            while not progress_queue.empty():
                update = await progress_queue.get()
                yield f"data: {json.dumps(update)}\n\n"
            
            # Get result
            try:
                document_id = await upload_task
                
                # Fetch the created document
                result = await db.execute(select(Document).where(Document.id == document_id))
                document = result.scalar_one()
                
                yield f"data: {json.dumps({'progress': 100, 'status': 'Complete!', 'document': {'id': document.id, 'filename': document.filename, 'chunk_count': document.chunk_count}})}\n\n"
            except Exception as e:
                print(f"Error uploading document: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        except Exception as e:
            print(f"Unexpected error in stream: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': f'Unexpected error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/bot/{bot_id}", response_model=List[DocumentResponse])
async def list_bot_documents(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents for a bot"""
    # Verify bot exists and user has access
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.creator_id != current_user.id and not bot.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get documents
    result = await db.execute(
        select(Document).where(Document.bot_id == bot_id)
    )
    documents = result.scalars().all()
    
    return documents


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    # Get document
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify user has access to the bot
    result = await db.execute(select(Bot).where(Bot.id == document.bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot or bot.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the bot creator can delete documents")
    
    # Delete document
    await vector_store.delete_document(db, document_id)
    
    return {"message": "Document deleted successfully"}


@router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents(
    search_request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search documents for a bot (for testing)"""
    # Verify bot exists and user has access
    result = await db.execute(select(Bot).where(Bot.id == search_request.bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.creator_id != current_user.id and not bot.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Search
    results = await vector_store.search(
        db=db,
        bot_id=search_request.bot_id,
        query=search_request.query,
        top_k=search_request.top_k,
        similarity_threshold=search_request.similarity_threshold
    )
    
    return results
