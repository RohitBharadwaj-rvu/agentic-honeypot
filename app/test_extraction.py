import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from app.agent.nodes.extractor import extractor_node

logging.basicConfig(level=logging.INFO)

def test_extraction():
    sample_input = (
        "Sir your SBI account is blocked. Please visit http://sbi-secure-kyc.com "
        "and update your KYC or your account will be closed. "
        "Send 1 Rs to verify-bank@upi to verify. Call 9876543210 for help."
    )
    
    print(f"\n--- SAMPLE INPUT ---\n{sample_input}\n")
    
    # Mock state
    state = {
        "current_user_message": sample_input,
        "messages": [],
        "extracted_intelligence": {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": [],
        },
        "agent_notes": "",
    }
    
    # Run extractor
    print("Running extractor_node (Sequential Regex + LLM)...")
    result = extractor_node(state)
    
    print("\n--- EXTRACTED JSON ---")
    print(json.dumps(result["extracted_intelligence"], indent=4))
    
    print("\n--- AGENT NOTES ---")
    print(result.get("agent_notes", "No notes."))
    
    print("\n--- SCAM CONFIRMED ---")
    print(result.get("is_scam_confirmed", False))

if __name__ == "__main__":
    test_extraction()
