import sys
import os
import hashlib
from typing import Dict, Any, List

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.agent.nodes.persona import persona_node, HOOK_INSTRUCTION, STALL_INSTRUCTION, LEAK_INSTRUCTION
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

def verify_stalling():
    print("=" * 50)
    print("Verifying Randomized Stalling Strategy (Multiple Sessions)")
    print("=" * 50)
    
    for s_idx in range(1, 4):
        session_id = f"test-session-v{s_idx}"
        print(f"\n--- Session: {session_id} ---")
        for turn in range(1, 11):
            state: AgentState = {
                "session_id": session_id,
                "current_user_message": "Hello, send me your account details.",
                "messages": [],
                "scam_confidence": 0.8,
                "is_scam_confirmed": True,
                "scam_level": "suspected",
                "extracted_intelligence": {
                    "bankAccounts": [],
                    "upiIds": [],
                    "phishingLinks": [],
                    "phoneNumbers": [],
                    "suspiciousKeywords": [],
                },
                "turn_count": turn,
                "persona_name": "Ramesh",
                "persona_age": 67,
                "persona_location": "Pune",
                "persona_background": "Retired",
                "persona_trait": "Anxious",
                "fake_phone": "9876543210",
                "fake_upi": "ramesh@upi",
                "fake_bank_account": "123456789",
                "fake_ifsc": "SBIN0123",
                "channel": "SMS",
                "language": "en",
                "locale": "IN",
            }
            
            persona_node(state)
            
            # Check which instruction was used
            phase = "UNKNOWN"
            if HOOK_INSTRUCTION in last_system_prompt:
                phase = "HOOK"
            elif STALL_INSTRUCTION in last_system_prompt:
                phase = "STALL"
            elif LEAK_INSTRUCTION in last_system_prompt:
                phase = "LEAK"
                
            print(f"Turn {turn:2}: Phase = {phase}")

    print("\n" + "=" * 50)
    print("Verifying Text-Based Constraints")
    print("=" * 50)
    
    if "NEVER use verbal fillers" in last_system_prompt:
        print("SUCCESS: Text-based communication constraints found in system prompt.")
    else:
        print("FAILURE: Text-based communication constraints NOT found.")

if __name__ == "__main__":
    verify_stalling()
