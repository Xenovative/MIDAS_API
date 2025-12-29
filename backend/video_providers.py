"""Video generation providers (Volcano Seedance)"""
import asyncio
from typing import List, Optional
import httpx
from backend.config import settings


class VideoProvider:
    """Base class for video generation providers"""
    async def generate(self, prompt: str, model: str, size: str) -> List[dict]:
        raise NotImplementedError

    def is_available(self) -> bool:
        return False

    def get_available_models(self) -> List[dict]:
        return []


class VolcanoVideoProvider(VideoProvider):
    """Volcano Engine Seedance video generation"""

    def __init__(self):
        self.api_key = settings.volcano_api_key
        self.base_url = settings.volcano_base_url

    def is_available(self) -> bool:
        return self.api_key is not None

    async def generate(self, prompt: str, model: str, size: str = "1280x720") -> List[dict]:
        if not self.api_key:
            raise ValueError("Volcano API key not configured")

        # Normalize resolution
        resolution = size if "x" in size else "1280x720"
        if resolution == "1024x1024":
            # allow 1:1 but keep as provided
            pass

        create_payload = {
            "model": model,
            "content": [
                {"type": "text", "text": prompt}
            ],
            "parameters": {
                "resolution": resolution,
                "duration": 5
            }
        }

        endpoints = [
            f"{self.base_url}/content-generation/tasks",      # hyphen
            f"{self.base_url}/content_generation/tasks",      # underscore (SDK)
            f"{self.base_url}/content-generation/video-tasks",  # possible alt path
            f"{self.base_url}/content_generation/video-tasks",  # possible alt path underscore
        ]

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = None
            last_error = ""
            for idx, endpoint in enumerate(endpoints):
                print("🎞️ VOLCANO VIDEO CREATE")
                print(f"   Attempt {idx+1}/{len(endpoints)} URL: {endpoint}")
                print(f"   Model: {model}")
                print(f"   Payload: {create_payload}")

                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=create_payload
                )

                if response.status_code == 200:
                    break

                last_error = response.text or response.reason_phrase
                print(f"⚠️ Video create failed ({response.status_code}): {last_error}")

            if response is None or response.status_code != 200:
                raise ValueError(f"Volcano Video Error: {last_error or 'Video create failed'}")

            task_data = response.json()
            task_id = task_data.get("id")
            if not task_id:
                raise ValueError(f"Failed to get task ID from Volcano: {task_data}")

            # Poll for results
            poll_endpoints = [
                f"{self.base_url}/content-generation/tasks/{task_id}",
                f"{self.base_url}/content_generation/tasks/{task_id}",
            ]
            print(f"⏳ Polling Volcano video task: {task_id}")
            for _ in range(120):  # 120 seconds timeout
                await asyncio.sleep(2)
                status_response = None
                for poll_ep in poll_endpoints:
                    status_response = await client.get(
                        poll_ep,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    if status_response.status_code == 200:
                        break
                if status_response is None or status_response.status_code != 200:
                    continue

                status_data = status_response.json()
                status = status_data.get("status")

                if status == "succeeded":
                    video_url = status_data.get("output", {}).get("video", {}).get("url") \
                        or status_data.get("output", {}).get("url")
                    if video_url:
                        return [{"url": video_url, "type": "video", "revised_prompt": None}]
                    raise ValueError(f"Video URL not found in successful task: {status_data}")
                if status == "failed":
                    error_msg = status_data.get("error", {}).get("message", "Unknown error")
                    raise ValueError(f"Volcano Video Generation failed: {error_msg}")
                if status == "cancelled":
                    raise ValueError("Volcano Video Generation was cancelled")

            raise TimeoutError("Volcano Video Generation timed out")

    def get_available_models(self) -> List[dict]:
        if not self.api_key:
            return []

        models = []
        if settings.volcano_video_endpoint:
            models.append({
                "id": settings.volcano_video_endpoint,
                "name": "Volcano Video (Dedicated)",
                "provider": "volcano",
                "sizes": ["1280x720", "720x1280", "1024x1024"],
                "qualities": ["standard"],
                "styles": [],
                "max_images": 1,
                "supports_style": False,
                "type": "video"
            })
        # Default Seedance model entry
        models.append({
            "id": "seedance-1.5-pro",
            "name": "Seedance 1.5 Pro (Video)",
            "provider": "volcano",
            "sizes": ["1280x720", "720x1280", "1024x1024", "960x544", "544x960"],
            "qualities": ["standard"],
            "styles": [],
            "max_images": 1,
            "supports_style": False,
            "type": "video"
        })
        return models


class VideoProviderManager:
    """Manage multiple video providers"""

    def __init__(self):
        self.providers = {
            "volcano": VolcanoVideoProvider()
        }

    def get_available_models(self) -> List[dict]:
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.get_available_models())
        return all_models

    async def generate(self, prompt: str, model: Optional[str], size: str) -> List[dict]:
        if not model:
            model = settings.volcano_video_endpoint or "seedance-1.5-pro"
        # If explicit ep is provided, send to volcano directly
        if model.startswith("ep-") or "seedance" in model.lower() or "video" in model.lower():
            provider = self.providers["volcano"]
            if not provider.is_available():
                raise ValueError("Volcano API key not configured")
            return await provider.generate(prompt=prompt, model=model, size=size)
        # Fallback to volcano if nothing else
        provider = self.providers["volcano"]
        if not provider.is_available():
            raise ValueError("Volcano API key not configured")
        return await provider.generate(prompt=prompt, model=model, size=size)


video_manager = VideoProviderManager()
