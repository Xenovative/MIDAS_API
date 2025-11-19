"""Test conversations endpoint"""
import asyncio
import sys
from backend.database import AsyncSessionLocal
from backend.models import Conversation, Message
from sqlalchemy import select, desc

async def test_list_conversations():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Conversation)
                .order_by(desc(Conversation.updated_at))
                .limit(50)
            )
            conversations = result.scalars().all()
            print(f"Found {len(conversations)} conversations")
            
            # Try to serialize
            response = []
            for conv in conversations:
                print(f"Processing conversation: {conv.id}")
                
                # Load messages separately
                messages_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conv.id)
                )
                messages = messages_result.scalars().all()
                print(f"  Found {len(messages)} messages")
                
                conv_dict = {
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
                }
                response.append(conv_dict)
            
            print(f"\nSuccess! Response: {response}")
            return response
            
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    result = asyncio.run(test_list_conversations())
    if result is not None:
        print("\n✓ Test passed!")
    else:
        print("\n✗ Test failed!")
        sys.exit(1)
