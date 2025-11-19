"""Create an admin user"""
import asyncio
from backend.database import AsyncSessionLocal
from backend.models import User
from backend.auth import get_password_hash
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("Admin user already exists!")
            print(f"Username: {existing_admin.username}")
            print(f"Email: {existing_admin.email}")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@midas.local",
            username="admin",
            hashed_password=get_password_hash("admin123"),  # Change this password!
            full_name="System Administrator",
            role="admin",
            is_active=True,
            daily_message_limit=999999
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        print("✓ Admin user created successfully!")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Password: admin123")
        print("\n⚠️  IMPORTANT: Change the admin password after first login!")

if __name__ == "__main__":
    asyncio.run(create_admin())
