from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.llm_providers import llm_manager
from backend.auth import get_user_or_guest
from backend.models import User

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


class SuggestionRequest(BaseModel):
    user_message: str
    assistant_message: str
    model: str = "gpt-4o-mini"
    provider: str = "openai"


@router.post("/generate")
async def generate_suggestions(
    request: SuggestionRequest,
    current_user: User = Depends(get_user_or_guest)
):
    """Generate contextual follow-up suggestions using AI"""
    
    # Create a prompt to generate suggestions
    system_prompt = """You are a helpful assistant that generates relevant follow-up questions.
Given a conversation between a user and an assistant, generate 5 natural, contextual follow-up questions that the user might want to ask next.

Rules:
1. Questions should be directly related to the conversation topic
2. Questions should help the user learn more or go deeper
3. Questions should be concise (max 10 words each)
4. Questions should be natural and conversational
5. Avoid generic questions - be specific to the topic discussed

Return ONLY the 5 questions, one per line, without numbering or bullets."""

    user_prompt = f"""User asked: {request.user_message}

Assistant responded: {request.assistant_message[:500]}...

Generate 5 relevant follow-up questions:"""

    try:
        # Get the provider
        provider = llm_manager.get_provider(request.provider)
        
        # Generate suggestions
        response = await provider.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=request.model,
            temperature=0.7,
            max_tokens=200
        )
        
        # Parse the response into a list of suggestions
        suggestions_text = response.get("content", "")
        suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
        
        # Ensure we have exactly 5 suggestions
        suggestions = suggestions[:5]
        while len(suggestions) < 5:
            suggestions.append("Tell me more about this")
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        # Fallback to generic suggestions if AI generation fails
        return {
            "suggestions": [
                "Can you explain this in simpler terms?",
                "Give me a practical example",
                "What are the best practices?",
                "What should I know next?",
                "How can I learn more about this?"
            ]
        }
