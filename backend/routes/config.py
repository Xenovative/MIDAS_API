from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path

router = APIRouter(prefix="/config", tags=["config"])


class APIKeyUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    volcano_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None


@router.get("/api-keys")
async def get_api_keys_status():
    """Get the status of API keys (masked for security)"""
    from backend.config import settings
    
    return {
        "openai": {
            "configured": bool(settings.openai_api_key),
            "masked_key": f"{settings.openai_api_key[:7]}...{settings.openai_api_key[-4:]}" if settings.openai_api_key else None
        },
        "anthropic": {
            "configured": bool(settings.anthropic_api_key),
            "masked_key": f"{settings.anthropic_api_key[:7]}...{settings.anthropic_api_key[-4:]}" if settings.anthropic_api_key else None
        },
        "google": {
            "configured": bool(settings.google_api_key),
            "masked_key": f"{settings.google_api_key[:7]}...{settings.google_api_key[-4:]}" if settings.google_api_key else None
        },
        "openrouter": {
            "configured": bool(settings.openrouter_api_key),
            "masked_key": f"{settings.openrouter_api_key[:7]}...{settings.openrouter_api_key[-4:]}" if settings.openrouter_api_key else None
        },
        "volcano": {
            "configured": bool(settings.volcano_api_key),
            "masked_key": f"{settings.volcano_api_key[:7]}...{settings.volcano_api_key[-4:]}" if settings.volcano_api_key else None
        },
        "deepseek": {
            "configured": bool(settings.deepseek_api_key),
            "masked_key": f"{settings.deepseek_api_key[:7]}...{settings.deepseek_api_key[-4:]}" if settings.deepseek_api_key else None
        },
        "ollama": {
            "configured": True,
            "base_url": settings.ollama_base_url
        }
    }


@router.post("/api-keys")
async def update_api_keys(keys: APIKeyUpdate):
    """Update API keys in the .env file"""
    try:
        env_path = Path(".env")
        
        # Read existing .env file
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Create a dictionary of existing env vars
        env_vars = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        # Update with new values (only if provided)
        if keys.openai_api_key is not None:
            if keys.openai_api_key:
                env_vars['OPENAI_API_KEY'] = keys.openai_api_key
            elif 'OPENAI_API_KEY' in env_vars:
                del env_vars['OPENAI_API_KEY']
        
        if keys.anthropic_api_key is not None:
            if keys.anthropic_api_key:
                env_vars['ANTHROPIC_API_KEY'] = keys.anthropic_api_key
            elif 'ANTHROPIC_API_KEY' in env_vars:
                del env_vars['ANTHROPIC_API_KEY']
        
        if keys.google_api_key is not None:
            if keys.google_api_key:
                env_vars['GOOGLE_API_KEY'] = keys.google_api_key
            elif 'GOOGLE_API_KEY' in env_vars:
                del env_vars['GOOGLE_API_KEY']
        
        if keys.openrouter_api_key is not None:
            if keys.openrouter_api_key:
                env_vars['OPENROUTER_API_KEY'] = keys.openrouter_api_key
            elif 'OPENROUTER_API_KEY' in env_vars:
                del env_vars['OPENROUTER_API_KEY']
        
        if keys.volcano_api_key is not None:
            if keys.volcano_api_key:
                env_vars['VOLCANO_API_KEY'] = keys.volcano_api_key
            elif 'VOLCANO_API_KEY' in env_vars:
                del env_vars['VOLCANO_API_KEY']
        
        if keys.deepseek_api_key is not None:
            if keys.deepseek_api_key:
                env_vars['DEEPSEEK_API_KEY'] = keys.deepseek_api_key
            elif 'DEEPSEEK_API_KEY' in env_vars:
                del env_vars['DEEPSEEK_API_KEY']
        
        if keys.ollama_base_url is not None:
            if keys.ollama_base_url:
                env_vars['OLLAMA_BASE_URL'] = keys.ollama_base_url
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        return {
            "success": True,
            "message": "API keys updated successfully. Please restart the backend server for changes to take effect."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-keys/{provider}")
async def delete_api_key(provider: str):
    """Remove an API key from the .env file"""
    try:
        env_path = Path(".env")
        
        if not env_path.exists():
            raise HTTPException(status_code=404, detail=".env file not found")
        
        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Map provider names to env var names
        provider_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "volcano": "VOLCANO_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }
        
        if provider not in provider_map:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        env_var_name = provider_map[provider]
        
        # Filter out the line with this key
        new_lines = [line for line in lines if not line.strip().startswith(f"{env_var_name}=")]
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        return {
            "success": True,
            "message": f"{provider} API key removed. Please restart the backend server."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
