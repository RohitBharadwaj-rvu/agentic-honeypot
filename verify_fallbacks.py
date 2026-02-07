import sys
import os
import random

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.agent.llm import call_llm
from app.core.rules import SCRIPT_FALLBACK_RESPONSES

def verify_fallbacks():
    print("=" * 50)
    print("Verifying Fallback Diversity and Randomization")
    print("=" * 50)
    
    # We will trigger fallbacks by mocking and checking the output
    # Since call_llm uses static responses if all LLMs fail, we just check call_llm with invalid task
    
    responses = []
    print("\nTriggering 10 fallbacks...")
    for _ in range(10):
        # Triggering fallback by invalid task
        resp = call_llm("persona", [{"role": "user", "content": "test"}])
        responses.append(resp)
        print(f"Fallback: {resp}")

    unique_responses = set(responses)
    print(f"\nUnique responses received: {len(unique_responses)} / {len(SCRIPT_FALLBACK_RESPONSES)}")
    
    if len(unique_responses) > 1:
        print("SUCCESS: Fallbacks are being cycled/randomized.")
    else:
        print("FAILURE: Fallbacks are repetitive.")

if __name__ == "__main__":
    # Force LLM failure by setting invalid keys
    import app.config as config
    settings = config.get_settings()
    settings.NVIDIA_API_KEY_PRIMARY = "invalid"
    settings.NVIDIA_API_KEY_FALLBACK = "invalid"
    
    verify_fallbacks()
