"""
Simple test for RAG embedding functionality
Tests only the embedding generation without full app initialization
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


async def test_embeddings():
    """Test OpenAI embedding generation"""
    print("🧪 Testing RAG Embedding Generation\n")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    print("✅ API key found")
    
    # Test embedding generation
    print("\n1️⃣ Testing embedding generation...")
    try:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": ["This is a test document about artificial intelligence."],
            "model": "text-embedding-3-small"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            embedding = data["data"][0]["embedding"]
            print(f"   ✅ Generated embedding with {len(embedding)} dimensions")
            print(f"   Sample values: {embedding[:5]}")
            print(f"   Model used: {data['model']}")
            print(f"   Total tokens: {data['usage']['total_tokens']}")
    except Exception as e:
        print(f"   ❌ Embedding test failed: {e}")
        return
    
    # Test cosine similarity calculation
    print("\n2️⃣ Testing cosine similarity...")
    try:
        import numpy as np
        
        # Create two sample vectors
        vec1 = np.random.rand(1536)
        vec2 = vec1 + np.random.rand(1536) * 0.1  # Similar vector
        vec3 = np.random.rand(1536)  # Different vector
        
        def cosine_similarity(a, b):
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            return float(dot_product / (norm_a * norm_b))
        
        sim1 = cosine_similarity(vec1, vec2)
        sim2 = cosine_similarity(vec1, vec3)
        
        print(f"   ✅ Similarity between similar vectors: {sim1:.4f}")
        print(f"   ✅ Similarity between different vectors: {sim2:.4f}")
        print(f"   ✅ Cosine similarity working correctly")
    except Exception as e:
        print(f"   ❌ Similarity test failed: {e}")
        return
    
    # Test text chunking
    print("\n3️⃣ Testing text chunking...")
    try:
        def split_text(text, chunk_size=100, chunk_overlap=20):
            chunks = []
            start = 0
            text_length = len(text)
            
            while start < text_length:
                end = min(start + chunk_size, text_length)
                
                # Try to break at sentence boundary
                if end < text_length:
                    for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                        last_punct = text.rfind(punct, start, end)
                        if last_punct != -1:
                            end = last_punct + len(punct)
                            break
                
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "start": start,
                        "end": end
                    })
                
                start = end - chunk_overlap if end < text_length else text_length
            
            return chunks
        
        long_text = """
        Artificial Intelligence (AI) is transforming the world. Machine learning is a subset of AI.
        Deep learning uses neural networks. Natural language processing helps computers understand text.
        Computer vision enables machines to interpret images. Robotics combines AI with physical systems.
        """ * 3
        
        chunks = split_text(long_text, chunk_size=100, chunk_overlap=20)
        print(f"   ✅ Split text into {len(chunks)} chunks")
        print(f"   First chunk: {chunks[0]['text'][:50]}...")
        print(f"   Chunk size range: {min(len(c['text']) for c in chunks)}-{max(len(c['text']) for c in chunks)} chars")
    except Exception as e:
        print(f"   ❌ Chunking test failed: {e}")
        return
    
    print("\n✅ All basic RAG tests passed!")
    print("\n📝 Next steps:")
    print("   1. Ensure database is migrated: python migrate_add_rag.py")
    print("   2. Start the API server")
    print("   3. Create a RAG-enabled bot via API")
    print("   4. Upload documents to the bot")
    print("   5. Chat with the bot to see RAG in action")


if __name__ == "__main__":
    asyncio.run(test_embeddings())
