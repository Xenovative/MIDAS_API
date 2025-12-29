from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai
from google.genai import types
from backend.config import settings
import json


class LLMProvider:
    """Base class for LLM providers"""
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    NO_TEMP_KEYWORDS = ['chatgpt-4o-latest', 'gpt-5', 'o1', 'o3', 'realtime']

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    
    def is_available(self) -> bool:
        return self.client is not None

    def _supports_temperature(self, model_id: str) -> bool:
        lower_id = model_id.lower()
        return not any(keyword in lower_id for keyword in self.NO_TEMP_KEYWORDS)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        params = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # Only add temperature if model supports it
        if self._supports_temperature(model):
            params["temperature"] = temperature
        
        # Handle max_tokens (skip for models that don't support the parameter)
        # O1/O3 models use max_completion_tokens instead of max_tokens
        if max_tokens:
            lower_model = model.lower()
            if any(lower_model.startswith(prefix) for prefix in ['o1', 'o3']):
                params["max_completion_tokens"] = max_tokens
            elif lower_model.startswith('gpt-5'):
                pass  # GPT-5 models might not support this yet
            else:
                params["max_tokens"] = max_tokens
        
        # Add tools if provided
        if tools:
            params["tools"] = tools
        
        response = await self.client.chat.completions.create(**params)
        
        result = {
            "content": response.choices[0].message.content,
            "model": response.model,
            "tokens": response.usage.total_tokens if response.usage else None
        }
        
        # Include tool calls if present
        if response.choices[0].message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in response.choices[0].message.tool_calls
            ]
        
        return result
    
    async def chat_with_reasoning(
        self,
        messages: List[Dict[str, str]],
        model: str,
        reasoning_effort: str = "medium",
        max_completion_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Chat with O1/O3 reasoning models
        
        O1 models only support minimal parameters:
        - model
        - messages
        
        They do NOT support:
        - temperature
        - max_tokens / max_completion_tokens
        - top_p
        - frequency_penalty
        - presence_penalty
        
        Args:
            messages: List of messages
            model: Model name (o1-preview, o1-mini, o3-mini, etc.)
            reasoning_effort: Ignored (for future compatibility)
            max_completion_tokens: Ignored (not supported by O1)
        
        Returns:
            Response dict with content and usage
        """
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        # O1 models only accept model and messages
        params = {
            "model": model,
            "messages": messages,
        }
        
        print(f"🔬 Calling O1/O3 model: {model}")
        print(f"   → Using minimal parameters (O1 models have fixed settings)")
        
        try:
            response = await self.client.chat.completions.create(**params)
            
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
            return result
        except Exception as e:
            print(f"❌ Error calling O1/O3: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        print(f"🔍 OpenAI chat_stream - Model: {model}")
        print(f"Temperature requested: {temperature}")
        print(f"Messages received: {len(messages)} messages")
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            if isinstance(content, list):
                print(f"  Message {i}: role={msg.get('role')}, content=<multimodal list with {len(content)} items>")
            else:
                preview = content[:100] if len(content) <= 100000 else f"<large content {len(content)} chars>"
                print(f"  Message {i}: role={msg.get('role')}, content={preview}...")
        
        params = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        # Only add temperature if model supports it
        if self._supports_temperature(model):
            params["temperature"] = temperature
            print(f"✅ Temperature added: {temperature}")
        else:
            print(f"⚠️ Temperature skipped for {model}")
        
        # Handle max_tokens (skip for models that don't support the parameter)
        if max_tokens:
            lower_model = model.lower()
            if any(lower_model.startswith(prefix) for prefix in ['gpt-5', 'o1', 'o3']):
                print(f"⚠️ Max tokens skipped for {model}")
            else:
                params["max_tokens"] = max_tokens
                print(f"✅ Max tokens added: {max_tokens}")
        
        print(f"Final params: {params}")
        stream = await self.client.chat.completions.create(**params)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        # Convert messages format
        system_message = None
        converted_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                converted_messages.append(msg)
        
        response = await self.client.messages.create(
            model=model,
            messages=converted_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 4096
        )
        
        return {
            "content": response.content[0].text,
            "model": response.model,
            "tokens": response.usage.input_tokens + response.usage.output_tokens
        }
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        system_message = None
        converted_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                converted_messages.append(msg)
        
        async with self.client.messages.stream(
            model=model,
            messages=converted_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 4096
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url
    
    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=2.0)
                return response.status_code == 200
        except:
            return False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["message"]["content"],
                "model": model,
                "tokens": data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
            }
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        ) if settings.openrouter_api_key else None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("OpenRouter API key not configured")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "tokens": response.usage.total_tokens if response.usage else None
        }
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("OpenRouter API key not configured")
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class VolcanoProvider(LLMProvider):
    """火山引擎 (Volcano Engine) Provider"""
    def __init__(self):
        self.api_key = settings.volcano_api_key
        self.endpoint_id = settings.volcano_endpoint_id
        self.base_url = settings.volcano_base_url
    
    def is_available(self) -> bool:
        return self.api_key is not None and self.endpoint_id is not None
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Return a single Smart Router entry for Volcano Engine"""
        if not self.is_available():
            return []
            
        # Volcano Engine is multi-modal and routes automatically.
        # We only need one entry to represent the configured endpoint.
        model_id = self.endpoint_id if (self.endpoint_id and self.endpoint_id.startswith("ep-")) else "doubao-pro"
        
        return [{
            "id": model_id,
            "name": "豆包 (Smart Router)",
            "provider": "volcano",
            "context_window": 128000,
            "supports_functions": True,
            "supports_vision": True
        }]

    def _get_endpoint_id(self, model: str) -> str:
        """Get the actual endpoint ID for a model name"""
        # If model is already an endpoint ID (starts with ep-), use it
        if model.startswith("ep-"):
            return model
        
        # Check environment variables for mapping: VOLCANO_MODEL_MAP="doubao-pro:ep-xxx,doubao-lite:ep-yyy"
        import os
        model_map_str = os.getenv("VOLCANO_MODEL_MAP", "")
        if model_map_str:
            try:
                model_map = dict(item.split(":") for item in model_map_str.split(",") if ":" in item)
                if model in model_map:
                    return model_map[model]
            except Exception as e:
                print(f"⚠️ Error parsing VOLCANO_MODEL_MAP: {e}")
        
        # Fallback to default endpoint ID from settings
        # Validate that the endpoint_id looks like a real endpoint ID (ep-...)
        if self.endpoint_id and self.endpoint_id.startswith("ep-"):
            return self.endpoint_id
            
        print(f"⚠️ No valid mapping found for Volcano model '{model}' and default endpoint_id is invalid: '{self.endpoint_id}'")
        return model # Fallback to model name itself, which will likely fail but at least it's clear

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Volcano Engine API key or endpoint ID not configured")
        
        # Check if user is trying to use a non-chat model
        non_chat_keywords = ["seedance", "seedream", "video-generation", "t2v", "i2v", "speech", "voice", "audio"]
        if any(kw in model.lower() for kw in non_chat_keywords):
            raise ValueError(f"Model '{model}' is a non-chat model and cannot be used with the chat completion endpoint. Please use a Doubao chat model.")

        endpoint_id = self._get_endpoint_id(model)
        print(f"🌋 Volcano Chat: model={model}, endpoint={endpoint_id}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": endpoint_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 4096
                }
            )
            
            if response.status_code != 200:
                error_text = response.text
                print(f"❌ Volcano API Error ({response.status_code}): {error_text}")
                raise ValueError(f"Volcano API Error: {error_text}")
                
            data = response.json()
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")
            
            # Support for reasoning_content (DeepSeek R1 on Ark)
            reasoning_content = message.get("reasoning_content")
            
            result = {
                "content": content,
                "model": model,
                "tokens": data.get("usage", {}).get("total_tokens", 0)
            }
            
            if reasoning_content:
                result["reasoning_content"] = reasoning_content
                
            return result
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("Volcano Engine API key or endpoint ID not configured")
        
        # Check if user is trying to use a non-chat model
        non_chat_keywords = ["seedance", "seedream", "video-generation", "t2v", "i2v", "speech", "voice", "audio"]
        if any(kw in model.lower() for kw in non_chat_keywords):
            yield f"Error: Model '{model}' is a non-chat model (video/audio/image) and is not supported for chat."
            return

        endpoint_id = self._get_endpoint_id(model)
        print(f"🌋 Volcano Stream: model={model}, endpoint={endpoint_id}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": endpoint_id,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens or 4096,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"❌ Volcano Stream Error ({response.status_code}): {error_text.decode()}")
                        yield f"Error from Volcano Engine ({response.status_code}): {error_text.decode()}"
                        return

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                            
                        if line.startswith("data: "):
                            content = line[6:].strip()
                            if content == "[DONE]":
                                break
                            try:
                                data = json.loads(content)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    
                                    # Support for reasoning_content (DeepSeek R1 on Ark)
                                    if "reasoning_content" in delta:
                                        yield f"<think>\n{delta['reasoning_content']}\n</think>"
                                        
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError as e:
                                print(f"⚠️ Volcano JSON parse error: {e}, line: {line}")
                                continue
            except Exception as e:
                print(f"💥 Volcano stream exception: {e}")
                yield f"Stream connection error: {str(e)}"


class GoogleProvider(LLMProvider):
    """Google AI (Gemini) Provider - using google-genai SDK for full Gemini 3 support"""
    
    # Gemini 3 models that need special handling
    GEMINI_3_MODELS = ['gemini-3-pro-preview', 'gemini-3-pro-image-preview']
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def _is_gemini_3(self, model: str) -> bool:
        """Check if model is Gemini 3 series"""
        return any(g3 in model for g3 in self.GEMINI_3_MODELS) or model.startswith('gemini-3')
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        thinking_level: Optional[str] = None  # Gemini 3: 'low', 'high'
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Google API key not configured")
        
        import base64
        import asyncio
        
        is_gemini_3 = self._is_gemini_3(model)
        
        # Convert messages to Gemini format using types
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
                continue
            
            # Map roles: user -> user, assistant -> model
            gemini_role = "model" if role == "assistant" else "user"
            
            # Handle multimodal content
            parts = []
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        parts.append(types.Part.from_text(text=item["text"]))
                    elif item.get("type") == "image_url":
                        image_url = item["image_url"]["url"]
                        if image_url.startswith("data:"):
                            header, b64_data = image_url.split(",", 1)
                            mime_type = header.split(":")[1].split(";")[0]
                            image_bytes = base64.b64decode(b64_data)
                            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
                    elif item.get("type") == "document":
                        doc_data = item.get("document", {})
                        mime_type = doc_data.get("mime_type", "application/pdf")
                        b64_data = doc_data.get("data", "")
                        doc_bytes = base64.b64decode(b64_data)
                        parts.append(types.Part.from_bytes(data=doc_bytes, mime_type=mime_type))
            else:
                parts.append(types.Part.from_text(text=content))
            
            contents.append(types.Content(role=gemini_role, parts=parts))
        
        # Build generation config
        config_kwargs = {}
        
        # Gemini 3 recommends temperature=1.0
        if is_gemini_3:
            config_kwargs["temperature"] = 1.0
        else:
            config_kwargs["temperature"] = temperature
        
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
        
        # Skip thinking config for now - may not be supported in all models
        # if is_gemini_3 and thinking_level:
        #     config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_level)
        
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        
        config = types.GenerateContentConfig(**config_kwargs)
        
        # Generate using the new SDK
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=model,
            contents=contents,
            config=config
        )
        
        # Extract text from response parts
        text_content = ""
        thought_signature = None
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text
                    if hasattr(part, 'thought_signature') and part.thought_signature:
                        thought_signature = part.thought_signature
        
        # Fallback to response.text
        if not text_content:
            try:
                text_content = response.text
            except Exception:
                text_content = ""
        
        result = {
            "content": text_content,
            "model": model,
            "tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else None
        }
        
        if thought_signature:
            result["thought_signature"] = thought_signature
        
        return result
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        thinking_level: Optional[str] = None  # Gemini 3: 'low', 'high'
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("Google API key not configured")
        
        import base64
        import asyncio
        
        is_gemini_3 = self._is_gemini_3(model)
        
        # Convert messages to Gemini format using types
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
                continue
            
            gemini_role = "model" if role == "assistant" else "user"
            
            parts = []
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        parts.append(types.Part.from_text(text=item["text"]))
                    elif item.get("type") == "image_url":
                        image_url = item["image_url"]["url"]
                        if image_url.startswith("data:"):
                            header, b64_data = image_url.split(",", 1)
                            mime_type = header.split(":")[1].split(";")[0]
                            image_bytes = base64.b64decode(b64_data)
                            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
                    elif item.get("type") == "document":
                        doc_data = item.get("document", {})
                        mime_type = doc_data.get("mime_type", "application/pdf")
                        b64_data = doc_data.get("data", "")
                        doc_bytes = base64.b64decode(b64_data)
                        parts.append(types.Part.from_bytes(data=doc_bytes, mime_type=mime_type))
            else:
                parts.append(types.Part.from_text(text=content))
            
            contents.append(types.Content(role=gemini_role, parts=parts))
        
        # Build generation config
        config_kwargs = {}
        
        if is_gemini_3:
            config_kwargs["temperature"] = 1.0
        else:
            config_kwargs["temperature"] = temperature
        
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
        
        # Skip thinking config for now - may not be supported in all models
        # if is_gemini_3 and thinking_level:
        #     config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_level)
        
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        
        config = types.GenerateContentConfig(**config_kwargs)
        
        # Use non-streaming and yield the full response
        # The google-genai SDK streaming doesn't work well with async
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=contents,
                config=config
            )
            
            # Extract text from response
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        # Yield in chunks to simulate streaming
                        text = part.text
                        chunk_size = 50
                        for i in range(0, len(text), chunk_size):
                            yield text[i:i+chunk_size]
        except Exception as e:
            print(f"❌ Google streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"\n\nError: {str(e)}"


class DeepSeekProvider(LLMProvider):
    """DeepSeek API Provider"""
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com"
        ) if settings.deepseek_api_key else None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("DeepSeek API key not configured")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        message = response.choices[0].message
        content = message.content
        reasoning_content = getattr(message, 'reasoning_content', None)
        
        result = {
            "content": content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        if reasoning_content:
            result["reasoning_content"] = reasoning_content
            
        return result
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("DeepSeek API key not configured")
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Support for reasoning_content (DeepSeek R1)
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                yield f"<think>\n{delta.reasoning_content}\n</think>"
                
            if delta.content:
                yield delta.content


class LLMManager:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider(),
            "openrouter": OpenRouterProvider(),
            "volcano": VolcanoProvider(),
            "deepseek": DeepSeekProvider(),
            "ollama": OllamaProvider()
        }
    
    def get_provider(self, provider_name: str) -> LLMProvider:
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]
    
    async def get_available_providers(self) -> List[Dict[str, Any]]:
        providers_status = []
        
        # OpenAI
        openai_provider = self.providers["openai"]
        if openai_provider.is_available():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        all_models = data.get("data", [])
                        print(f"🔍 Total models from OpenAI API: {len(all_models)}")
                        
                        # Don't filter - show all models
                        chat_models = all_models
                        
                        print(f"📋 Showing all {len(chat_models)} models")
                        print("First 10 models:")
                        for model in chat_models[:10]:
                            print(f"  - {model['id']}")
                        
                        # Sort by most recent/relevant models first
                        priority_models = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
                        sorted_models = []
                        
                        for priority in priority_models:
                            matching = [m for m in chat_models if priority in m["id"]]
                            sorted_models.extend(matching)
                        
                        # Add remaining models
                        remaining = [m for m in chat_models if m not in sorted_models]
                        sorted_models.extend(remaining)
                        
                        models = [
                            {
                                "id": model["id"],
                                "name": model["id"].replace("-", " ").title(),
                                "provider": "openai",
                                "context_window": 128000 if "gpt-4" in model["id"] else 16385,
                                "supports_functions": True
                            }
                            for model in sorted_models  # Show all available models
                        ]
                        
                        if models:  # Only add if we got models
                            providers_status.append({
                                "provider": "openai",
                                "available": True,
                                "models": models
                            })
                        else:
                            # If no models found, use fallback
                            raise ValueError("No chat models found")
            except Exception as e:
                print(f"OpenAI models fetch error: {e}")
                # Fallback to default models if API call fails
                providers_status.append({
                    "provider": "openai",
                    "available": True,
                    "models": [
                        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "context_window": 128000, "supports_functions": True, "supports_vision": True},
                        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "context_window": 128000, "supports_functions": True, "supports_vision": True},
                        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai", "context_window": 128000, "supports_functions": True, "supports_vision": True},
                        {"id": "gpt-4", "name": "GPT-4", "provider": "openai", "context_window": 8192, "supports_functions": True, "supports_vision": False},
                        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai", "context_window": 16385, "supports_functions": True, "supports_vision": False}
                    ]
                })
        
        # Anthropic - Use static list (Anthropic doesn't have a models list endpoint)
        anthropic_provider = self.providers["anthropic"]
        if anthropic_provider.is_available():
            providers_status.append({
                "provider": "anthropic",
                "available": True,
                "models": [
                    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "context_window": 200000, "supports_functions": True, "supports_vision": True},
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic", "context_window": 200000, "supports_functions": True, "supports_vision": True},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "provider": "anthropic", "context_window": 200000, "supports_functions": True, "supports_vision": True},
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "provider": "anthropic", "context_window": 200000, "supports_functions": True, "supports_vision": True}
                ]
            })
        
        # Google AI (Gemini) - Use static list (google-genai SDK model listing is different)
        google_provider = self.providers["google"]
        if google_provider.is_available():
            providers_status.append({
                "provider": "google",
                "available": True,
                "models": [
                    {"id": "gemini-2.5-pro-preview-06-05", "name": "Gemini 2.5 Pro Preview", "provider": "google", "context_window": 1048576, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-2.5-flash-preview-05-20", "name": "Gemini 2.5 Flash Preview", "provider": "google", "context_window": 1048576, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "google", "context_window": 1048576, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "provider": "google", "context_window": 1048576, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "context_window": 2097152, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google", "context_window": 1048576, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-3-pro-preview", "name": "Gemini 3 Pro Preview", "provider": "google", "context_window": 1048576, "supports_functions": True, "supports_vision": True},
                    {"id": "gemini-3-pro-image-preview", "name": "Gemini 3 Pro Image", "provider": "google", "context_window": 1048576, "supports_functions": False, "supports_vision": True},
                ]
            })
        
        # OpenRouter
        openrouter_provider = self.providers["openrouter"]
        if openrouter_provider.is_available():
            providers_status.append({
                "provider": "openrouter",
                "available": True,
                "models": [
                    {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "openrouter", "context_window": 128000, "supports_functions": True, "supports_vision": True},
                    {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openrouter", "context_window": 128000, "supports_functions": True, "supports_vision": True},
                    {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "openrouter", "context_window": 200000, "supports_functions": True, "supports_vision": True},
                    {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus", "provider": "openrouter", "context_window": 200000, "supports_functions": True, "supports_vision": True},
                    {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5", "provider": "openrouter", "context_window": 1000000, "supports_functions": True, "supports_vision": True},
                    {"id": "meta-llama/llama-3.1-405b-instruct", "name": "Llama 3.1 405B", "provider": "openrouter", "context_window": 128000, "supports_functions": True, "supports_vision": False},
                    {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "openrouter", "context_window": 128000, "supports_functions": True, "supports_vision": False},
                    {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "provider": "openrouter", "context_window": 64000, "supports_functions": True, "supports_vision": False},
                    {"id": "qwen/qwen-2.5-72b-instruct", "name": "Qwen 2.5 72B", "provider": "openrouter", "context_window": 128000, "supports_functions": True, "supports_vision": False}
                ]
            })
        
        # DeepSeek
        deepseek_provider = self.providers["deepseek"]
        if deepseek_provider.is_available():
            providers_status.append({
                "provider": "deepseek",
                "available": True,
                "models": [
                    {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek", "context_window": 64000, "supports_functions": True, "supports_vision": False},
                    {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "deepseek", "context_window": 64000, "supports_functions": True, "supports_vision": False},
                    {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)", "provider": "deepseek", "context_window": 64000, "supports_functions": False, "supports_vision": False}
                ]
            })
        
        # Volcano Engine (火山引擎)
        volcano_provider = self.providers["volcano"]
        if volcano_provider.is_available():
            try:
                # Volcano Engine uses smart routing, so we only need one entry
                volcano_models = await volcano_provider.get_available_models()
                
                providers_status.append({
                    "provider": "volcano",
                    "available": True,
                    "models": volcano_models
                })
            except Exception as e:
                print(f"⚠️ Error in Volcano discovery: {e}")
                providers_status.append({
                    "provider": "volcano",
                    "available": True,
                    "models": [
                        {"id": "doubao-pro", "name": "豆包 (Smart Router)", "provider": "volcano", "context_window": 128000, "supports_functions": True, "supports_vision": True}
                    ]
                })
        
        # Ollama - Fetch from local API
        ollama_provider = self.providers["ollama"]
        if await ollama_provider.is_available():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
                    data = response.json()
                    models = [
                        {
                            "id": model["name"],
                            "name": model["name"].replace(":", " ").title(),
                            "provider": "ollama",
                            "context_window": model.get("details", {}).get("parameter_size", "Unknown"),
                            "supports_functions": False
                        }
                        for model in data.get("models", [])
                    ]
                    providers_status.append({
                        "provider": "ollama",
                        "available": True,
                        "models": models
                    })
            except:
                pass
        
        return providers_status


llm_manager = LLMManager()
