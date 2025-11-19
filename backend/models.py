from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=True, index=True)  # Nullable for guests
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)  # Nullable for guests
    full_name = Column(String, nullable=True)
    role = Column(String, default="free")  # guest, free, premium, admin
    is_active = Column(Boolean, default=True)
    is_guest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Usage limits
    daily_message_limit = Column(Integer, default=50)
    daily_messages_used = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bots = relationship("Bot", back_populates="creator", cascade="all, delete-orphan")


class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Bot(Base):
    __tablename__ = "bots"

    id = Column(String, primary_key=True, default=generate_uuid)
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
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="bots")
    conversations = relationship("Conversation", back_populates="bot", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Nullable for backward compatibility
    bot_id = Column(String, ForeignKey("bots.id"), nullable=True)  # Optional bot association
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", backref="conversations")
    bot = relationship("Bot", back_populates="conversations")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model = Column(String, nullable=True)
    tokens = Column(Integer, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    tool_input = Column(JSON, nullable=False)
    tool_output = Column(Text, nullable=True)
    status = Column(String, nullable=False)  # pending, success, error
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
