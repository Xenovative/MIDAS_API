"""
Deep Research RAG - Uses OpenAI reasoning models for thorough document analysis
Provides comprehensive, well-reasoned answers from documents
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.llm_providers import llm_manager


class DeepResearchRAG:
    """Enhanced RAG using OpenAI's reasoning capabilities for deep analysis"""
    
    @staticmethod
    async def deep_research_query(
        query: str,
        retrieved_chunks: List[Dict],
        reasoning_model: str = "o1",
        max_reasoning_tokens: int = 10000
    ) -> Dict:
        """
        Perform deep research on retrieved chunks using advanced reasoning model
        
        Args:
            query: User's question
            retrieved_chunks: Chunks from vector search
            reasoning_model: OpenAI model - tries in order:
                - "o1" (o1-pro, o1-preview, o1-mini)
                - "o3" (o3-mini)
                - "gpt-4o" (fallback)
            max_reasoning_tokens: Max tokens for response
        
        Returns:
            Dictionary with answer and reasoning process
        """
        if not retrieved_chunks:
            return {
                "answer": "No relevant information found in documents.",
                "reasoning": None,
                "sources": []
            }
        
        # Prepare document context
        context = DeepResearchRAG._prepare_research_context(retrieved_chunks)
        
        # Build research prompt
        num_sections = len(retrieved_chunks)
        research_prompt = f"""You are a research assistant analyzing documents to answer questions thoroughly.

QUESTION:
{query}

AVAILABLE DOCUMENTS:
You have access to {num_sections} substantial sections from the uploaded document(s).
This represents comprehensive coverage of the relevant content.

{context}

IMPORTANT INSTRUCTIONS:
1. You have SUBSTANTIAL portions of the complete document(s) - NOT just snippets
2. The {num_sections} sections above provide comprehensive context
3. Carefully read and analyze ALL provided sections
4. Identify key information relevant to the question
5. Consider multiple perspectives and interpretations
6. Synthesize information across all sections
7. Provide a comprehensive, well-reasoned answer
8. Cite specific sections when making claims
9. DO NOT claim you only have "limited access" or "snippets"
10. You have enough context to provide thorough, authoritative answers

Please provide a thorough, research-quality answer based on the comprehensive document context provided."""

        try:
            # Use OpenAI reasoning model for deep analysis
            provider = llm_manager.get_provider("openai")
            
            messages = [
                {
                    "role": "user",
                    "content": research_prompt
                }
            ]
            
            # Try models in order of preference with automatic fallback
            models_to_try = DeepResearchRAG._get_model_fallback_chain(reasoning_model)
            
            last_error = None
            for model_name in models_to_try:
                try:
                    print(f"🔬 Attempting deep research with {model_name}...")
                    print(f"📊 Analyzing {len(retrieved_chunks)} document sections")
                    
                    # Adjust parameters based on model type
                    is_reasoning_model = model_name.startswith(('o1', 'o3'))
                    
                    # For reasoning models, use reasoning_effort parameter for deep research
                    # For GPT-4 models, use lower temperature for focused analysis
                    if is_reasoning_model:
                        # O1/O3 models - minimal parameters only
                        # These models inherently do deep reasoning with fixed settings
                        print(f"   → Using O1/O3 reasoning model (fixed settings)")
                        print(f"   → O1 models control their own token usage")
                        
                        # Call O1/O3 model with minimal parameters
                        response = await provider.chat_with_reasoning(
                            messages=messages,
                            model=model_name
                        )
                    else:
                        # GPT-4 models accept temperature
                        print(f"   → Using GPT-4 parameters (temperature: 0.3)")
                        print(f"   → max_tokens: {max_reasoning_tokens}")
                        response = await provider.chat(
                            messages=messages,
                            model=model_name,
                            temperature=0.3,
                            max_tokens=max_reasoning_tokens
                        )
                    
                    answer = response.get("content", "")
                    reasoning_tokens = response.get("usage", {}).get("completion_tokens", 0)
                    
                    print(f"✅ Deep research complete with {model_name} ({reasoning_tokens} tokens)")
                    
                    # Extract sources
                    sources = DeepResearchRAG._extract_sources(retrieved_chunks)
                    
                    return {
                        "answer": answer,
                        "reasoning_tokens": reasoning_tokens,
                        "sources": sources,
                        "model": model_name
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    
                    print(f"⚠️  Error with {model_name}: {error_msg}")
                    
                    # Check if it's a model availability error (try next model)
                    if any(phrase in error_msg.lower() for phrase in [
                        "does not exist",
                        "model_not_found", 
                        "not found",
                        "invalid model",
                        "not supported",
                        "not available"
                    ]):
                        print(f"   → Model not available, trying next model...")
                        continue
                    else:
                        # Other error (API error, rate limit, etc.) - don't try more models
                        print(f"   → Non-availability error, stopping fallback chain")
                        print(f"   → Full error: {e}")
                        raise
            
            # All models failed
            print(f"❌ All models failed. Last error: {last_error}")
            return {
                "answer": f"Deep research unavailable. All models failed. Last error: {last_error}",
                "reasoning": None,
                "sources": []
            }
            
        except Exception as e:
            print(f"❌ Deep research error: {e}")
            return {
                "answer": f"Error during deep research: {str(e)}",
                "reasoning": None,
                "sources": []
            }
    
    @staticmethod
    def _get_model_fallback_chain(preferred_model: str) -> List[str]:
        """
        Get fallback chain of models to try
        
        Args:
            preferred_model: User's preferred model or model family
        
        Returns:
            List of model names to try in order
        """
        # Define model families and their fallback chains
        # Simplified: Try standard models first, then fallback to GPT-4o
        fallback_chains = {
            "o1": ["o1-preview", "o1-mini", "gpt-4o"],
            "o1-pro": ["o1-pro", "o1-preview", "o1-mini", "gpt-4o"],
            "o1-preview": ["o1-preview", "o1-mini", "gpt-4o"],
            "o1-mini": ["o1-mini", "gpt-4o"],
            "o3": ["o3-mini", "o1-mini", "gpt-4o"],
            "o3-mini": ["o3-mini", "o1-mini", "gpt-4o"],
            "gpt-4o": ["gpt-4o"],
            "gpt-4-turbo": ["gpt-4-turbo", "gpt-4o"],
            "gpt-4o-mini": ["gpt-4o-mini", "gpt-4o"]
        }
        
        # Get the fallback chain for the preferred model
        chain = fallback_chains.get(preferred_model, ["gpt-4o"])
        
        print(f"🔄 Model fallback chain: {' → '.join(chain)}")
        return chain
    
    @staticmethod
    def _prepare_research_context(chunks: List[Dict]) -> str:
        """Prepare document context for research"""
        lines = []
        
        # Group by document
        from collections import defaultdict
        docs = defaultdict(list)
        
        for chunk in chunks:
            docs[chunk['filename']].append(chunk)
        
        # Sort chunks within each document
        for doc_name in docs:
            docs[doc_name].sort(key=lambda x: x.get('chunk_index', 0))
        
        # Format context
        for doc_name, doc_chunks in docs.items():
            lines.append(f"\n{'='*60}")
            lines.append(f"DOCUMENT: {doc_name}")
            lines.append(f"{'='*60}\n")
            
            for idx, chunk in enumerate(doc_chunks, 1):
                relevance = int(chunk['similarity'] * 100)
                chunk_num = chunk.get('chunk_index', 0)
                
                lines.append(f"[Section {idx} | Chunk #{chunk_num} | Relevance: {relevance}%]")
                lines.append(chunk['content'])
                lines.append("")  # Blank line
        
        return "\n".join(lines)
    
    @staticmethod
    def _extract_sources(chunks: List[Dict]) -> List[Dict]:
        """Extract source information from chunks"""
        sources = []
        seen = set()
        
        for chunk in chunks:
            doc_id = chunk.get('document_id')
            if doc_id not in seen:
                sources.append({
                    'document_id': doc_id,
                    'filename': chunk['filename'],
                    'relevance': chunk['similarity']
                })
                seen.add(doc_id)
        
        return sources
    
    @staticmethod
    def format_research_response(research_result: Dict) -> str:
        """Format research result for LLM context"""
        lines = []
        
        lines.append("=== DEEP RESEARCH ANALYSIS ===\n")
        
        if research_result.get('model'):
            lines.append(f"Analysis performed by: {research_result['model']}")
            if research_result.get('reasoning_tokens'):
                lines.append(f"Reasoning tokens used: {research_result['reasoning_tokens']:,}")
        
        lines.append("\n" + "="*60)
        lines.append("RESEARCH FINDINGS:")
        lines.append("="*60 + "\n")
        
        lines.append(research_result.get('answer', 'No answer available'))
        
        if research_result.get('sources'):
            lines.append("\n" + "="*60)
            lines.append("SOURCES ANALYZED:")
            lines.append("="*60)
            for source in research_result['sources']:
                relevance = int(source['relevance'] * 100)
                lines.append(f"• {source['filename']} (Relevance: {relevance}%)")
        
        lines.append("\n=== END OF RESEARCH ANALYSIS ===")
        
        return "\n".join(lines)


class HybridRAG:
    """Hybrid approach: Fast retrieval + optional deep research"""
    
    @staticmethod
    async def query(
        query: str,
        retrieved_chunks: List[Dict],
        use_deep_research: bool = False,
        complexity_threshold: int = 50  # Auto-enable for complex queries
    ) -> str:
        """
        Query with hybrid approach
        
        Args:
            query: User's question
            retrieved_chunks: Retrieved chunks
            use_deep_research: Force deep research
            complexity_threshold: Auto-enable threshold (query length)
        
        Returns:
            Formatted context string
        """
        # Determine if deep research is needed
        query_length = len(query.split())
        
        # Check for complexity keywords
        complexity_keywords = [
            'analyze', 'compare', 'explain', 'why', 'how',
            'relationship', 'difference', 'similarity',
            'comprehensive', 'detailed', 'thorough'
        ]
        found_keywords = [kw for kw in complexity_keywords if kw in query.lower()]
        
        is_complex = (
            query_length > complexity_threshold or
            len(found_keywords) > 0
        )
        
        should_use_deep = use_deep_research or is_complex
        
        # Detailed logging
        print(f"\n{'='*60}")
        print(f"🔍 RAG Query Analysis:")
        print(f"  Query: {query[:100]}...")
        print(f"  Query length: {query_length} words")
        print(f"  Complexity threshold: {complexity_threshold} words")
        print(f"  Keywords found: {found_keywords if found_keywords else 'None'}")
        print(f"  Is complex: {is_complex}")
        print(f"  Force deep research: {use_deep_research}")
        print(f"  Should use deep: {should_use_deep}")
        print(f"  Retrieved chunks: {len(retrieved_chunks)}")
        print(f"{'='*60}\n")
        
        if should_use_deep and len(retrieved_chunks) > 0:
            print(f"🔬 USING DEEP RESEARCH")
            research_result = await DeepResearchRAG.deep_research_query(
                query=query,
                retrieved_chunks=retrieved_chunks,
                reasoning_model="o1"  # Tries o1-pro → o1-preview → o1-mini → gpt-4o
            )
            return DeepResearchRAG.format_research_response(research_result)
        else:
            print(f"⚡ USING FAST RETRIEVAL (reading flow)")
            # Use reading flow for simple queries
            from backend.reading_flow_rag import reading_flow_rag
            return reading_flow_rag.format_reading_context(retrieved_chunks)


# Global instances
deep_research_rag = DeepResearchRAG()
hybrid_rag = HybridRAG()
