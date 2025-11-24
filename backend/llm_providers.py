from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai
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
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
    
    def is_available(self) -> bool:
        return self.api_key is not None and self.endpoint_id is not None
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Volcano Engine API key or endpoint ID not configured")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.endpoint_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 4096
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "tokens": data.get("usage", {}).get("total_tokens", 0)
            }
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_available():
            raise ValueError("Volcano Engine API key or endpoint ID not configured")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.endpoint_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or 4096,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]
                        if line.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(line)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue


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
        messages: List[Dict[str, str]],
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
        
        return {
            "content": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
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
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMManager:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
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
            providers_status.append({
                "provider": "volcano",
                "available": True,
                "models": [
                    {"id": "doubao-pro", "name": "豆包 Pro", "provider": "volcano", "context_window": 128000, "supports_functions": True, "supports_vision": False},
                    {"id": "doubao-lite", "name": "豆包 Lite", "provider": "volcano", "context_window": 128000, "supports_functions": True, "supports_vision": False},
                    {"id": "doubao-vision", "name": "豆包 Vision", "provider": "volcano", "context_window": 128000, "supports_functions": True, "supports_vision": True}
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
