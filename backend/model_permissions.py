"""Model permissions and rate limiting for different user tiers"""
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime
from backend.database import Base
from datetime import datetime
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class ModelPermission(Base):
    """Model access permissions for different user roles"""
    __tablename__ = "model_permissions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, nullable=False, index=True)  # e.g., "openai:gpt-4"
    provider = Column(String, nullable=False)
    
    # Visibility by role
    visible_to_guest = Column(Boolean, default=False)
    visible_to_free = Column(Boolean, default=True)
    visible_to_premium = Column(Boolean, default=True)
    visible_to_admin = Column(Boolean, default=True)
    
    # Rate limits (requests per hour, 0 = unlimited)
    guest_rate_limit = Column(Integer, default=0)  # 0 = not allowed
    free_rate_limit = Column(Integer, default=10)
    premium_rate_limit = Column(Integer, default=100)
    admin_rate_limit = Column(Integer, default=0)  # 0 = unlimited
    
    # Token limits (max tokens per request, 0 = model default)
    guest_max_tokens = Column(Integer, default=1000)
    free_max_tokens = Column(Integer, default=4000)
    premium_max_tokens = Column(Integer, default=0)  # 0 = unlimited
    admin_max_tokens = Column(Integer, default=0)  # 0 = unlimited
    
    # Additional metadata
    description = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserModelUsage(Base):
    """Track model usage per user for rate limiting"""
    __tablename__ = "user_model_usage"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    model_id = Column(String, nullable=False, index=True)
    
    # Usage tracking
    requests_this_hour = Column(Integer, default=0)
    tokens_this_hour = Column(Integer, default=0)
    last_request_time = Column(DateTime, default=datetime.utcnow)
    hour_start = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def get_model_permission(db, model_id: str):
    """Get model permission settings"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(ModelPermission).where(ModelPermission.model_id == model_id)
    )
    return result.scalar_one_or_none()


async def create_default_permissions(db, model_id: str, provider: str):
    """Create default permissions for a model"""
    permission = ModelPermission(
        model_id=model_id,
        provider=provider,
        visible_to_guest=False,
        visible_to_free=True,
        visible_to_premium=True,
        visible_to_admin=True,
        guest_rate_limit=0,
        free_rate_limit=10,
        premium_rate_limit=100,
        admin_rate_limit=0,
        guest_max_tokens=1000,
        free_max_tokens=4000,
        premium_max_tokens=0,
        admin_max_tokens=0,
        is_enabled=True
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


async def can_user_access_model(db, user_role: str, model_id: str) -> tuple[bool, str]:
    """Check if user can access a model"""
    permission = await get_model_permission(db, model_id)
    
    if not permission:
        # No permission set, allow by default for non-guests
        return (user_role != "guest", "Model not configured" if user_role == "guest" else "")
    
    if not permission.is_enabled:
        return (False, "Model is disabled")
    
    # Check visibility
    if user_role == "guest" and not permission.visible_to_guest:
        return (False, "Model not available for guests")
    elif user_role == "free" and not permission.visible_to_free:
        return (False, "Model not available for free users")
    elif user_role == "premium" and not permission.visible_to_premium:
        return (False, "Model not available for premium users")
    elif user_role == "admin" and not permission.visible_to_admin:
        return (False, "Model not available")
    
    return (True, "")


async def check_rate_limit(db, user_id: str, user_role: str, model_id: str) -> tuple[bool, str]:
    """Check if user has exceeded rate limit for a model"""
    from sqlalchemy import select
    from datetime import datetime, timedelta
    
    permission = await get_model_permission(db, model_id)
    if not permission:
        return (True, "")  # No limits if not configured
    
    # Get rate limit for user role
    rate_limit = 0
    if user_role == "guest":
        rate_limit = permission.guest_rate_limit
    elif user_role == "free":
        rate_limit = permission.free_rate_limit
    elif user_role == "premium":
        rate_limit = permission.premium_rate_limit
    elif user_role == "admin":
        rate_limit = permission.admin_rate_limit
    
    # 0 means unlimited
    if rate_limit == 0:
        return (True, "")
    
    # Get or create usage record
    result = await db.execute(
        select(UserModelUsage).where(
            UserModelUsage.user_id == user_id,
            UserModelUsage.model_id == model_id
        )
    )
    usage = result.scalar_one_or_none()
    
    now = datetime.utcnow()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    
    if not usage:
        # Create new usage record
        usage = UserModelUsage(
            user_id=user_id,
            model_id=model_id,
            requests_this_hour=0,
            hour_start=current_hour
        )
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
    
    # Check if we need to reset the counter
    usage_hour = usage.hour_start
    if usage_hour < current_hour:
        usage.requests_this_hour = 0
        usage.hour_start = current_hour
        await db.commit()
    
    # Check rate limit
    if usage.requests_this_hour >= rate_limit:
        return (False, f"Rate limit exceeded. Limit: {rate_limit} requests/hour")
    
    return (True, "")


async def increment_usage(db, user_id: str, model_id: str, tokens: int = 0):
    """Increment usage counter for a user and model"""
    from sqlalchemy import select
    from datetime import datetime
    
    result = await db.execute(
        select(UserModelUsage).where(
            UserModelUsage.user_id == user_id,
            UserModelUsage.model_id == model_id
        )
    )
    usage = result.scalar_one_or_none()
    
    if usage:
        usage.requests_this_hour += 1
        usage.tokens_this_hour += tokens
        usage.last_request_time = datetime.utcnow()
        usage.updated_at = datetime.utcnow()
        await db.commit()


async def get_max_tokens_for_user(db, user_role: str, model_id: str) -> int:
    """Get max tokens allowed for user role and model"""
    permission = await get_model_permission(db, model_id)
    
    if not permission:
        return 0  # 0 = use model default
    
    if user_role == "guest":
        return permission.guest_max_tokens
    elif user_role == "free":
        return permission.free_max_tokens
    elif user_role == "premium":
        return permission.premium_max_tokens
    elif user_role == "admin":
        return permission.admin_max_tokens
    
    return 0
