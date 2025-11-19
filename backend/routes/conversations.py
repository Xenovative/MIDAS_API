from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from backend.database import get_db
from backend.models import Conversation, Message
from backend.schemas import ConversationCreate, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/")
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    new_conversation = Conversation(title=conversation.title)
    db.add(new_conversation)
    await db.commit()
    await db.refresh(new_conversation)
    
    return {
        "id": new_conversation.id,
        "title": new_conversation.title,
        "created_at": new_conversation.created_at.isoformat(),
        "updated_at": new_conversation.updated_at.isoformat(),
        "messages": []
    }


@router.get("/")
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all conversations"""
    try:
        result = await db.execute(
            select(Conversation)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        # Manually load messages for each conversation
        response = []
        for conv in conversations:
            # Load messages separately
            messages_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at)
            )
            messages = messages_result.scalars().all()
            
            response.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "conversation_id": msg.conversation_id,
                        "role": msg.role,
                        "content": msg.content,
                        "model": msg.model,
                        "tokens": msg.tokens,
                        "meta_data": msg.meta_data,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            })
        
        return response
    except Exception as e:
        print(f"Error in list_conversations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific conversation with messages"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Load messages separately
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "model": msg.model,
                "tokens": msg.tokens,
                "meta_data": msg.meta_data,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "Conversation deleted successfully"}


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: str,
    db: AsyncSession = Depends(get_db)
):
    """Update conversation title"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.title = title
    await db.commit()
    await db.refresh(conversation)
    
    return conversation
