
import os
import sys
from openai import OpenAI
from app.config import get_settings

def test_llm_connection():
    try:
        settings = get_settings()
        api_key = settings.NVIDIA_API_KEY
        
        print(f"Checking configuration...")
        print(f"API Key present: {'Yes' if api_key else 'No'}")
        print(f"Base URL: {settings.NVIDIA_BASE_URL}")
        print(f"Model: {settings.MODEL_PRIMARY}")
        
        if not api_key:
            print("❌ ERROR: NVIDIA_API_KEY is missing via .env or environment variable.")
            return

        client = OpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=api_key,
        )

        print("\nSending test request to LLM...")
        completion = client.chat.completions.create(
            model=settings.MODEL_PRIMARY,
            messages=[{"role": "user", "content": "Say 'Connection successful' if you can hear me."}],
            max_tokens=20,
        )

        response = completion.choices[0].message.content
        print(f"[SUCCESS] Response: {response}")

    except Exception as e:
        print(f"[FAILED] CONNECT ERROR: {e}")

if __name__ == "__main__":
    test_llm_connection()
