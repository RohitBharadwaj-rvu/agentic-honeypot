
import asyncio
import logging
from app.agent.llm import call_llm, _call_with_retry, get_openai_client
from app.config import get_settings

# Configure logging to see switches
logging.basicConfig(level=logging.INFO)

async def verify_llms():
    settings = get_settings()
    print(f"Primary Model: {settings.MODEL_PRIMARY}")
    print(f"Fallback Model: {settings.MODEL_FALLBACK}")
    print(f"Base URL: {settings.NVIDIA_BASE_URL}")
    
    messages = [{"role": "user", "content": "Respond with 'P-OK'."}]
    
    print("\n--- Testing Primary Model ---")
    try:
        # Test primary directly
        client_primary = get_openai_client(settings.NVIDIA_API_KEY_PRIMARY)
        response = _call_with_retry(client_primary, settings.MODEL_PRIMARY, messages)
        print(f"Primary Response: {response}")
    except Exception as e:
        print(f"Primary failed: {e}")
    
    print("\n--- Testing Fallback Model ---")
    try:
        # Test fallback directly
        client_fallback = get_openai_client(settings.NVIDIA_API_KEY_FALLBACK)
        response_fallback = _call_with_retry(client_fallback, settings.MODEL_FALLBACK, [{"role": "user", "content": "Respond with 'F-OK'."}])
        print(f"Fallback Response: {response_fallback}")
    except Exception as e:
        print(f"Fallback failed: {e}")

if __name__ == "__main__":
    import sys
    # Ensure stdout is flushed immediately
    sys.stdout.reconfigure(line_buffering=True)
    asyncio.run(verify_llms())
