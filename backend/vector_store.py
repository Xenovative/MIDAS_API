"""
Simple in-memory vector store for RAG
Uses cosine similarity for retrieval
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.models import Document, DocumentChunk
from backend.embeddings import embedding_provider


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a_arr = np.array(a)
    b_arr = np.array(b)
    
    dot_product = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


class VectorStore:
    """Vector store for document retrieval"""
    
    async def add_document(
        self,
        db: AsyncSession,
        filename: str,
        content: str,
        bot_id: str = None,
        conversation_id: str = None,
        user_id: str = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        batch_size: int = 20,  # Reduced from 50 to save memory
        progress_callback = None
    ) -> str:
        """
        Add a document to the vector store with batched processing
        Can be associated with bot, conversation, or user
        Returns the document ID
        
        Args:
            batch_size: Number of chunks to process at once (default 50)
            progress_callback: Optional callback function(current, total, status)
        """
        # Create document record
        document = Document(
            bot_id=bot_id,
            conversation_id=conversation_id,
            user_id=user_id,
            filename=filename,
            content=content,
            chunk_count=0
        )
        db.add(document)
        await db.flush()
        
        if progress_callback:
            await progress_callback(0, 100, "Splitting document into chunks...")
        
        # Split into chunks with progress
        print(f"📄 Starting to split document: {len(content)} characters")
        chunks = self._split_text(content, chunk_size, chunk_overlap)
        total_chunks = len(chunks)
        print(f"✂️  Document split into {total_chunks} chunks")
        
        print(f"\n{'='*60}")
        print(f"📄 Processing {filename}: {total_chunks} chunks")
        print(f"{'='*60}", flush=True)
        
        if progress_callback:
            await progress_callback(10, 100, f"Processing {total_chunks} chunks in batches...")
        
        # Process in batches to avoid memory issues
        processed = 0
        total_batches = (total_chunks + batch_size - 1) // batch_size
        
        import time
        import gc
        batch_times = []  # Track batch processing times for ETA
        
        for batch_num, batch_start in enumerate(range(0, total_chunks, batch_size), 1):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_chunks = chunks[batch_start:batch_end]
            
            # Progress for embedding generation
            embed_progress = 10 + int(((batch_start / total_chunks) * 85))
            if progress_callback:
                await progress_callback(
                    embed_progress,
                    100,
                    f"Batch {batch_num}/{total_batches}: Generating embeddings for {len(batch_chunks)} chunks (this may take 5-15 seconds)..."
                )
            
            # Generate embeddings for this batch
            batch_start_time = time.time()
            chunk_texts = [chunk["text"] for chunk in batch_chunks]
            embeddings = await embedding_provider.embed_texts(chunk_texts)
            embed_time = time.time() - batch_start_time
            print(f"  ⏱️  Embedding generation took {embed_time:.2f}s for {len(batch_chunks)} chunks", flush=True)
            
            # Progress for storing
            store_progress = 10 + int(((batch_start + len(batch_chunks) * 0.5) / total_chunks) * 85)
            if progress_callback:
                await progress_callback(
                    store_progress,
                    100,
                    f"Batch {batch_num}/{total_batches}: Storing chunks in database..."
                )
            
            # Store chunks with embeddings
            for i, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                chunk_record = DocumentChunk(
                    document_id=document.id,
                    chunk_index=batch_start + i,
                    content=chunk["text"],
                    embedding=embedding,
                    start_char=chunk["start"],
                    end_char=chunk["end"]
                )
                db.add(chunk_record)
            
            # Commit this batch
            await db.flush()
            
            # Free memory after each batch
            del chunk_texts
            del embeddings
            del batch_chunks
            gc.collect()  # Force garbage collection
            
            # Calculate batch time and ETA
            batch_total_time = time.time() - batch_start_time
            batch_times.append(batch_total_time)
            
            processed = batch_end
            progress_pct = 10 + int((processed / total_chunks) * 85)
            
            # Calculate ETA
            if len(batch_times) >= 2:
                avg_batch_time = sum(batch_times) / len(batch_times)
                remaining_batches = total_batches - batch_num
                eta_seconds = int(avg_batch_time * remaining_batches)
                eta_str = f" (ETA: ~{eta_seconds}s)" if eta_seconds > 0 else ""
            else:
                eta_str = ""
            
            if progress_callback:
                await progress_callback(
                    progress_pct, 
                    100, 
                    f"Batch {batch_num}/{total_batches} complete: {processed}/{total_chunks} chunks processed{eta_str}"
                )
            
            print(f"  ✓ Batch {batch_num}/{total_batches}: {processed}/{total_chunks} chunks (took {batch_total_time:.2f}s){eta_str}", flush=True)
        
        document.chunk_count = len(chunks)
        await db.commit()
        await db.refresh(document)
        
        if progress_callback:
            await progress_callback(100, 100, "Complete!")
        
        print(f"✅ Added document '{filename}' with {len(chunks)} chunks")
        print(f"{'='*60}\n", flush=True)
        return document.id
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        bot_id: str = None,
        conversation_id: str = None,
        user_id: str = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        include_adjacent: bool = True
    ) -> List[Dict]:
        """
        Search for relevant document chunks
        Can search by bot_id, conversation_id, or user_id
        Returns list of chunks with similarity scores
        
        Args:
            include_adjacent: If True, includes adjacent chunks for better context
        """
        # Generate query embedding
        query_embedding = await embedding_provider.embed_text(query)
        
        # Build query based on what's provided
        query_stmt = select(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id)
        
        conditions = []
        if bot_id:
            conditions.append(Document.bot_id == bot_id)
        if conversation_id:
            conditions.append(Document.conversation_id == conversation_id)
        if user_id:
            conditions.append(Document.user_id == user_id)
        
        if conditions:
            from sqlalchemy import or_
            query_stmt = query_stmt.where(or_(*conditions))
        
        result = await db.execute(query_stmt)
        chunks_with_docs = result.all()
        
        if not chunks_with_docs:
            return []
        
        # Calculate similarities
        results = []
        for chunk, doc in chunks_with_docs:
            similarity = cosine_similarity(query_embedding, chunk.embedding)
            
            if similarity >= similarity_threshold:
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "content": chunk.content,
                    "similarity": similarity,
                    "chunk_index": chunk.chunk_index
                })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results[:top_k]
        
        # Optionally include adjacent chunks for better context
        if include_adjacent and top_results:
            expanded_results = []
            added_chunk_ids = set()
            
            for result in top_results:
                doc_id = result['document_id']
                chunk_idx = result['chunk_index']
                
                # Get adjacent chunks (previous and next)
                adjacent_query = select(DocumentChunk).where(
                    DocumentChunk.document_id == doc_id,
                    DocumentChunk.chunk_index.in_([chunk_idx - 1, chunk_idx, chunk_idx + 1])
                ).order_by(DocumentChunk.chunk_index)
                
                adjacent_result = await db.execute(adjacent_query)
                adjacent_chunks = adjacent_result.scalars().all()
                
                # Add adjacent chunks with lower similarity score
                for adj_chunk in adjacent_chunks:
                    if adj_chunk.id not in added_chunk_ids:
                        # Mark adjacent chunks with adjusted similarity
                        is_main = adj_chunk.chunk_index == chunk_idx
                        expanded_results.append({
                            "chunk_id": adj_chunk.id,
                            "document_id": doc_id,
                            "filename": result['filename'],
                            "content": adj_chunk.content,
                            "similarity": result['similarity'] if is_main else result['similarity'] * 0.8,
                            "chunk_index": adj_chunk.chunk_index,
                            "is_adjacent": not is_main
                        })
                        added_chunk_ids.add(adj_chunk.id)
            
            # Sort by document and chunk index for coherent reading
            expanded_results.sort(key=lambda x: (x['document_id'], x['chunk_index']))
            return expanded_results
        
        return top_results
    
    async def delete_document(self, db: AsyncSession, document_id: str):
        """Delete a document and all its chunks"""
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if document:
            await db.delete(document)
            await db.commit()
            print(f"✅ Deleted document {document_id}")
    
    async def list_documents(self, db: AsyncSession, bot_id: str) -> List[Dict]:
        """List all documents for a bot"""
        result = await db.execute(
            select(Document).where(Document.bot_id == bot_id)
        )
        documents = result.scalars().all()
        
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "chunk_count": doc.chunk_count,
                "created_at": doc.created_at
            }
            for doc in documents
        ]
    
    def _split_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Dict]:
        """Split text into overlapping chunks (optimized for large documents)"""
        chunks = []
        start = 0
        text_length = len(text)
        chunk_count = 0
        
        # Estimate total chunks for progress
        estimated_chunks = text_length // (chunk_size - chunk_overlap) + 1
        print(f"  Estimated chunks: ~{estimated_chunks}")
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # Try to break at sentence boundary (simplified for speed)
            if end < text_length:
                # Look for nearest sentence ending (optimized)
                search_start = max(start, end - 100)  # Only search last 100 chars
                for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_punct = text.rfind(punct, search_start, end)
                    if last_punct != -1:
                        end = last_punct + len(punct)
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start": start,
                    "end": end
                })
                chunk_count += 1
                
                # Progress logging every 100 chunks
                if chunk_count % 100 == 0:
                    print(f"  Chunking progress: {chunk_count}/{estimated_chunks} chunks", flush=True)
            
            # Move start position with overlap
            start = end - chunk_overlap if end < text_length else text_length
        
        return chunks


# Global vector store instance
vector_store = VectorStore()
