"""
Mock LLM Module.
Provides a mock LLM client for deterministic testing without hitting the real API.
"""
import json
from typing import List, Dict


# Pre-defined mock responses for different scenarios
MOCK_RESPONSES = {
    # Persona responses based on scam level patterns
    "safe_persona": "Hello, I think you have the wrong number. Who is this?",
    "suspected_persona": "Kya? What verification? I don't understand.",
    "confirmed_persona": "Ha theek hai, aap ko verification chahiye to batao.",
    
    # Extraction responses (empty extraction)
    "extract_empty": json.dumps({
        "upiIds": [],
        "phoneNumbers": [],
        "phishingLinks": [],
        "bankAccounts": []
    }),
    
    # Extraction responses with data
    "extract_upi": json.dumps({
        "upiIds": ["scammer@upi"],
        "phoneNumbers": [],
        "phishingLinks": [],
        "bankAccounts": []
    }),
    
    "extract_phone": json.dumps({
        "upiIds": [],
        "phoneNumbers": ["9876543210"],
        "phishingLinks": [],
        "bankAccounts": []
    }),
    
    "extract_bank": json.dumps({
        "upiIds": [],
        "phoneNumbers": [],
        "phishingLinks": [],
        "bankAccounts": ["12345678901234"]
    }),
}


def call_llm_mock(task: str, messages: List[Dict]) -> str:
    """
    Mock LLM function for deterministic testing.
    
    Analyzes the input messages to determine the appropriate mock response.
    
    Args:
        task: "persona" or "extract"
        messages: List of message dicts with "role" and "content"
    
    Returns:
        Appropriate mock response string.
    """
    # Get the last user message content for analysis
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "").lower()
            break
    
    if task == "extract":
        # Check for patterns in the message to return appropriate extraction
        if "@" in user_message and "upi" in user_message:
            return MOCK_RESPONSES["extract_upi"]
        elif any(char.isdigit() for char in user_message) and "phone" in user_message:
            return MOCK_RESPONSES["extract_phone"]
        elif "account" in user_message and any(char.isdigit() for char in user_message):
            return MOCK_RESPONSES["extract_bank"]
        else:
            return MOCK_RESPONSES["extract_empty"]
    
    elif task == "persona":
        # Check for scam indicators to return appropriate persona response
        confirmed_keywords = ["upi", "otp", "send money", "transfer", "paytm", "gpay"]
        suspected_keywords = ["urgent", "kyc", "blocked", "verify", "frozen"]
        
        for kw in confirmed_keywords:
            if kw in user_message:
                return MOCK_RESPONSES["confirmed_persona"]
        
        for kw in suspected_keywords:
            if kw in user_message:
                return MOCK_RESPONSES["suspected_persona"]
        
        return MOCK_RESPONSES["safe_persona"]
    
    # Default fallback
    return MOCK_RESPONSES["safe_persona"]
