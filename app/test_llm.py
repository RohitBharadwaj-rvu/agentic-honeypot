import os
import sys
import logging
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from app.agent.llm import call_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test():
    print("Testing LLM connectivity...")
    messages = [{"role": "user", "content": "Say hello world"}]
    try:
        response = call_llm("persona", messages)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
