import sys
import os
from typing import Dict, Any, List

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.agent.nodes.persona import persona_node
from app.agent.state import AgentState

# Mock call_llm to capture the system prompt
last_system_prompt = ""

def mock_call_llm(task: str, messages: List[Dict]) -> str:
    global last_system_prompt
    for m in messages:
        if m["role"] == "system":
            last_system_prompt = m["content"]
    return "Mocked response from agent."

# Monkeypatch call_llm in persona module
import app.agent.nodes.persona as persona_module
persona_module.call_llm = mock_call_llm

def verify_language():
    print("=" * 50)
    print("Verifying Language Consistency")
    print("=" * 50)
    
    test_cases = [
        {"lang": "en", "expected": "English primarily"},
        {"lang": "hi", "expected": "Hindi only"},
    ]
    
    for case in test_cases:
        state: AgentState = {
            "session_id": "test-lang",
            "current_user_message": "Hello",
            "messages": [],
            "language": case["lang"],
            "turn_count": 1,
            # include other required state fields if needed
        }
        
        persona_node(state)
        
        print(f"\nLanguage State: {case['lang']}")
        if case["expected"] in last_system_prompt:
            print(f"SUCCESS: Found expected instruction '{case['expected']}' in system prompt.")
        else:
            print(f"FAILURE: Instruction '{case['expected']}' NOT found in system prompt.")

if __name__ == "__main__":
    verify_language()
