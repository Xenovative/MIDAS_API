from fastapi import APIRouter
from typing import List
from backend.schemas import ProviderStatus
from backend.llm_providers import llm_manager

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/")
async def get_available_models():
    """Get all available LLM providers and their models"""
    try:
        providers = await llm_manager.get_available_providers()
        return providers
    except Exception as e:
        print(f"Error in get_available_models: {e}")
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
