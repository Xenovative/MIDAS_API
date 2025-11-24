"""One-time script to clean up base64 images from database"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from backend.database import AsyncSessionLocal
from backend.models import Message

async def cleanup_base64_images():
    """Remove all base64 images from message meta_data"""
    async with AsyncSessionLocal() as db:
        # Get all messages with meta_data
        result = await db.execute(select(Message))
        messages = result.scalars().all()
        
        cleaned_count = 0
        for msg in messages:
            # Check meta_data
            if msg.meta_data and msg.meta_data.get("images"):
                images = msg.meta_data["images"]
                if images and isinstance(images, list):
                    first_img = str(images[0]) if images else ""
                    if len(first_img) > 100:
                        print(f"Cleaning message {msg.id} meta_data - has {len(first_img)} char base64")
                        msg.meta_data = {"images": []}
                        cleaned_count += 1
            
            # Check content (might have base64 embedded)
            if isinstance(msg.content, str) and len(msg.content) > 100000:
                print(f"Message {msg.id} has huge content: {len(msg.content)} chars")
                if "base64," in msg.content:
                    print(f"  -> Contains base64 data!")
                    cleaned_count += 1
        
        if cleaned_count > 0:
            await db.commit()
            print(f"✅ Cleaned {cleaned_count} messages")
        else:
            print("No base64 images found")

if __name__ == "__main__":
    asyncio.run(cleanup_base64_images())
