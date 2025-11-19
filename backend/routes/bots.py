from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.database import get_db
from backend.models import Bot, User
from backend.auth import get_current_user

router = APIRouter(prefix="/bots", tags=["bots"])


class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    avatar: str = "🤖"
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    is_public: bool = False


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar: Optional[str] = None
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class BotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    avatar: str
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    temperature: float
    max_tokens: Optional[int] = None
    creator_id: str
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=BotResponse)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new bot"""
    print(f"Creating bot for user: {current_user.username} (ID: {current_user.id})")
    print(f"Bot data: {bot_data.dict()}")
    
    try:
        bot = Bot(
            name=bot_data.name,
            description=bot_data.description,
            system_prompt=bot_data.system_prompt,
            avatar=bot_data.avatar,
            default_model=bot_data.default_model,
            default_provider=bot_data.default_provider,
            temperature=bot_data.temperature,
            max_tokens=bot_data.max_tokens,
            creator_id=current_user.id,
            is_public=bot_data.is_public
        )
        
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        
        print(f"Bot created successfully: {bot.id}")
        return bot
    except Exception as e:
        print(f"Error creating bot: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[BotResponse])
async def list_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all bots (user's own + public bots)"""
    # Get user's own bots
    result = await db.execute(
        select(Bot).where(
            Bot.creator_id == current_user.id,
            Bot.is_active == True
        )
    )
    user_bots = result.scalars().all()
    
    # Get public bots from other users
    result = await db.execute(
        select(Bot).where(
            Bot.is_public == True,
            Bot.is_active == True,
            Bot.creator_id != current_user.id
        )
    )
    public_bots = result.scalars().all()
    
    return list(user_bots) + list(public_bots)


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific bot"""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Check if user has access (owner or public bot)
    if bot.creator_id != current_user.id and not bot.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a bot"""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Only owner can update
    if bot.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can update this bot")
    
    # Update fields
    update_data = bot_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)
    
    await db.commit()
    await db.refresh(bot)
    
    return bot


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a bot"""
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Only owner can delete
    if bot.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can delete this bot")
    
    await db.delete(bot)
    await db.commit()
    
    return {"message": "Bot deleted successfully"}
