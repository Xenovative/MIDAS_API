"""
Test script for RAG functionality
"""
import asyncio
from backend.embeddings import embedding_provider
from backend.vector_store import vector_store
from backend.database import get_db, init_db
from backend.models import Bot, User
from sqlalchemy import select
import uuid


async def test_rag():
    """Test RAG components"""
    print("🧪 Testing RAG Functionality\n")
    
    # Initialize database
    await init_db()
    
    # Test 1: Embedding generation
    print("1️⃣ Testing embedding generation...")
    try:
        test_text = "This is a test document about artificial intelligence."
        embedding = await embedding_provider.embed_text(test_text)
        print(f"   ✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"   ❌ Embedding test failed: {e}")
        return
    
    # Test 2: Text chunking
    print("\n2️⃣ Testing text chunking...")
    try:
        long_text = """
        Artificial Intelligence (AI) is transforming the world. Machine learning is a subset of AI.
        Deep learning uses neural networks. Natural language processing helps computers understand text.
        Computer vision enables machines to interpret images. Robotics combines AI with physical systems.
        """ * 3  # Make it longer
        
        chunks = vector_store._split_text(long_text, chunk_size=100, chunk_overlap=20)
        print(f"   ✅ Split text into {len(chunks)} chunks")
        print(f"   First chunk: {chunks[0]['text'][:50]}...")
    except Exception as e:
        print(f"   ❌ Chunking test failed: {e}")
        return
    
    # Test 3: Document addition and search
    print("\n3️⃣ Testing document addition and search...")
    try:
        async for db in get_db():
            # Create a test bot
            test_bot_id = str(uuid.uuid4())
            
            # Add test document
            doc_id = await vector_store.add_document(
                db=db,
                bot_id=test_bot_id,
                filename="test_doc.txt",
                content="""
                Python is a high-level programming language. It is known for its simplicity and readability.
                Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.
                The Python standard library is extensive and includes modules for various tasks.
                Python is widely used in web development, data science, machine learning, and automation.
                """,
                chunk_size=150,
                chunk_overlap=30
            )
            print(f"   ✅ Added document: {doc_id}")
            
            # Search for relevant content
            results = await vector_store.search(
                db=db,
                bot_id=test_bot_id,
                query="What is Python used for?",
                top_k=3,
                similarity_threshold=0.5
            )
            
            print(f"   ✅ Found {len(results)} relevant chunks")
            for i, result in enumerate(results, 1):
                print(f"   [{i}] Similarity: {result['similarity']:.3f}")
                print(f"       Content: {result['content'][:80]}...")
            
            # Cleanup
            await vector_store.delete_document(db, doc_id)
            print(f"   ✅ Cleaned up test document")
            
            break
    except Exception as e:
        print(f"   ❌ Document test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ All RAG tests passed!")


if __name__ == "__main__":
    asyncio.run(test_rag())
