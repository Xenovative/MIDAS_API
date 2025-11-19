from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from backend.config import settings
from backend.image_providers import image_manager
from openai import AsyncOpenAI
import base64
import io

router = APIRouter(prefix="/generation", tags=["generation"])


class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "dall-e-3"
    size: str = "1024x1024"
    quality: str = "standard"
    style: Optional[str] = None
    n: int = 1


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
    model: str = "tts-1"
    speed: float = 1.0


@router.get("/image/models")
async def list_image_models():
    """List all available image generation models"""
    try:
        models = image_manager.get_available_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
async def generate_image(request: ImageGenerationRequest):
    """Generate images using various providers"""
    try:
        images = await image_manager.generate(
            prompt=request.prompt,
            model=request.model,
            size=request.size,
            quality=request.quality,
            style=request.style,
            n=request.n
        )
        
        return {"images": images}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        if not settings.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.audio.speech.create(
            model=request.model,
            voice=request.voice,
            input=request.text,
            speed=request.speed
        )
        
        # Stream the audio response
        audio_data = io.BytesIO()
        async for chunk in response.iter_bytes():
            audio_data.write(chunk)
        
        audio_data.seek(0)
        
        return StreamingResponse(
            audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    model: str = "whisper-1",
    language: Optional[str] = None
):
    """Convert speech to text using Whisper"""
    try:
        if not settings.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Read the uploaded file
        audio_data = await file.read()
        
        # Create a file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = file.filename or "audio.mp3"
        
        # Transcribe
        params = {
            "model": model,
            "file": audio_file
        }
        if language:
            params["language"] = language
        
        transcript = await client.audio.transcriptions.create(**params)
        
        return {
            "text": transcript.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
