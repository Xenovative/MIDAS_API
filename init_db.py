"""Initialize the database"""
import asyncio
from backend.database import engine, Base
from backend.models import Conversation, Message, AgentExecution, User, SystemSettings
from backend.model_permissions import ModelPermission, UserModelUsage

async def init_database():
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
