from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageCreate(BaseModel):
    role: str
    content: str
    model: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model: Optional[str] = None
    tokens: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    bot_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class DocumentData(BaseModel):
    """Document data for inline processing (Google AI)"""
    mime_type: str = "application/pdf"
    data: str  # Base64 encoded document


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    images: Optional[List[str]] = None  # Base64 encoded images
    documents: Optional[List[DocumentData]] = None  # Inline documents for Google AI
    model: str = "gpt-3.5-turbo"
    provider: str = "openai"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    use_agent: bool = False
    use_realtime_data: bool = False
    use_deep_research: bool = False
    system_prompt: Optional[str] = None
    bot_id: Optional[str] = None
    bot_name: Optional[str] = None
    image_model: Optional[str] = "gpt-image-1"
    image_size: Optional[str] = "1024x1024"  # Image generation size
    image_fidelity: Optional[str] = "high"  # Image fidelity: low, medium, high
    moderation: Optional[str] = "low"  # Content moderation: low, medium, high


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    agent_executions: List[Dict[str, Any]] = []


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    context_window: int
    supports_functions: bool = True
    supports_vision: bool = False
    supports_image_generation: bool = False
    supports_tts: bool = False
    supports_stt: bool = False


class ProviderStatus(BaseModel):
    provider: str
    available: bool
    models: List[ModelInfo] = []
