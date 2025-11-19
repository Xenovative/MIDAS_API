"""Test models endpoint"""
import asyncio
from backend.llm_providers import llm_manager

async def test_models():
    try:
        providers = await llm_manager.get_available_providers()
        print(f"Success! Found {len(providers)} providers")
        for p in providers:
            print(f"  - {p['provider']}: {len(p['models'])} models")
        return providers
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_models())
    if result:
        print("\n✓ Test passed!")
    else:
        print("\n✗ Test failed!")
