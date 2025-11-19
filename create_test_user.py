"""Create a test user for login"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import AsyncSessionLocal
from backend.models import User
from backend.auth import get_password_hash

async def create_test_user():
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✓ Admin user already exists")
            print(f"  Username: {existing.username}")
            print(f"  Email: {existing.email}")
            print(f"  Role: {existing.role}")
            print(f"  Active: {existing.is_active}")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@midas.local",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            role="admin",
            is_active=True,
            is_guest=False
        )
        
        db.add(admin)
        await db.commit()
        
        print("✓ Admin user created successfully!")
        print("  Username: admin")
        print("  Email: admin@midas.local")
        print("  Password: admin123")
        print("\n⚠️  IMPORTANT: Change the admin password after first login!")

if __name__ == "__main__":
    asyncio.run(create_test_user())
