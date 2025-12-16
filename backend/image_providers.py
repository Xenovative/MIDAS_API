"""Image generation providers"""
from abc import ABC, abstractmethod
from typing import Optional, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import httpx
import base64
import io
from PIL import Image
from backend.config import settings
from google import genai
from google.genai import types


class ImageProvider(ABC):
    """Base class for image generation providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1,
        image: Optional[str] = None  # Base64 encoded image for img2img
    ) -> List[dict]:
        """Generate images from prompt, optionally with image input"""
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
        model: str = "dall-e-3",
        image: Optional[str] = None,
        reference_images: Optional[List[str]] = None,
        image_fidelity: str = "high",
        moderation: str = "low"
    ) -> List[dict]:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        # Image editing support:
        # - DALL-E 2: Supports images.edit() and images.create_variation()
        # - GPT-Image-1: Supports images.edit() with different parameters
        # - DALL-E 3: Text-to-image only
        if image and model == "dall-e-2":
            # Decode base64 image
            image_bytes = base64.b64decode(image)
            
            # Open and process image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Make image square by center cropping (required by OpenAI)
            width, height = img.size
            target_size = min(width, height)
            
            # Calculate crop box for center crop
            left = (width - target_size) // 2
            top = (height - target_size) // 2
            right = left + target_size
            bottom = top + target_size
            
            square_img = img.crop((left, top, right, bottom))
            
            # Convert to RGBA if needed
            if square_img.mode != 'RGBA':
                square_img = square_img.convert('RGBA')
            
            # Resize to match requested size
            size_map = {"256x256": 256, "512x512": 512, "1024x1024": 1024}
            target_dim = size_map.get(size, 1024)
            if target_size != target_dim:
                square_img = square_img.resize((target_dim, target_dim), Image.Resampling.LANCZOS)
            
            # Save as PNG to BytesIO
            image_file = io.BytesIO()
            square_img.save(image_file, format='PNG')
            image_file.seek(0)
            image_file.name = "image.png"
            
            # Use edit endpoint with prompt, or variation without
            if prompt and prompt.strip():
                # Edit endpoint - transforms based on prompt
                response = await self.client.images.edit(
                    image=image_file,
                    prompt=prompt,
                    n=n,
                    size=size if size in ["256x256", "512x512", "1024x1024"] else "1024x1024"
                )
            else:
                # Variation endpoint - creates variations
                response = await self.client.images.create_variation(
                    image=image_file,
                    n=n,
                    size=size if size in ["256x256", "512x512", "1024x1024"] else "1024x1024"
                )
            
            return [
                {
                    "url": img_result.url,
                    "revised_prompt": None
                }
                for img_result in response.data
            ]
        
        # Check if this is image editing (gpt-image-1 with input image)
        if image and model == "gpt-image-1":
            print(f"📷 Using images.edit for gpt-image-1 image editing")
            # Convert base64 to bytes
            image_bytes = base64.b64decode(image)
            
            # Create a file-like object for the image
            image_file = io.BytesIO(image_bytes)
            image_file.name = "image.png"
            
            # GPT-Image-1 images.edit() parameters
            # NOTE: images.edit() does NOT support 'quality' parameter
            # Quality is only for images.generate()
            params = {
                "image": image_file,
                "prompt": prompt,
                "model": model,
                "n": n,
                "size": size
            }
            
            print(f"📤 Calling OpenAI images.edit with GPT-Image-1")
            print(f"   Parameters: model={model}, size={size}, n={n}")
            response = await self.client.images.edit(**params)
        elif reference_images and model == "gpt-image-1":
            # Image references for GPT-Image-1
            # Use direct HTTP API call for multiple image references
            print(f"🎨 Using image references for GPT-Image-1")
            print(f"   Number of reference images: {len(reference_images)}")
            
            # Get API key
            api_key = settings.openai_api_key
            
            # Prepare form data with array syntax
            # OpenAI requires 'image[]' for multiple images, not multiple 'image' fields
            files = []
            for idx, ref_img in enumerate(reference_images):
                ref_bytes = base64.b64decode(ref_img)
                files.append(
                    ('image[]', (f'reference_{idx}.png', ref_bytes, 'image/png'))
                )
            
            # Prepare other parameters
            data = {
                'model': model,
                'prompt': prompt,
                'size': size,
                'n': str(n),
                'input_fidelity': image_fidelity,
                'moderation': moderation
            }
            
            print(f"📤 Calling OpenAI images.edit API directly with {len(files)} images")
            print(f"   Parameters: model={model}, size={size}, n={n}")
            print(f"   Files: {[(name, fname) for name, (fname, _, _) in files]}")
            print(f"   Data: {data}")
            
            # Make direct HTTP call
            # Image generation can take a while, especially with multiple reference images
            async with httpx.AsyncClient(timeout=180.0) as http_client:
                api_response = await http_client.post(
                    'https://api.openai.com/v1/images/edits',
                    headers={
                        'Authorization': f'Bearer {api_key}'
                    },
                    files=files,
                    data=data
                )
                
                # Log response for debugging
                if api_response.status_code != 200:
                    print(f"❌ API Error {api_response.status_code}")
                    print(f"Response: {api_response.text}")
                
                api_response.raise_for_status()
                response_data = api_response.json()
            
            # Convert response to match OpenAI SDK format
            class ImageResponse:
                def __init__(self, data):
                    self.data = []
                    for img_data in data.get('data', []):
                        img_obj = type('ImageObject', (), {})()
                        img_obj.url = img_data.get('url')
                        img_obj.b64_json = img_data.get('b64_json')
                        img_obj.revised_prompt = img_data.get('revised_prompt')
                        self.data.append(img_obj)
            
            response = ImageResponse(response_data)
            print(f"✅ Received response with {len(response.data)} images")
        else:
            # Standard text-to-image generation
            params = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": n
            }
            
            # Map quality based on model
            if model == "gpt-image-1":
                # gpt-image-1 uses: low, medium, high, auto
                quality_map = {
                    "standard": "medium",
                    "hd": "high"
                }
                params["quality"] = quality_map.get(quality, "auto")
            else:
                # DALL-E uses: standard, hd
                params["quality"] = quality
            
            if style and model == "dall-e-3":
                params["style"] = style
            
            print(f"📤 Calling OpenAI images.generate with params: {params}")
            response = await self.client.images.generate(**params)
        print(f"📥 OpenAI response type: {type(response)}")
        print(f"📥 Response data length: {len(response.data)}")
        
        results = []
        for img in response.data:
            # Handle both url and b64_json formats
            if hasattr(img, 'url') and img.url:
                url = img.url
                print(f"✅ Got URL response")
            elif hasattr(img, 'b64_json') and img.b64_json:
                # Convert b64_json to data URL
                url = f"data:image/png;base64,{img.b64_json}"
                print(f"✅ Got b64_json response, converted to data URL")
            else:
                print(f"⚠️ Image object has neither url nor b64_json")
                url = None
            
            results.append({
                "url": url,
                "revised_prompt": getattr(img, "revised_prompt", None)
            })
        
        return results
    
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
        model: str = "stable-diffusion-xl-1024-v1-0",
        image: Optional[str] = None
    ) -> List[dict]:
        if not self.api_key:
            raise ValueError("Stability AI API key not configured")
        
        # Note: Stability AI img2img requires different endpoint
        # For now, we'll just do text-to-image
        if image:
            raise NotImplementedError("Stability AI img2img not yet implemented")
        
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


class GoogleImageProvider(ImageProvider):
    """Google AI (Gemini) image generation - using google-genai SDK for full Gemini 3 support"""
    
    # Gemini 3 image models
    GEMINI_3_IMAGE_MODELS = ['gemini-3-pro-image-preview']
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
    
    def _is_gemini_3(self, model: str) -> bool:
        """Check if model is Gemini 3 series"""
        return any(g3 in model for g3 in self.GEMINI_3_IMAGE_MODELS) or model.startswith('gemini-3')
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1,
        model: str = "gemini-2.5-flash-preview-05-20",
        image: Optional[str] = None,
        reference_images: Optional[List[str]] = None,
        use_google_search: bool = False,  # Gemini 3: grounded generation
        thought_signature: Optional[str] = None,  # Gemini 3: for multi-turn editing
        **kwargs
    ) -> List[dict]:
        if not self.client:
            raise ValueError("Google API key not configured")
        
        import asyncio
        
        is_gemini_3 = self._is_gemini_3(model)
        
        # Map size to aspect ratio
        size_to_aspect = {
            "1024x1024": "1:1",
            "1792x1024": "16:9",
            "1024x1792": "9:16",
            "1280x720": "16:9",
            "720x1280": "9:16",
            "1536x1024": "3:2",
            "1024x1536": "2:3",
        }
        aspect_ratio = size_to_aspect.get(size, "1:1")
        
        # Build contents list
        contents = []
        
        # Add reference images if provided (for editing)
        if image:
            # Single input image for editing - decode base64 to bytes
            image_bytes = base64.b64decode(image)
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
        elif reference_images:
            # Multiple reference images (Gemini 3 Pro supports up to 14)
            for ref_img in reference_images[:14]:
                ref_bytes = base64.b64decode(ref_img)
                contents.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/png"))
        
        # Add the text prompt
        contents.append(prompt)
        
        # Build generation config with image settings
        # Note: response_modalities tells the model to output both text and images
        config = types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        )
        
        # Generate using the new SDK
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=model,
            contents=contents,
            config=config
        )
        
        # Debug: Log response structure
        print(f"📦 Gemini image response received")
        
        # Extract images from response
        results = []
        response_thought_signature = None
        
        # Check if response has parts
        if not response.candidates or not response.candidates[0].content.parts:
            # Try to get text explaining why no image
            text_response = ""
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_response += part.text
            if text_response:
                raise ValueError(f"No image generated. Model response: {text_response[:500]}")
            raise ValueError("No image generated - response contained no parts")
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Convert to data URL
                mime_type = part.inline_data.mime_type
                b64_data = part.inline_data.data
                if isinstance(b64_data, bytes):
                    b64_data = base64.b64encode(b64_data).decode('utf-8')
                
                result = {
                    "url": f"data:{mime_type};base64,{b64_data}",
                    "revised_prompt": None
                }
                
                # Extract thought signature for Gemini 3 (needed for multi-turn editing)
                if is_gemini_3 and hasattr(part, 'thought_signature') and part.thought_signature:
                    result["thought_signature"] = part.thought_signature
                    response_thought_signature = part.thought_signature
                
                results.append(result)
            elif hasattr(part, 'text') and part.text:
                # Some responses include text description
                print(f"Gemini response text: {part.text}")
                # Gemini 3: text parts can also have thought signatures
                if is_gemini_3 and hasattr(part, 'thought_signature') and part.thought_signature:
                    response_thought_signature = part.thought_signature
        
        if not results:
            raise ValueError("No images generated in response")
        
        # Attach thought signature to first result for easy access
        if response_thought_signature and results:
            results[0]["thought_signature"] = response_thought_signature
        
        return results
    
    def get_available_models(self) -> List[dict]:
        if not self.api_key:
            return []
        
        return [
            {
                "id": "gemini-2.5-flash-image",
                "name": "Gemini 2.5 Flash Image (Nano Banana)",
                "provider": "google",
                "sizes": ["1024x1024", "1792x1024", "1024x1792"],
                "qualities": ["standard"],
                "styles": [],
                "max_images": 1,
                "supports_style": False
            },
            {
                "id": "gemini-3-pro-image-preview",
                "name": "Gemini 3 Pro Image (Nano Banana Pro)",
                "provider": "google",
                "sizes": ["1024x1024", "1792x1024", "1024x1792"],
                "qualities": ["standard", "hd", "ultra"],
                "styles": [],
                "max_images": 1,
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
        model: str = "stability-ai/sdxl",
        image: Optional[str] = None
    ) -> List[dict]:
        if not self.api_key:
            raise ValueError("Replicate API key not configured")
        
        # Note: Replicate img2img requires different model versions
        # For now, we'll just do text-to-image
        if image:
            raise NotImplementedError("Replicate img2img not yet implemented")
        
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
            "google": GoogleImageProvider(),
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
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1,
        image: Optional[str] = None,
        reference_images: Optional[List[str]] = None,
        image_fidelity: str = "high",
        moderation: str = "low"
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
                    model=model,
                    image=image,
                    reference_images=reference_images,
                    image_fidelity=image_fidelity,
                    moderation=moderation
                )
        
        raise ValueError(f"Model {model} not found in any provider")


# Global instance
image_manager = ImageProviderManager()


# Import asyncio for Replicate polling
import asyncio
