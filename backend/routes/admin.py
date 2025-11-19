from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from backend.database import get_db
from backend.models import User, Conversation, Message
from backend.model_permissions import (
    ModelPermission, get_model_permission, create_default_permissions
)
from backend.auth import require_admin, get_password_hash
from backend.settings_manager import get_all_settings, set_setting
import json
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])


class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[EmailStr] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "free"


class ModelPermissionUpdate(BaseModel):
    visible_to_guest: Optional[bool] = None
    visible_to_free: Optional[bool] = None
    visible_to_premium: Optional[bool] = None
    visible_to_admin: Optional[bool] = None
    guest_rate_limit: Optional[int] = None
    free_rate_limit: Optional[int] = None
    premium_rate_limit: Optional[int] = None
    admin_rate_limit: Optional[int] = None
    guest_max_tokens: Optional[int] = None
    free_max_tokens: Optional[int] = None
    premium_max_tokens: Optional[int] = None
    admin_max_tokens: Optional[int] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None


@router.get("/settings")
async def get_settings(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all system settings (admin only)"""
    settings = await get_all_settings(db)
    return settings


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    setting_update: SettingUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a system setting (admin only)"""
    # Validate certain settings
    if key == "guest_message_limit":
        try:
            limit = int(setting_update.value)
            if limit < 0:
                raise ValueError("Limit must be non-negative")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid value: {e}")
    
    elif key == "guest_allowed_models":
        try:
            models = json.loads(setting_update.value)
            if not isinstance(models, list):
                raise ValueError("Must be a JSON array")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    
    elif key == "guest_enabled":
        if setting_update.value.lower() not in ["true", "false"]:
            raise HTTPException(status_code=400, detail="Value must be 'true' or 'false'")
    
    setting = await set_setting(
        db,
        key,
        setting_update.value,
        setting_update.description
    )
    
    return {
        "key": setting.key,
        "value": setting.value,
        "description": setting.description
    }


@router.get("/stats")
async def get_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system statistics (admin only)"""
    # User stats
    total_users = await db.execute(select(func.count(User.id)))
    guest_users = await db.execute(
        select(func.count(User.id)).where(User.is_guest == True)
    )
    active_users = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    
    # Role counts
    admin_count = await db.execute(
        select(func.count(User.id)).where(User.role == "admin")
    )
    premium_count = await db.execute(
        select(func.count(User.id)).where(User.role == "premium")
    )
    free_count = await db.execute(
        select(func.count(User.id)).where(User.role == "free")
    )
    
    # Conversation stats
    total_conversations = await db.execute(select(func.count(Conversation.id)))
    
    # Message stats
    total_messages = await db.execute(select(func.count(Message.id)))
    
    return {
        "users": {
            "total": total_users.scalar(),
            "guests": guest_users.scalar(),
            "active": active_users.scalar(),
            "by_role": {
                "admin": admin_count.scalar(),
                "premium": premium_count.scalar(),
                "free": free_count.scalar()
            }
        },
        "conversations": {
            "total": total_conversations.scalar()
        },
        "messages": {
            "total": total_messages.scalar()
        }
    }


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    result = await db.execute(
        select(User)
        .order_by(desc(User.created_at))
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_guest": user.is_guest,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user details (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's conversation and message counts
    conv_count = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )
    msg_count = await db.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .where(Conversation.user_id == user_id)
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_guest": user.is_guest,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "stats": {
            "conversations": conv_count.scalar(),
            "messages": msg_count.scalar()
        }
    }


@router.post("/users")
async def create_user(
    user_data: UserCreate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate role
    if user_data.role not in ["admin", "premium", "free"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True,
        is_guest=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat()
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deactivating themselves
    if user.id == admin_user.id and user_update.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    # Prevent admin from demoting themselves
    if user.id == admin_user.id and user_update.role and user_update.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    # Update fields
    if user_update.role is not None:
        if user_update.role not in ["admin", "premium", "free", "guest"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = user_update.role
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    if user_update.email is not None:
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == user_update.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = user_update.email
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_guest": user.is_guest
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Delete user's conversations and messages (cascade should handle this)
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/models/permissions")
async def list_model_permissions(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all model permissions (admin only)"""
    result = await db.execute(select(ModelPermission))
    permissions = result.scalars().all()
    
    return {
        "permissions": [
            {
                "id": perm.id,
                "model_id": perm.model_id,
                "provider": perm.provider,
                "visible_to_guest": perm.visible_to_guest,
                "visible_to_free": perm.visible_to_free,
                "visible_to_premium": perm.visible_to_premium,
                "visible_to_admin": perm.visible_to_admin,
                "guest_rate_limit": perm.guest_rate_limit,
                "free_rate_limit": perm.free_rate_limit,
                "premium_rate_limit": perm.premium_rate_limit,
                "admin_rate_limit": perm.admin_rate_limit,
                "guest_max_tokens": perm.guest_max_tokens,
                "free_max_tokens": perm.free_max_tokens,
                "premium_max_tokens": perm.premium_max_tokens,
                "admin_max_tokens": perm.admin_max_tokens,
                "is_enabled": perm.is_enabled,
                "description": perm.description
            }
            for perm in permissions
        ]
    }


@router.post("/models/permissions/bulk-create")
async def bulk_create_permissions(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create permissions for all available models (admin only)"""
    from backend.llm_providers import llm_manager
    
    providers = await llm_manager.get_available_providers()
    created_count = 0
    
    for provider in providers:
        for model in provider["models"]:
            model_id = f"{provider['provider']}:{model['id']}"
            
            # Check if permission already exists
            existing = await get_model_permission(db, model_id)
            if not existing:
                await create_default_permissions(db, model_id, provider['provider'])
                created_count += 1
    
    return {
        "message": f"Created permissions for {created_count} models",
        "created_count": created_count
    }


@router.get("/models/permissions/{model_id}")
async def get_model_permission_details(
    model_id: str,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get model permission details (admin only)"""
    permission = await get_model_permission(db, model_id)
    
    if not permission:
        raise HTTPException(status_code=404, detail="Model permission not found")
    
    return {
        "id": permission.id,
        "model_id": permission.model_id,
        "provider": permission.provider,
        "visible_to_guest": permission.visible_to_guest,
        "visible_to_free": permission.visible_to_free,
        "visible_to_premium": permission.visible_to_premium,
        "visible_to_admin": permission.visible_to_admin,
        "guest_rate_limit": permission.guest_rate_limit,
        "free_rate_limit": permission.free_rate_limit,
        "premium_rate_limit": permission.premium_rate_limit,
        "admin_rate_limit": permission.admin_rate_limit,
        "guest_max_tokens": permission.guest_max_tokens,
        "free_max_tokens": permission.free_max_tokens,
        "premium_max_tokens": permission.premium_max_tokens,
        "admin_max_tokens": permission.admin_max_tokens,
        "is_enabled": permission.is_enabled,
        "description": permission.description
    }


@router.post("/models/permissions/{model_id}")
async def create_model_permission(
    model_id: str,
    provider: str,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create model permission with defaults (admin only)"""
    # Check if already exists
    existing = await get_model_permission(db, model_id)
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists for this model")
    
    permission = await create_default_permissions(db, model_id, provider)
    
    return {
        "id": permission.id,
        "model_id": permission.model_id,
        "provider": permission.provider,
        "message": "Model permission created with default settings"
    }


@router.patch("/models/permissions/{model_id}")
async def update_model_permission(
    model_id: str,
    updates: ModelPermissionUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update model permission (admin only)"""
    permission = await get_model_permission(db, model_id)
    
    if not permission:
        raise HTTPException(status_code=404, detail="Model permission not found")
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission, field, value)
    
    permission.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(permission)
    
    return {
        "id": permission.id,
        "model_id": permission.model_id,
        "message": "Model permission updated successfully"
    }


@router.delete("/models/permissions/{model_id}")
async def delete_model_permission(
    model_id: str,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete model permission (admin only)"""
    permission = await get_model_permission(db, model_id)
    
    if not permission:
        raise HTTPException(status_code=404, detail="Model permission not found")
    
    await db.delete(permission)
    await db.commit()
    
    return {"message": "Model permission deleted successfully"}
