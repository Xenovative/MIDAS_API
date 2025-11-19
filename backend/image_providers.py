"""Image generation providers"""
from abc import ABC, abstractmethod
from typing import Optional, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import httpx
from backend.config import settings


class ImageProvider(ABC):
    """Base class for image generation providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1
    ) -> List[dict]:
        """Generate images from prompt"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[dict]:
        """Get list of available models"""
        pass


class OpenAIImageProvider(ImageProvider):
    """OpenAI DALL-E image generation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1,
        model: str = "dall-e-3"
    ) -> List[dict]:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        params = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }
        
        if style and model == "dall-e-3":
            params["style"] = style
        
        response = await self.client.images.generate(**params)
        
        return [
            {
                "url": img.url,
                "revised_prompt": getattr(img, "revised_prompt", None)
            }
            for img in response.data
        ]
    
    def get_available_models(self) -> List[dict]:
        if not settings.openai_api_key:
            return []
        
        return [
            {
                "id": "gpt-image-1",
                "name": "GPT-Image-1",
                "provider": "openai",
                "sizes": ["1024x1024", "1024x1792", "1792x1024"],
                "qualities": ["auto", "low", "medium", "high"],
                "styles": ["vivid", "natural"],
                "max_images": 1,
                "supports_style": True
            },
            {
                "id": "dall-e-3",
                "name": "DALL-E 3",
                "provider": "openai",
                "sizes": ["1024x1024", "1024x1792", "1792x1024"],
                "qualities": ["standard", "hd"],
                "styles": ["vivid", "natural"],
                "max_images": 1,
                "supports_style": True
            },
            {
                "id": "dall-e-2",
                "name": "DALL-E 2",
                "provider": "openai",
                "sizes": ["256x256", "512x512", "1024x1024"],
                "qualities": ["standard"],
                "styles": [],
                "max_images": 10,
                "supports_style": False
            }
        ]


class StabilityAIProvider(ImageProvider):
    """Stability AI (Stable Diffusion) image generation"""
    
    def __init__(self):
        self.api_key = settings.stability_api_key if hasattr(settings, 'stability_api_key') else None
        self.base_url = "https://api.stability.ai/v1/generation"
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1,
        model: str = "stable-diffusion-xl-1024-v1-0"
    ) -> List[dict]:
        if not self.api_key:
            raise ValueError("Stability AI API key not configured")
        
        # Parse size
        width, height = map(int, size.split('x'))
        
        # Map quality to steps
        steps_map = {
            "standard": 30,
            "hd": 50,
            "ultra": 75
        }
        steps = steps_map.get(quality, 30)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{model}/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [{"text": prompt, "weight": 1}],
                    "cfg_scale": 7,
                    "height": height,
                    "width": width,
                    "steps": steps,
                    "samples": n,
                    "style_preset": style if style else None
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
        
        # Convert base64 to data URL
        results = []
        for artifact in data.get("artifacts", []):
            if artifact.get("base64"):
                results.append({
                    "url": f"data:image/png;base64,{artifact['base64']}",
                    "revised_prompt": None
                })
        
        return results
    
    def get_available_models(self) -> List[dict]:
        if not self.api_key:
            return []
        
        return [
            {
                "id": "stable-diffusion-xl-1024-v1-0",
                "name": "Stable Diffusion XL 1.0",
                "provider": "stability",
                "sizes": ["1024x1024", "1152x896", "896x1152", "1216x832", "832x1216"],
                "qualities": ["standard", "hd", "ultra"],
                "styles": ["3d-model", "analog-film", "anime", "cinematic", "comic-book", 
                          "digital-art", "enhance", "fantasy-art", "isometric", "line-art",
                          "low-poly", "modeling-compound", "neon-punk", "origami", "photographic",
                          "pixel-art", "tile-texture"],
                "max_images": 10,
                "supports_style": True
            },
            {
                "id": "stable-diffusion-v1-6",
                "name": "Stable Diffusion 1.6",
                "provider": "stability",
                "sizes": ["512x512", "768x768", "1024x1024"],
                "qualities": ["standard", "hd"],
                "styles": [],
                "max_images": 10,
                "supports_style": False
            }
        ]


class ReplicateProvider(ImageProvider):
    """Replicate image generation (various models)"""
    
    def __init__(self):
        self.api_key = settings.replicate_api_key if hasattr(settings, 'replicate_api_key') else None
        self.base_url = "https://api.replicate.com/v1"
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1,
        model: str = "stability-ai/sdxl"
    ) -> List[dict]:
        if not self.api_key:
            raise ValueError("Replicate API key not configured")
        
        width, height = map(int, size.split('x'))
        
        async with httpx.AsyncClient() as client:
            # Start prediction
            response = await client.post(
                f"{self.base_url}/predictions",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": self._get_model_version(model),
                    "input": {
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "num_outputs": n
                    }
                },
                timeout=10.0
            )
            response.raise_for_status()
            prediction = response.json()
            
            # Poll for completion
            prediction_id = prediction["id"]
            for _ in range(60):  # 60 seconds timeout
                await asyncio.sleep(1)
                status_response = await client.get(
                    f"{self.base_url}/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {self.api_key}"}
                )
                status_data = status_response.json()
                
                if status_data["status"] == "succeeded":
                    output = status_data.get("output", [])
                    if isinstance(output, str):
                        output = [output]
                    return [{"url": url, "revised_prompt": None} for url in output]
                elif status_data["status"] == "failed":
                    raise ValueError(f"Generation failed: {status_data.get('error')}")
        
        raise TimeoutError("Image generation timed out")
    
    def _get_model_version(self, model: str) -> str:
        """Get the specific version hash for a model"""
        versions = {
            "stability-ai/sdxl": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "playgroundai/playground-v2.5": "a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24"
        }
        return versions.get(model, versions["stability-ai/sdxl"])
    
    def get_available_models(self) -> List[dict]:
        if not self.api_key:
            return []
        
        return [
            {
                "id": "stability-ai/sdxl",
                "name": "SDXL (Replicate)",
                "provider": "replicate",
                "sizes": ["1024x1024", "1152x896", "896x1152"],
                "qualities": ["standard"],
                "styles": [],
                "max_images": 4,
                "supports_style": False
            },
            {
                "id": "playgroundai/playground-v2.5",
                "name": "Playground v2.5",
                "provider": "replicate",
                "sizes": ["1024x1024", "1280x768", "768x1280"],
                "qualities": ["standard"],
                "styles": [],
                "max_images": 4,
                "supports_style": False
            }
        ]


class ImageProviderManager:
    """Manage multiple image generation providers"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIImageProvider(),
            "stability": StabilityAIProvider(),
            "replicate": ReplicateProvider()
        }
    
    def get_provider(self, provider_name: str) -> ImageProvider:
        """Get a specific provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]
    
    def get_available_models(self) -> List[dict]:
        """Get all available models from all providers"""
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.get_available_models())
        return all_models
    
    async def generate(
        self,
        prompt: str,
        model: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1
    ) -> List[dict]:
        """Generate images using the specified model"""
        # Find which provider has this model
        for provider_name, provider in self.providers.items():
            models = provider.get_available_models()
            if any(m["id"] == model for m in models):
                return await provider.generate(
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    n=n,
                    model=model
                )
        
        raise ValueError(f"Model not found: {model}")


# Global instance
image_manager = ImageProviderManager()


# Import asyncio for Replicate polling
import asyncio
