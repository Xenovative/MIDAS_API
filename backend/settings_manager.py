"""System settings manager"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import SystemSettings
import json

# Default settings
DEFAULT_SETTINGS = {
    "guest_enabled": {
        "value": "true",
        "description": "Allow guest access without authentication"
    },
    "guest_message_limit": {
        "value": "30",
        "description": "Daily message limit for guest users"
    },
    "guest_allowed_models": {
        "value": json.dumps([
            "gpt-3.5-turbo",
            "gpt-4o-mini",
            "claude-3-haiku-20240307"
        ]),
        "description": "List of models available to guest users"
    },
    "free_message_limit": {
        "value": "50",
        "description": "Daily message limit for free users"
    },
    "premium_message_limit": {
        "value": "999999",
        "description": "Daily message limit for premium users"
    }
}


async def get_setting(db: AsyncSession, key: str, default: str = None) -> str:
    """Get a system setting value"""
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        return setting.value
    
    # Return default from DEFAULT_SETTINGS or provided default
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key]["value"]
    
    return default


async def set_setting(db: AsyncSession, key: str, value: str, description: str = None):
    """Set a system setting value"""
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = value
        if description:
            setting.description = description
    else:
        setting = SystemSettings(
            key=key,
            value=value,
            description=description or DEFAULT_SETTINGS.get(key, {}).get("description")
        )
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    return setting


async def get_all_settings(db: AsyncSession) -> dict:
    """Get all system settings"""
    result = await db.execute(select(SystemSettings))
    settings = result.scalars().all()
    
    # Merge with defaults
    settings_dict = {}
    for key, default_data in DEFAULT_SETTINGS.items():
        settings_dict[key] = {
            "value": default_data["value"],
            "description": default_data["description"]
        }
    
    # Override with database values
    for setting in settings:
        settings_dict[setting.key] = {
            "value": setting.value,
            "description": setting.description
        }
    
    return settings_dict


async def is_guest_enabled(db: AsyncSession) -> bool:
    """Check if guest access is enabled"""
    value = await get_setting(db, "guest_enabled", "true")
    return value.lower() == "true"


async def get_guest_message_limit(db: AsyncSession) -> int:
    """Get guest message limit"""
    value = await get_setting(db, "guest_message_limit", "30")
    return int(value)


async def get_guest_allowed_models(db: AsyncSession) -> list:
    """Get list of models allowed for guests"""
    value = await get_setting(db, "guest_allowed_models", json.dumps([]))
    return json.loads(value)
