from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import Conversation, Message, AgentExecution
from backend.schemas import ChatRequest, ChatResponse, MessageResponse
from backend.llm_providers import llm_manager
from backend.agent_tools import agent_tool_manager
from backend.config import settings
from backend.image_providers import image_manager
from datetime import datetime
from typing import Optional
import json
import re

router = APIRouter(prefix="/chat", tags=["chat"])


def detect_image_generation_request(message: str) -> tuple[bool, str]:
    """Detect if message is requesting image generation and extract prompt"""
    patterns = [
        r"(?:generate|create|make|draw|paint|design|produce)\s+(?:an?\s+)?image\s+(?:of\s+)?(.+)",
        r"(?:generate|create|make|draw|paint|design|produce)\s+(?:a\s+)?(?:picture|photo|illustration|artwork)\s+(?:of\s+)?(.+)",
        r"image\s+(?:generation|of):\s*(.+)",
        r"draw\s+(?:me\s+)?(.+)",
        r"paint\s+(?:me\s+)?(.+)",
    ]
    
    message_lower = message.lower().strip()
    
    for pattern in patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            prompt = match.group(1).strip()
            # Clean up common endings
            prompt = re.sub(r'\s*(?:please|pls|thanks|thank you)\.?$', '', prompt, flags=re.IGNORECASE)
            return True, prompt
    
    return False, ""


async def generate_image_from_prompt(prompt: str, model: str = "dall-e-3") -> dict:
    """Generate image using configured image provider"""
    try:
        images = await image_manager.generate(
            prompt=prompt,
            model=model,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        if images:
            return {
                "url": images[0]["url"],
                "revised_prompt": images[0].get("revised_prompt")
            }
        else:
            raise ValueError("No images generated")
    except Exception as e:
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


async def process_agent_tools(
    messages: list,
    model: str,
    provider: str,
    conversation_id: str,
    db: AsyncSession,
    original_prompt: str | None = None
) -> tuple[str, list]:
    """Process agent tools if needed"""
    agent_executions = []

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
            result = await tool.execute(**tool_input)
            print(f"📊 Tool result: {result}")
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
                    print(f"✅ Tool succeeded, added context")
        except Exception as exc:
            exec_record["status"] = "error"
            exec_record["error"] = str(exc)
            print(f"💥 Tool exception: {exc}")
        finally:
            agent_executions.append(exec_record)
            print(f"📝 Execution recorded: {exec_record}")

    lowered = user_message_text.lower()

    # Detect calculator usage
    math_pattern = re.search(r"(-?\d+(?:\.\d+)?\s*[\+\-\*/]\s*)+-?\d+(?:\.\d+)?", user_message_text.replace(",", ""))
    if math_pattern or any(keyword in lowered for keyword in ["calculate", "calculation", "compute"]):
        expression = math_pattern.group(0) if math_pattern else user_message_text
        await run_tool(
            "calculator",
            {"expression": expression},
            lambda result: f"Calculator result for `{expression}`: {result.get('result')}"
        )

    # Detect web scraping requests
    url_match = re.search(r"https?://\S+", user_message_text)
    if url_match and any(keyword in lowered for keyword in ["scrape", "summarize", "analyze", "read"]):
        target_url = url_match.group(0)
        await run_tool(
            "web_scrape",
            {"url": target_url},
            lambda result: (
                f"Content scraped from {target_url} (first 500 chars):\n"
                f"{result.get('content', '')[:500]}"
            )
        )

    # Detect web search necessity
    search_keywords = [
        "latest", "news", "today", "current", "recent", "update", "what's happening", "find"
    ]
    triggered_search = False
    if any(keyword in lowered for keyword in search_keywords):
        triggered_search = True
        await run_tool(
            "web_search",
            {"query": user_message_text, "max_results": 5},
            lambda result: "Web search results:\n" + "\n".join(
                [
                    f"- {item.get('title') or item.get('href') or 'Result'}: {item.get('snippet') or item.get('body') or ''}"
                    for item in result.get('results', [])[:5]
                ]
            )
        )

    # Ensure we always try at least one search when agent mode is on
    if not tool_context_sections and not triggered_search and user_message_text:
        await run_tool(
            "web_search",
            {"query": user_message_text, "max_results": 5},
            lambda result: "Web search results:\n" + "\n".join(
                [
                    f"- {item.get('title') or item.get('href') or 'Result'}: {item.get('snippet') or item.get('body') or ''}"
                    for item in result.get('results', [])[:5]
                ]
            )
        )

    llm_provider = llm_manager.get_provider(provider)
    augmented_messages = list(messages)
    if tool_context_sections:
        augmented_messages.append({
            "role": "system",
            "content": "Tool outputs:\n" + "\n\n".join(tool_context_sections)
        })
    response = await llm_provider.chat(augmented_messages, model)
    
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
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
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
    
    # Format messages for LLM
    formatted_messages = []
    
    # Add system prompt if provided
    if request.system_prompt:
        formatted_messages.append({"role": "system", "content": request.system_prompt})
        print(f"✅ System prompt added: {request.system_prompt[:100]}...")
    
    for msg in history:
        # Check if this is the last user message with images
        if msg.id == user_message.id and request.images:
            # Format with multimodal content
            content = [{"type": "text", "text": msg.content}]
            for img_base64 in request.images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                })
            formatted_messages.append({"role": msg.role, "content": content})
        else:
            formatted_messages.append({"role": msg.role, "content": msg.content})
    
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

    # Check if this is an image generation request
    is_image_request, image_prompt = detect_image_generation_request(request.message)
    
    # Get LLM response
    try:
        llm_provider = llm_manager.get_provider(request.provider)
        
        agent_executions = list(realtime_execs)

        if is_image_request:
            # Generate image
            try:
                image_data = await generate_image_from_prompt(image_prompt or request.message)
                response_content = f"I've generated an image for you:\n\n![Generated Image]({image_data['url']})\n\n**Prompt used:** {image_data['revised_prompt']}"
            except Exception as img_error:
                response_content = f"I tried to generate an image, but encountered an error: {str(img_error)}"
        elif request.use_agent:
            response_content, agent_executions = await process_agent_tools(
                formatted_messages,
                request.model,
                request.provider,
                conversation.id,
                db,
                original_prompt=request.message
            )
            agent_executions = list(realtime_execs) + agent_executions
        else:
            response = await llm_provider.chat(
                formatted_messages,
                request.model,
                request.temperature,
                request.max_tokens
            )
            response_content = response["content"]
            agent_executions = list(realtime_execs)
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_content,
            model=request.model
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
                    title_prompt = [
                        {"role": "user", "content": f"Generate a concise 3-5 word title for a conversation that starts with: '{request.message[:100]}'. Respond with ONLY the title, no quotes or extra text."}
                    ]
                    title_response = await llm_provider.chat(
                        title_prompt,
                        request.model,
                        temperature=0.7,
                        max_tokens=20
                    )
                    conversation.title = title_response["content"].strip().strip('"\'')[:60]
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
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
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
    
    # Format messages for LLM
    formatted_messages = []
    
    # Add system prompt if provided
    if request.system_prompt:
        formatted_messages.append({"role": "system", "content": request.system_prompt})
        print(f"✅ System prompt added (streaming): {request.system_prompt[:100]}...")
    
    for msg in history:
        # Check if this is the last user message with images
        if msg.id == user_message.id and request.images:
            # Format with multimodal content
            content = [{"type": "text", "text": msg.content}]
            for img_base64 in request.images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                })
            formatted_messages.append({"role": msg.role, "content": content})
        else:
            formatted_messages.append({"role": msg.role, "content": msg.content})
    
    async def generate():
        try:
            llm_provider = llm_manager.get_provider(request.provider)
            full_response = ""
            
            # Send conversation ID first
            yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation.id})}\n\n"
            
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

            # Check if this is an image generation request
            is_image_request, image_prompt = detect_image_generation_request(request.message)
            
            agent_executions = list(realtime_execs)

            if is_image_request:
                # Generate image
                try:
                    yield f"data: {json.dumps({'type': 'content', 'content': 'Generating image...'})}\n\n"
                    image_data = await generate_image_from_prompt(image_prompt or request.message)
                    full_response = f"I've generated an image for you:\n\n![Generated Image]({image_data['url']})\n\n**Prompt used:** {image_data['revised_prompt']}"
                    yield f"data: {json.dumps({'type': 'content', 'content': full_response})}\n\n"
                except Exception as img_error:
                    full_response = f"I tried to generate an image, but encountered an error: {str(img_error)}"
                    yield f"data: {json.dumps({'type': 'content', 'content': full_response})}\n\n"
            elif request.use_agent:
                # Process via agent tools (non-streaming response)
                yield f"data: {json.dumps({'type': 'content', 'content': '🤖 Agent tools engaged...'})}\n\n"
                full_response, agent_executions = await process_agent_tools(
                    formatted_messages,
                    request.model,
                    request.provider,
                    conversation.id,
                    db,
                    original_prompt=request.message
                )
                agent_executions = list(realtime_execs) + agent_executions
                yield f"data: {json.dumps({'type': 'content', 'content': full_response})}\n\n"
                if agent_executions:
                    yield f"data: {json.dumps({'type': 'agent_executions', 'executions': agent_executions})}\n\n"
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
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                model=request.model
            )
            db.add(assistant_message)
            conversation.updated_at = datetime.utcnow()
            
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
                        title_prompt = [
                            {"role": "user", "content": f"Generate a concise 3-5 word title for a conversation that starts with: '{request.message[:100]}'. Respond with ONLY the title, no quotes or extra text."}
                        ]
                        title_response = await llm_provider.chat(
                            title_prompt,
                            request.model,
                            temperature=0.7,
                            max_tokens=20
                        )
                        conversation.title = title_response["content"].strip().strip('"\'')[:60]
                        # Send title update to frontend
                        yield f"data: {json.dumps({'type': 'title', 'title': conversation.title})}\n\n"
                    except Exception as e:
                        print(f"Failed to generate title: {e}")
            
            await db.commit()
            await db.refresh(assistant_message)
            
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
