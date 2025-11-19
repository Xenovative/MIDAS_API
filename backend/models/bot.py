from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    avatar = Column(String(10), default="🤖")  # Emoji avatar
    
    # Model settings
    default_model = Column(String(100))
    default_provider = Column(String(50))
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer)
    
    # Metadata
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="bots")
    conversations = relationship("Conversation", back_populates="bot", cascade="all, delete-orphan")
