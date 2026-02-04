
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
    
    messages = [{"role": "user", "content": "Hello, respond with exactly 'P-OK' if you are the primary model."}]
    
    print("\n--- Testing Primary Model (Kimi) ---")
    response = call_llm("persona", messages)
    print(f"Primary Response: {response}")
    
    print("\n--- Testing Fallback Model (Mistral) Direct ---")
    # Test fallback directly using its key and model
    client_fallback = get_openai_client(settings.NVIDIA_API_KEY_FALLBACK)
    response_fallback = _call_with_retry(client_fallback, settings.MODEL_FALLBACK, [{"role": "user", "content": "Respond with 'F-OK'."}])
    print(f"Fallback Response: {response_fallback}")

if __name__ == "__main__":
    asyncio.run(verify_llms())
