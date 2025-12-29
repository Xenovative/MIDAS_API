from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from backend.database import get_db
from backend.models import Conversation, Message, Bot, User
from backend.schemas import ChatRequest, ChatResponse, MessageResponse
from backend.auth import get_current_user, get_current_user_optional
from backend.vector_store import vector_store
from backend.reading_flow_rag import reading_flow_rag
from backend.deep_research_rag import hybrid_rag
from backend.image_providers import image_manager
from backend.video_providers import video_manager
from backend.llm_providers import llm_manager
from backend.agent_tools import agent_tool_manager
from datetime import datetime
from pathlib import Path
import json
import re
import base64
import os
import uuid
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


def save_uploaded_images(base64_images: list[str]) -> list[str]:
    """Save base64 images to disk and return file paths
    
    Args:
        base64_images: List of base64 encoded image strings
        
    Returns:
        List of static URL paths (e.g., '/static/uploads/abc123.jpg')
    """
    upload_dir = Path("backend/static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    for img_b64 in base64_images:
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = upload_dir / filename
        
        # Decode and save
        img_data = base64.b64decode(img_b64)
        with open(filepath, "wb") as f:
            f.write(img_data)
        
        # Return full static path for frontend
        saved_paths.append(f"/static/uploads/{filename}")
    
    return saved_paths


def detect_image_generation_request(message: str, has_images: bool = False) -> tuple[bool, str, bool]:
    """Detect if message is requesting image generation and extract prompt
    
    Returns:
        (is_image_request, prompt, is_img2img)
    """
    message_lower = message.lower().strip()
    
    # Check for image-to-image patterns (requires uploaded image)
    if has_images:
        img2img_patterns = [
            r"(?:transform|modify|edit|change|alter|convert|turn|make)\s+(?:this|the)\s+(?:image|picture|photo)",
            r"(?:apply|add)\s+(?:a\s+)?(?:style|effect|filter)",
            r"make\s+(?:it|this)",
            r"turn\s+(?:it|this)\s+into",
            r"(?:variation|version)\s+of\s+(?:this|the)",
            # Catch references to uploaded content
            r"(?:this|the)\s+(?:girl|boy|person|man|woman|face|scene|photo|picture)",
            r"(?:generate|create|make|draw)\s+(?:an?\s+)?(?:image|picture).*(?:this|the)\s+(?:girl|boy|person|man|woman|scene)",
        ]
        
        for pattern in img2img_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                # Extract the transformation description
                prompt = message.strip()
                prompt = re.sub(r'\s*(?:please|pls|thanks|thank you)\.?$', '', prompt, flags=re.IGNORECASE)
                return True, prompt, True
    
    # Check for text-to-image patterns
    text2img_patterns = [
        r"(?:generate|create|make|draw|paint|design|produce)\s+(?:an?\s+)?image\s+(?:of\s+)?(.+)",
        r"(?:generate|create|make|draw|paint|design|produce)\s+(?:a\s+)?(?:picture|photo|illustration|artwork)\s+(?:of\s+)?(.+)",
        r"image\s+(?:generation|of):\s*(.+)",
        r"draw\s+(?:me\s+)?(.+)",
        r"paint\s+(?:me\s+)?(.+)",
    ]
    
    for pattern in text2img_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            prompt = match.group(1).strip()
            # Clean up common endings
            prompt = re.sub(r'\s*(?:please|pls|thanks|thank you)\.?$', '', prompt, flags=re.IGNORECASE)
            return True, prompt, False
    
    return False, "", False


# -------- Video generation (Volcano Seedance) --------
class VideoGenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    size: Optional[str] = "1280x720"
    duration: Optional[int] = 5
    watermark: Optional[bool] = True
    camera_fixed: Optional[bool] = True
    generate_audio: Optional[bool] = True
    ratio: Optional[str] = None


@router.post("/video_generate")
async def generate_video(req: VideoGenerateRequest):
    """Direct video generation endpoint (Volcano Seedance)."""
    prompt = req.prompt
    model = req.model or os.getenv("VOLCANO_VIDEO_ENDPOINT") or "seedance-1.5-pro"
    size = req.size or "1280x720"
    duration = req.duration if req.duration is not None else 5
    watermark = req.watermark if req.watermark is not None else True
    camera_fixed = req.camera_fixed if req.camera_fixed is not None else True
    generate_audio = req.generate_audio if req.generate_audio is not None else True
    ratio = req.ratio

    print(f"🎬 Video generate requested: model={model}, size={size}, duration={duration}, watermark={watermark}, camera_fixed={camera_fixed}, audio={generate_audio}, ratio={ratio}")
    videos = await video_manager.generate(
        prompt=prompt,
        model=model,
        size=size,
        duration=duration,
        watermark=watermark,
        camera_fixed=camera_fixed,
        generate_audio=generate_audio,
        ratio=ratio,
    )

    if not videos:
        raise HTTPException(status_code=500, detail="No video generated")

    video_url = videos[0].get("url")
    if not video_url:
        raise HTTPException(status_code=500, detail="Video generated but no URL returned")

    return {
        "url": video_url,
        "type": videos[0].get("type", "video"),
        "revised_prompt": videos[0].get("revised_prompt"),
    }


async def generate_image_from_prompt(prompt: str, model: str = "gpt-image-1", image: Optional[str] = None, reference_images: Optional[List[str]] = None, size: str = "1024x1024", image_fidelity: str = "high", moderation: str = "low") -> dict:
    """Generate image using configured image provider
    
    Args:
        prompt: Text prompt for generation
        model: Image generation model to use
        image: Optional base64 encoded image for img2img/editing
        reference_images: Optional list of base64 encoded reference images
        size: Image dimensions (e.g., "1024x1024")
        image_fidelity: Image quality/fidelity (low, medium, high)
        moderation: Content moderation level (low, medium, high)
    """
    try:
        # If caller passed a video endpoint/model, route to video manager instead of image flow
        model_lower = model.lower() if model else ""
        if (
            ("seedance" in model_lower or "video" in model_lower)
            or (os.getenv("VOLCANO_VIDEO_ENDPOINT") and model == os.getenv("VOLCANO_VIDEO_ENDPOINT"))
        ):
            print(f"🎬 Detected video model in image route, delegating to video manager: model={model}")
            videos = await video_manager.generate(prompt=prompt, model=model, size=size)
            if not videos:
                raise ValueError("No video generated")
            video_url = videos[0].get("url")
            if not video_url:
                raise ValueError("Video generated but no URL returned")
            return {
                "url": video_url,
                "type": videos[0].get("type", "video"),
                "revised_prompt": videos[0].get("revised_prompt"),
            }

        print(f"🎨 Generating image with model: {model}")
        print(f"📝 Prompt: {prompt}")
        print(f"🖼️ Has input image: {bool(image)}")
        
        # GPT-Image-1 and DALL-E 2 support native image editing
        if image and model in ["gpt-image-1", "dall-e-2"]:
            print(f"✅ Using {model} native image editing")
            # These models can directly edit images with the prompt
            quality = "auto" if model == "gpt-image-1" else "standard"
        elif image and model == "dall-e-3":
            print("🔍 DALL-E 3 doesn't support image editing, using vision model to enhance prompt...")
            from backend.llm_providers import llm_manager
            
            try:
                vision_provider = llm_manager.get_provider("openai")
                image_size_kb = len(image) * 3 / 4 / 1024
                print(f"📏 Image size: {image_size_kb:.1f} KB")
                
                vision_messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this image and create a DALL-E prompt to recreate it with this change: '{prompt}'. Keep the subject but apply the requested modification. Output ONLY the prompt."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                            }
                        ]
                    }
                ]
                
                vision_response = await vision_provider.chat(
                    vision_messages,
                    "gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=300
                )
                
                enhanced_prompt = vision_response["content"]
                print(f"✨ Enhanced prompt: {enhanced_prompt[:200]}...")
                
                if "sorry" in enhanced_prompt.lower() or "can't" in enhanced_prompt.lower():
                    print(f"⚠️ Vision model refused, using original prompt")
                else:
                    prompt = enhanced_prompt
                    image = None  # Don't pass image to DALL-E
            except Exception as vision_error:
                print(f"⚠️ Vision analysis failed: {vision_error}")
                image = None
            
            quality = "standard"
        else:
            # Text-to-image generation
            quality = "auto" if model == "gpt-image-1" else "standard"
        
        images = await image_manager.generate(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            n=1,
            image=image,
            reference_images=reference_images,
            image_fidelity=image_fidelity,
            moderation=moderation
        )
        
        if images:
            image_url = images[0].get("url")
            print(f"✅ Image generated successfully")
            
            if not image_url:
                raise ValueError("Image generated but no URL returned")
            
            # If it's a data URL, save to disk and return file path
            if image_url.startswith("data:"):
                print(f"💾 Saving data URL to disk...")
                # Extract base64 data
                base64_data = image_url.split(",", 1)[1]
                # Save using the same helper (returns full /static/uploads/... path)
                saved_paths = save_uploaded_images([base64_data])
                image_url = saved_paths[0]
                print(f"✅ Saved generated image to: {image_url}")
            else:
                print(f"🔗 HTTP URL: {image_url[:100]}...")
            
            print(f"📦 Revised prompt: {images[0].get('revised_prompt', 'None')}")
            
            return {
                "url": image_url,
                "revised_prompt": images[0].get("revised_prompt"),
                "type": images[0].get("type", "image")
            }
        else:
            raise ValueError("No images generated")
    except Exception as e:
        print(f"❌ Image generation error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


async def fetch_realtime_context(query: str) -> tuple[Optional[str], list[dict]]:
    """Run web search tool to gather up-to-date info"""
    tool = agent_tool_manager.get_tool("web_search")
    if not tool or not query:
        return None, []
    exec_record = {
        "tool_name": "web_search",
        "input": {"query": query},
        "status": "pending"
    }
    try:
        result = await tool.execute(query=query, max_results=5)
        exec_record["output"] = result
        if not result.get("success"):
            exec_record["status"] = "error"
            exec_record["error"] = result.get("error", "Unknown error")
            return None, [exec_record]
        exec_record["status"] = "success"
        results = result.get("results", [])
        if not results:
            return None, [exec_record]
        lines = []
        for idx, item in enumerate(results[:5]):
            title = item.get("title") or item.get("body") or item.get("href") or "Result"
            snippet = item.get("body") or item.get("snippet") or item.get("description") or ""
            link = item.get("href") or item.get("link") or ""
            entry = f"{idx + 1}. {title.strip()}"
            if snippet:
                entry += f"\n   {snippet.strip()}"
            if link:
                entry += f"\n   Source: {link}"
            lines.append(entry)
        context_text = "\n".join(lines)
        return context_text, [exec_record]
    except Exception as exc:
        exec_record["status"] = "error"
        exec_record["error"] = str(exc)
        return None, [exec_record]


async def fetch_rag_context(query: str, bot_id: str, conversation_id: str, db: AsyncSession, use_deep_research: bool = False) -> tuple[Optional[str], list[dict]]:
    """Retrieve relevant context from bot's or conversation's knowledge base using RAG"""
    
    # Get bot configuration if bot is specified
    bot = None
    top_k = 15  # Increased from 5 to get more context
    similarity_threshold = 0.6  # Lowered from 0.7 to include more chunks
    
    if bot_id:
        result = await db.execute(select(Bot).where(Bot.id == bot_id))
        bot = result.scalar_one_or_none()
        if bot and bot.use_rag:
            top_k = bot.rag_top_k
            similarity_threshold = bot.rag_similarity_threshold
    
    exec_record = {
        "tool_name": "rag_retrieval",
        "input": {"query": query, "bot_id": bot_id, "conversation_id": conversation_id},
        "status": "pending"
    }
    
    try:
        # Search vector store (bot docs + conversation docs)
        results = await vector_store.search(
            db=db,
            query=query,
            bot_id=bot_id if bot and bot.use_rag else None,
            conversation_id=conversation_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        exec_record["output"] = {"results_count": len(results)}
        
        if not results:
            exec_record["status"] = "success"
            return None, [exec_record]
        
        exec_record["status"] = "success"
        
        # Use hybrid RAG: auto-detects if deep research is needed
        # Complex queries → Deep research with o1-mini
        # Simple queries → Fast reading flow
        
        # Check if deep research should be forced
        force_deep = use_deep_research  # From frontend toggle
        
        # Also check if bot has deep research enabled in meta_data
        if bot_id and not force_deep:
            bot_result = await db.execute(select(Bot).where(Bot.id == bot_id))
            bot = bot_result.scalar_one_or_none()
            if bot and bot.meta_data and bot.meta_data.get('use_deep_research'):
                force_deep = True
                print(f"🔬 Bot has deep research enabled in meta_data")
        
        if force_deep:
            print(f"🔬 Deep research FORCED by user toggle")
        
        context_text = await hybrid_rag.query(
            query=query,
            retrieved_chunks=results,
            use_deep_research=force_deep,  # Can be forced by user or bot settings
            complexity_threshold=20  # Lower threshold (more aggressive)
        )
        
        return context_text, [exec_record]
    except Exception as exc:
        exec_record["status"] = "error"
        exec_record["error"] = str(exc)
        print(f"❌ RAG retrieval error: {exc}")
        return None, [exec_record]


async def process_agent_tools(
    messages: list,
    model: str,
    provider: str,
    conversation_id: str,
    db: AsyncSession,
    original_prompt: str | None = None,
    uploaded_images: list | None = None
) -> tuple[str, list]:
    """Process agent tools - messages are text-only, images passed separately"""
    agent_executions = []
    uploaded_image = uploaded_images[0] if uploaded_images else None

    def extract_text(message_content):
        if isinstance(message_content, str):
            return message_content
        if isinstance(message_content, list):
            parts = []
            for item in message_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(parts)
        return ""

    user_message_text = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message_text = extract_text(msg.get("content"))
            break

    if not user_message_text and original_prompt:
        user_message_text = original_prompt

    tool_context_sections: list[str] = []

    async def run_tool(tool_name: str, tool_input: dict, formatter) -> None:
        tool = agent_tool_manager.get_tool(tool_name)
        if not tool:
            print(f"⚠️ Tool not found: {tool_name}")
            return
        exec_record = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "status": "pending"
        }
        print(f"🔧 Running tool: {tool_name} with input: {tool_input}")
        try:
            # Pass uploaded_image to image generation tool
            if tool_name == "generate_image":
                result = await tool.execute(**tool_input, uploaded_image=uploaded_image)
            else:
                result = await tool.execute(**tool_input)
            
            # Don't log result - may contain base64 image data
            print(f"📊 Tool {tool_name} executed")
            exec_record["tool_output"] = result
            
            if not result.get("success", True):
                exec_record["status"] = "error"
                exec_record["error"] = result.get("error", "Unknown error")
                print(f"❌ Tool failed: {exec_record['error']}")
            else:
                exec_record["status"] = "success"
                formatted = formatter(result)
                if formatted:
                    tool_context_sections.append(formatted)
                    print(f"✅ Tool succeeded")
        except Exception as exc:
            exec_record["status"] = "error"
            exec_record["error"] = str(exc)
            print(f"💥 Tool exception: {exc}")
        finally:
            agent_executions.append(exec_record)
            print(f"📝 Execution recorded for {tool_name}")

    # Use LLM function calling to decide which tools to use
    from backend.agent_tools import agent_tool_manager
    
    tools = agent_tool_manager.get_tools_for_llm()
    
    # Strip images from message history to avoid token limits
    # Images are only needed for the current tool execution, not in conversation context
    print(f"🔍 Original messages count: {len(messages)}")
    for i, msg in enumerate(messages):
        content_type = type(msg.get("content")).__name__
        if isinstance(msg.get("content"), list):
            print(f"  Message {i}: role={msg.get('role')}, content is list with {len(msg['content'])} items")
        elif isinstance(msg.get("content"), str):
            print(f"  Message {i}: role={msg.get('role')}, content length={len(msg['content'])}")
    
    clean_messages = []
    for msg in messages:
        clean_msg = msg.copy()
        if isinstance(clean_msg.get("content"), list):
            # Remove image_url items from content array
            clean_msg["content"] = [
                item for item in clean_msg["content"]
                if item.get("type") != "image_url"
            ]
            # If only one text item left, simplify to string
            if len(clean_msg["content"]) == 1 and clean_msg["content"][0].get("type") == "text":
                clean_msg["content"] = clean_msg["content"][0]["text"]
            # If no content left, use empty string
            elif not clean_msg["content"]:
                clean_msg["content"] = ""
        clean_messages.append(clean_msg)
    
    print(f"✅ Cleaned messages count: {len(clean_messages)}")
    total_chars = 0
    for i, msg in enumerate(clean_messages):
        if isinstance(msg.get("content"), str):
            total_chars += len(msg['content'])
            print(f"  Clean message {i}: role={msg.get('role')}, content length={len(msg['content'])}")
        elif isinstance(msg.get("content"), list):
            print(f"  Clean message {i}: role={msg.get('role')}, content is STILL A LIST with {len(msg['content'])} items - THIS IS THE BUG!")
    print(f"📊 Total characters in clean_messages: {total_chars} (~{total_chars // 4} tokens)")
    
    # Add context about uploaded images
    if uploaded_image:
        clean_messages.append({
            "role": "system",
            "content": "The user has uploaded an image. If they want to transform, modify, or generate a new version of it, use the generate_image tool. The uploaded image will be automatically passed to the tool."
        })
    
    try:
        # Estimate tokens before calling
        total_chars = sum(len(str(m.get("content", ""))) for m in clean_messages)
        print(f"📊 About to call LLM with {len(clean_messages)} messages, ~{total_chars} chars (~{total_chars // 4} tokens)")
        
        # Call LLM with available tools
        response = await llm_manager.get_provider(provider).chat(
            clean_messages,
            model,
            tools=tools
        )
        
        # Check if LLM wants to use any tools
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                # Formatter that doesn't log base64 data
                def format_result(result):
                    if tool_name == "generate_image":
                        return "Image generated successfully"
                    return f"{tool_name} result: {json.dumps(result, indent=2)}"
                
                await run_tool(tool_name, tool_args, format_result)
        
        # Get final response after tool execution
        if tool_context_sections:
            clean_messages.append({
                "role": "system",
                "content": "Tool outputs:\n" + "\n\n".join(tool_context_sections)
            })
        
        final_response = await llm_manager.get_provider(provider).chat(
            clean_messages,
            model
        )
        
        return final_response["content"], agent_executions
    except Exception as e:
        print(f"❌ Agent processing error: {e}")
        # Fallback to simple response (use clean_messages to avoid token limits)
        response = await llm_manager.get_provider(provider).chat(clean_messages, model)
        return response["content"], agent_executions


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message and get a response"""
    
    # Get or create conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            title=request.message[:50],
            bot_id=request.bot_id  # Store bot_id in conversation
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    # Save uploaded images to disk immediately
    image_paths = save_uploaded_images(request.images) if request.images else None
    if image_paths:
        print(f"💾 Saved {len(image_paths)} images to: {image_paths}")
    
    # Handle inline documents (for Google AI)
    inline_documents = None
    if request.documents:
        inline_documents = [{"mime_type": doc.mime_type, "data": doc.data} for doc in request.documents]
        print(f"📄 Received {len(inline_documents)} inline documents for Google AI")
    
    # Build meta_data for user message
    user_meta_data = {}
    if image_paths:
        user_meta_data["images"] = image_paths
    if inline_documents:
        user_meta_data["documents"] = inline_documents
    
    # Save user message with file paths and inline documents
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        meta_data=user_meta_data if user_meta_data else None
    )
    db.add(user_message)
    await db.commit()
    
    # Get conversation history
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    history = messages_result.scalars().all()
    
    # Build conversation history for LLM
    formatted_messages = []
    if request.system_prompt:
        formatted_messages.append({"role": "system", "content": request.system_prompt})
    
    # Check if using Google AI provider (needs special multimodal format)
    is_google_provider = request.provider == "google"
    
    for msg in history:
        # For Google AI, include images/documents inline in content
        if is_google_provider and msg.meta_data:
            content_parts = []
            
            # Add images if present
            msg_images = msg.meta_data.get("images", [])
            for img_path in msg_images:
                clean_path = img_path.replace("/static/", "")
                file_path = Path("backend/static") / clean_path
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()
                    ext = file_path.suffix.lower()
                    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
                    mime_type = mime_map.get(ext, "image/jpeg")
                    content_parts.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}})
            
            # Add documents if present
            msg_docs = msg.meta_data.get("documents", [])
            for doc in msg_docs:
                content_parts.append({"type": "document", "document": doc})
            
            # Add text content
            if msg.content:
                content_parts.append({"type": "text", "text": msg.content})
            
            if content_parts:
                formatted_messages.append({"role": msg.role, "content": content_parts})
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        else:
            formatted_messages.append({"role": msg.role, "content": msg.content})
    
    # Inject RAG context from bot or conversation documents
    rag_context = None
    rag_execs: list[dict] = []
    rag_context, rag_execs = await fetch_rag_context(request.message, request.bot_id, conversation.id, db, request.use_deep_research)
    if rag_context:
        formatted_messages.append({
            "role": "system",
            "content": "Relevant information from knowledge base:\n" + rag_context
        })
        print("📚 RAG context added")
    
    # Inject realtime context if requested
    realtime_context = None
    realtime_execs: list[dict] = []
    if request.use_realtime_data:
        realtime_context, realtime_execs = await fetch_realtime_context(request.message)
        if realtime_context:
            formatted_messages.append({
                "role": "system",
                "content": "Latest web research results:\n" + realtime_context
            })
            print("🌐 Realtime context added")
        else:
            print("⚠️ Realtime context unavailable")

    # Check if this is an image or video generation model
    # Use image_manager for robust detection
    all_image_models = [m["id"] for m in image_manager.get_available_models()]
    
    is_volcano_media = False
    if request.provider == "volcano":
        from backend.config import settings
        media_keywords = ["seedance", "seedream", "video-generation", "t2v", "i2v"]
        
        # Check if it matches specialized endpoints or has media keywords or is in the image manager
        is_volcano_media = (
            request.model in all_image_models or
            any(kw in request.model.lower() for kw in media_keywords) or
            (settings.volcano_image_endpoint and request.model == settings.volcano_image_endpoint) or
            (settings.volcano_video_endpoint and request.model == settings.volcano_video_endpoint)
        )
        print(f"🔍 Volcano Media Check: model={request.model}, is_media={is_volcano_media}")
        print(f"   Image EP: {settings.volcano_image_endpoint}")
        print(f"   Video EP: {settings.volcano_video_endpoint}")
        
    is_image_model = request.model in all_image_models or is_volcano_media
    
    generated_images = []
    generated_videos = []
    
    # Get LLM response
    try:
        agent_executions = list(rag_execs) + list(realtime_execs)
        
        if is_image_model:
            # Direct image generation when image model is selected
            print(f"🎨 Image model selected: {request.model}")
            print(f"📝 Generating image from prompt: {request.message[:100]}...")
            
            # Multi-turn image generation: Check if there's a previous generated image
            input_image = None
            reference_images_list = None
            
            if request.images:
                # User uploaded image(s)
                if len(request.images) == 1:
                    # Single image - use for editing
                    input_image = request.images[0]
                    print(f"🖼️ Using user-uploaded image for editing")
                else:
                    # Multiple images - use as references (GPT-Image-1 only)
                    if request.model == "gpt-image-1":
                        reference_images_list = request.images
                        print(f"🎨 Using {len(request.images)} images as references")
                    else:
                        # For other models, just use first image
                        input_image = request.images[0]
                        print(f"🖼️ Using first uploaded image (model doesn't support references)")
            else:
                # Check if the last assistant message has a generated image (multi-turn)
                if len(history) >= 2:
                    last_assistant_msg = None
                    for msg in reversed(history):
                        if msg.role == "assistant":
                            last_assistant_msg = msg
                            break
                    
                    if last_assistant_msg and last_assistant_msg.meta_data:
                        last_images = last_assistant_msg.meta_data.get("images", [])
                        if last_images:
                            # Load the last generated image for multi-turn editing
                            last_image_path = last_images[0]
                            print(f"🔄 Multi-turn: Using previous generated image: {last_image_path}")
                            
                            # Load image from disk and convert to base64
                            from pathlib import Path
                            clean_path = last_image_path.replace("/static/", "")
                            file_path = Path("backend/static") / clean_path
                            if file_path.exists():
                                with open(file_path, "rb") as f:
                                    input_image = base64.b64encode(f.read()).decode()
                                print(f"✅ Loaded previous image for multi-turn editing")
                            else:
                                print(f"⚠️ Previous image not found on disk")
            
            try:
                # Generate image directly
                image_result = await generate_image_from_prompt(
                    prompt=request.message,
                    model=request.model,
                    image=input_image,
                    reference_images=reference_images_list,
                    size=request.image_size or "1024x1024",
                    image_fidelity=request.image_fidelity or "high",
                    moderation=request.moderation or "low"
                )
                
                # Format response with image or video
                media_type = "video" if "seedance" in request.model.lower() or "video" in request.model.lower() else "image"
                response_content = f"🎨 Generated {media_type} using {request.model}"
                if image_result.get("revised_prompt"):
                    response_content += f"\n\n**Revised prompt:** {image_result['revised_prompt']}"
                
                # Add to appropriate list in meta_data
                if media_type == "video":
                    generated_videos = [image_result["url"]]
                    generated_images = []
                else:
                    generated_images = [image_result["url"]]
                    generated_videos = []
                
                print(f"✅ {media_type.capitalize()} generated successfully: {image_result['url'][:100]}")
            except Exception as img_error:
                print(f"❌ Image generation failed: {img_error}")
                
                # Parse error message for better user feedback
                error_msg = str(img_error)
                if "safety system" in error_msg.lower() or "moderation_blocked" in error_msg:
                    response_content = "🚫 **Content Policy Violation**\n\nYour image generation request was blocked by OpenAI's safety system. The content may violate their usage policies.\n\nPlease try:\n- Rephrasing your prompt\n- Using more general descriptions\n- Avoiding sensitive content"
                elif "rate_limit" in error_msg.lower():
                    response_content = "⏱️ **Rate Limit Reached**\n\nToo many requests. Please wait a moment and try again."
                elif "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                    response_content = "💳 **Quota Exceeded**\n\nYour API quota has been exceeded. Please check your OpenAI account."
                elif "invalid" in error_msg.lower():
                    response_content = f"⚠️ **Invalid Request**\n\n{error_msg}"
                else:
                    response_content = f"❌ **Image Generation Failed**\n\n{error_msg}"
                
                generated_images = []
        
        elif request.use_agent:
            llm_provider = llm_manager.get_provider(request.provider)
            # Load base64 from file paths only when needed for tools
            uploaded_images_b64 = []
            if image_paths:
                for path in image_paths:
                    # Strip /static/ prefix if present
                    clean_path = path.replace("/static/", "")
                    file_path = Path("backend/static") / clean_path
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            uploaded_images_b64.append(base64.b64encode(f.read()).decode())
                print(f"🤖 Agent mode: loaded {len(uploaded_images_b64)} images from disk for tools")
            
            response_content, agent_executions = await process_agent_tools(
                formatted_messages,
                request.model,
                request.provider,
                conversation.id,
                db,
                original_prompt=request.message,
                uploaded_images=uploaded_images_b64
            )
            agent_executions = list(realtime_execs) + agent_executions
            
            # Extract generated image URLs from agent executions
            generated_images = []
            for exec_record in agent_executions:
                if exec_record.get("tool_name") == "generate_image" and exec_record.get("status") == "success":
                    tool_output = exec_record.get("tool_output", {})
                    if tool_output.get("url"):
                        generated_images.append(tool_output["url"])
        else:
            llm_provider = llm_manager.get_provider(request.provider)
            response = await llm_provider.chat(
                formatted_messages,
                request.model,
                request.temperature,
                request.max_tokens
            )
            response_content = response["content"]
            
            # If there's reasoning content (DeepSeek R1 / Volcano), wrap it in <think> tags
            # so the frontend can format it consistently with streaming mode
            if response.get("reasoning_content"):
                response_content = f"<think>\n{response['reasoning_content']}\n</think>\n\n{response_content}"
                
            agent_executions = list(realtime_execs)
            generated_images = []
        
        # Save assistant message with generated media in meta_data
        meta_data = {"agent_executions": agent_executions} if agent_executions else {}
        if generated_images:
            meta_data["images"] = generated_images
        if generated_videos:
            meta_data["videos"] = generated_videos
            
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_content,
            model=request.model,
            meta_data=meta_data if meta_data else None
        )
        db.add(assistant_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        # Generate title for new conversations (first exchange)
        if len(history) == 1:  # Only user message exists
            # Use bot name if provided, otherwise generate a title
            if request.bot_name:
                conversation.title = f"Chat with {request.bot_name}"
                print(f"✅ Using bot name for title: {conversation.title}")
            else:
                try:
                    # Always use GPT-4o for title generation (image models don't support chat)
                    title_llm = llm_manager.get_provider("openai")
                    title_prompt = [
                        {"role": "user", "content": f"Generate a concise 3-5 word title for a conversation that starts with: '{request.message[:100]}'. Respond with ONLY the title, no quotes or extra text."}
                    ]
                    title_response = await title_llm.chat(
                        title_prompt,
                        "gpt-4o-mini",  # Use fast, cheap model for titles
                        temperature=0.7,
                        max_tokens=20
                    )
                    conversation.title = title_response["content"].strip().strip('"\'')[:60]
                    print(f"✅ Generated title: {conversation.title}")
                except Exception as e:
                    print(f"Failed to generate title: {e}")
                    # Keep the default title if generation fails
        
        await db.commit()
        await db.refresh(assistant_message)
        
        return ChatResponse(
            conversation_id=conversation.id,
            message=MessageResponse.model_validate(assistant_message),
            agent_executions=agent_executions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Stream chat response"""
    
    # Get or create conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            title=request.message[:50],
            bot_id=request.bot_id  # Store bot_id in conversation
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    # Save uploaded images to disk immediately
    image_paths = save_uploaded_images(request.images) if request.images else None
    if image_paths:
        print(f"💾 Saved {len(image_paths)} images (streaming)")
    
    # Handle inline documents (for Google AI)
    inline_documents = None
    if request.documents:
        inline_documents = [{"mime_type": doc.mime_type, "data": doc.data} for doc in request.documents]
        print(f"📄 Received {len(inline_documents)} inline documents for Google AI")
    
    # Build meta_data for user message
    user_meta_data = {}
    if image_paths:
        user_meta_data["images"] = image_paths
    if inline_documents:
        user_meta_data["documents"] = inline_documents
    
    # Save user message with file paths and inline documents
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        meta_data=user_meta_data if user_meta_data else None
    )
    db.add(user_message)
    await db.commit()
    
    # Get conversation history
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    history = messages_result.scalars().all()
    
    # Build conversation history for LLM
    formatted_messages = []
    if request.system_prompt:
        formatted_messages.append({"role": "system", "content": request.system_prompt})
    
    # Check if using Google AI provider (needs special multimodal format)
    is_google_provider = request.provider == "google"
    
    for msg in history:
        # For Google AI, include images/documents inline in content
        if is_google_provider and msg.meta_data:
            content_parts = []
            
            # Add images if present
            msg_images = msg.meta_data.get("images", [])
            for img_path in msg_images:
                # Load image from disk and convert to base64
                clean_path = img_path.replace("/static/", "")
                file_path = Path("backend/static") / clean_path
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()
                    # Determine mime type from extension
                    ext = file_path.suffix.lower()
                    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
                    mime_type = mime_map.get(ext, "image/jpeg")
                    content_parts.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}})
            
            # Add documents if present
            msg_docs = msg.meta_data.get("documents", [])
            for doc in msg_docs:
                content_parts.append({"type": "document", "document": doc})
            
            # Add text content
            if msg.content:
                content_parts.append({"type": "text", "text": msg.content})
            
            if content_parts:
                formatted_messages.append({"role": msg.role, "content": content_parts})
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        else:
            # Standard text-only format for other providers
            formatted_messages.append({"role": msg.role, "content": msg.content})
    
    async def generate():
        try:
            llm_provider = llm_manager.get_provider(request.provider)
            full_response = ""
            generated_images = []
            generated_videos = []
            
            # Send conversation ID first
            yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation.id})}\n\n"
            
            # Optionally add RAG context
            rag_context = None
            rag_execs: list[dict] = []
            rag_context, rag_execs = await fetch_rag_context(request.message, request.bot_id, conversation.id, db, request.use_deep_research)
            if rag_context:
                formatted_messages.append({
                    "role": "system",
                    "content": "Relevant information from knowledge base:\n" + rag_context
                })
                yield f"data: {json.dumps({'type': 'content', 'content': '📚 Retrieved context from knowledge base...'})}\n\n"
            if rag_execs:
                yield f"data: {json.dumps({'type': 'agent_executions', 'executions': rag_execs})}\n\n"
            
            # Optionally add realtime context
            realtime_context = None
            realtime_execs: list[dict] = []
            if request.use_realtime_data:
                realtime_context, realtime_execs = await fetch_realtime_context(request.message)
                if realtime_context:
                    formatted_messages.append({
                        "role": "system",
                        "content": "Latest web research results:\n" + realtime_context
                    })
                    yield f"data: {json.dumps({'type': 'content', 'content': '🌐 Pulled fresh info from the web...'})}\n\n"
                if realtime_execs:
                    yield f"data: {json.dumps({'type': 'agent_executions', 'executions': realtime_execs})}\n\n"

            agent_executions = list(rag_execs) + list(realtime_execs)
            
            # Check if this is an image or video generation model
            # Use image_manager for robust detection
            all_image_models = [m["id"] for m in image_manager.get_available_models()]
            
            is_volcano_media = False
            if request.provider == "volcano":
                from backend.config import settings
                media_keywords = ["seedance", "seedream", "video-generation", "t2v", "i2v"]
                is_volcano_media = (
                    request.model in all_image_models or
                    any(kw in request.model.lower() for kw in media_keywords) or
                    (settings.volcano_image_endpoint and request.model == settings.volcano_image_endpoint) or
                    (settings.volcano_video_endpoint and request.model == settings.volcano_video_endpoint)
                )
                
            is_image_model = request.model in all_image_models or is_volcano_media
            
            if is_image_model:
                media_type = "video" if "seedance" in request.model.lower() or "video" in request.model.lower() or (settings.volcano_video_endpoint and request.model == settings.volcano_video_endpoint) else "image"
                # Direct media generation when model is selected
                yield f"data: {json.dumps({'type': 'content', 'content': f'🎨 Generating {media_type} with {request.model}...'})}\n\n"
                
                # Multi-turn image generation: Check if there's a previous generated image
                input_image = None
                reference_images_list = None
                
                if request.images:
                    # User uploaded image(s)
                    if len(request.images) == 1:
                        # Single image - use for editing
                        input_image = request.images[0]
                        print(f"🖼️ Using user-uploaded image for editing")
                    else:
                        # Multiple images - use as references (GPT-Image-1 only)
                        if request.model == "gpt-image-1":
                            reference_images_list = request.images
                            print(f"🎨 Using {len(request.images)} images as references")
                            yield f"data: {json.dumps({'type': 'content', 'content': f'🎨 Using {len(request.images)} reference images...'})}\n\n"
                        else:
                            # For other models, just use first image
                            input_image = request.images[0]
                            print(f"🖼️ Using first uploaded image (model doesn't support references)")
                else:
                    # Check if the last assistant message has a generated image (multi-turn)
                    if len(history) >= 2:
                        last_assistant_msg = None
                        for msg in reversed(history):
                            if msg.role == "assistant":
                                last_assistant_msg = msg
                                break
                        
                        if last_assistant_msg and last_assistant_msg.meta_data:
                            last_images = last_assistant_msg.meta_data.get("images", [])
                            if last_images:
                                # Load the last generated image for multi-turn editing
                                last_image_path = last_images[0]
                                print(f"🔄 Multi-turn: Using previous generated image: {last_image_path}")
                                yield f"data: {json.dumps({'type': 'content', 'content': '🔄 Refining previous image...'})}\n\n"
                                
                                # Load image from disk and convert to base64
                                from pathlib import Path
                                clean_path = last_image_path.replace("/static/", "")
                                file_path = Path("backend/static") / clean_path
                                if file_path.exists():
                                    with open(file_path, "rb") as f:
                                        input_image = base64.b64encode(f.read()).decode()
                                    print(f"✅ Loaded previous image for multi-turn editing")
                                else:
                                    print(f"⚠️ Previous image not found on disk")
                
                try:
                    image_result = await generate_image_from_prompt(
                        prompt=request.message,
                        model=request.model,
                        image=input_image,
                        reference_images=reference_images_list,
                        size=request.image_size or "1024x1024",
                        image_fidelity=request.image_fidelity or "high",
                        moderation=request.moderation or "low"
                    )
                    
                    full_response = f"🎨 Generated {media_type} using {request.model}"
                    if image_result.get("revised_prompt"):
                        full_response += f"\n\n**Revised prompt:** {image_result['revised_prompt']}"
                    
                    # Send the generated media
                    if media_type == "video":
                        yield f"data: {json.dumps({'type': 'video', 'url': image_result['url']})}\n\n"
                        generated_videos = [image_result["url"]]
                        generated_images = []
                    else:
                        yield f"data: {json.dumps({'type': 'image', 'url': image_result['url']})}\n\n"
                        generated_images = [image_result["url"]]
                        generated_videos = []
                        
                    yield f"data: {json.dumps({'type': 'content', 'content': full_response})}\n\n"
                except Exception as img_error:
                    print(f"❌ Image generation failed: {img_error}")
                    
                    # Parse error message for better user feedback
                    error_msg = str(img_error)
                    if "safety system" in error_msg.lower() or "moderation_blocked" in error_msg:
                        full_response = "🚫 **Content Policy Violation**\n\nYour image generation request was blocked by OpenAI's safety system. The content may violate their usage policies.\n\nPlease try:\n- Rephrasing your prompt\n- Using more general descriptions\n- Avoiding sensitive content"
                    elif "rate_limit" in error_msg.lower():
                        full_response = "⏱️ **Rate Limit Reached**\n\nToo many requests. Please wait a moment and try again."
                    elif "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                        full_response = "💳 **Quota Exceeded**\n\nYour API quota has been exceeded. Please check your OpenAI account."
                    elif "invalid" in error_msg.lower():
                        full_response = f"⚠️ **Invalid Request**\n\n{error_msg}"
                    else:
                        full_response = f"❌ **Image Generation Failed**\n\n{error_msg}"
                    
                    yield f"data: {json.dumps({'type': 'content', 'content': full_response})}\n\n"
                    generated_images = []
            
            elif request.use_agent:
                # Load base64 from file paths only when needed for tools
                uploaded_images_b64 = []
                if image_paths:
                    for path in image_paths:
                        # Strip /static/ prefix if present
                        clean_path = path.replace("/static/", "")
                        file_path = Path("backend/static") / clean_path
                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                uploaded_images_b64.append(base64.b64encode(f.read()).decode())
                    print(f"🤖 Agent mode (streaming): loaded {len(uploaded_images_b64)} images from disk for tools")
                
                # Process via agent tools (non-streaming response)
                yield f"data: {json.dumps({'type': 'content', 'content': '🤖 Agent tools engaged...'})}\n\n"
                full_response, agent_executions = await process_agent_tools(
                    formatted_messages,
                    request.model,
                    request.provider,
                    conversation.id,
                    db,
                    original_prompt=request.message,
                    uploaded_images=uploaded_images_b64
                )
                agent_executions = list(realtime_execs) + agent_executions
                yield f"data: {json.dumps({'type': 'content', 'content': full_response})}\n\n"
                if agent_executions:
                    yield f"data: {json.dumps({'type': 'agent_executions', 'executions': agent_executions})}\n\n"
                
                # Extract generated image URLs from agent executions
                generated_images = []
                for exec_record in agent_executions:
                    if exec_record.get("tool_name") == "generate_image" and exec_record.get("status") == "success":
                        tool_output = exec_record.get("tool_output", {})
                        if tool_output.get("url"):
                            generated_images.append(tool_output["url"])
                            # Send image URL
                            yield f"data: {json.dumps({'type': 'image', 'url': tool_output['url']})}\n\n"
            else:
                # Normal LLM streaming
                async for chunk in llm_provider.chat_stream(
                    formatted_messages,
                    request.model,
                    request.temperature,
                    request.max_tokens
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                generated_images = []
            
            # Save final message
            meta_data = {"agent_executions": agent_executions} if agent_executions else {}
            if generated_images:
                meta_data["images"] = generated_images
            if generated_videos:
                meta_data["videos"] = generated_videos
                
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                model=request.model,
                meta_data=meta_data if meta_data else None
            )
            db.add(assistant_message)
            conversation.updated_at = datetime.utcnow()
            print(f"💾 Saved assistant message with meta_data: {assistant_message.meta_data is not None}")
            
            # Generate title for new conversations (first exchange)
            if len(history) == 1:  # Only user message exists
                # Use bot name if provided, otherwise generate a title
                if request.bot_name:
                    conversation.title = f"Chat with {request.bot_name}"
                    print(f"✅ Using bot name for title (streaming): {conversation.title}")
                    # Send title update to frontend
                    yield f"data: {json.dumps({'type': 'title', 'title': conversation.title})}\n\n"
                else:
                    try:
                        # Always use GPT-4o for title generation (image models don't support chat)
                        title_llm = llm_manager.get_provider("openai")
                        title_prompt = [
                            {"role": "user", "content": f"Generate a concise 3-5 word title for a conversation that starts with: '{request.message[:100]}'. Respond with ONLY the title, no quotes or extra text."}
                        ]
                        title_response = await title_llm.chat(
                            title_prompt,
                            "gpt-4o-mini",  # Use fast, cheap model for titles
                            temperature=0.7,
                            max_tokens=20
                        )
                        conversation.title = title_response["content"].strip().strip('"\'')[:60]
                        print(f"✅ Generated title: {conversation.title}")
                        # Send title update to frontend
                        yield f"data: {json.dumps({'type': 'title', 'title': conversation.title})}\n\n"
                    except Exception as e:
                        print(f"Failed to generate title: {e}")
            
            await db.commit()
            await db.refresh(assistant_message)
            
            # Include meta_data in done event so frontend can display images
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id, 'meta_data': assistant_message.meta_data})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
