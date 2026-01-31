"""
Scam Detector Node.
Analyzes incoming messages to classify as safe/suspected/confirmed scam.
Uses keyword heuristics only (deterministic).
"""
from typing import Dict, Any

from app.agent.state import AgentState


# Keywords indicating confirmed scam (money/UPI/OTP requests)
CONFIRMED_KEYWORDS = [
    "send money",
    "transfer money",
    "pay now",
    "upi",
    "otp",
    "one time password",
    "send otp",
    "share otp",
    "enter otp",
    "pin",
    "send pin",
    "share pin",
    "cvv",
    "card number",
    "bank transfer",
    "paytm",
    "gpay",
    "phonepe",
    "google pay",
    "bhim",
]

# Keywords indicating suspected scam (urgency/KYC/blocked)
SUSPECTED_KEYWORDS = [
    "urgent",
    "urgently",
    "immediately",
    "kyc",
    "blocked",
    "suspended",
    "frozen",
    "verify",
    "verification",
    "expire",
    "expiring",
    "legal action",
    "police",
    "arrest",
    "deadline",
    "last chance",
    "account will be",
    "turant",
    "abhi",
    "jaldi",
]


def detector_node(state: AgentState) -> Dict[str, Any]:
    """
    Detector node: Analyzes message for scam indicators using keyword heuristics.
    
    Input: current_user_message (string)
    Output: updates scam_level and scam_confidence only
    
    Rules:
    - If message asks for money / UPI / OTP → confirmed (confidence: 0.9)
    - If message contains urgency / KYC / blocked → suspected (confidence: 0.6)
    - Else → safe (confidence: 0.1)
    """
    message = state["current_user_message"].lower()
    
    # Check for confirmed scam indicators
    for keyword in CONFIRMED_KEYWORDS:
        if keyword in message:
            return {
                "scam_level": "confirmed",
                "scam_confidence": 0.9,
            }
    
    # Check for suspected scam indicators
    for keyword in SUSPECTED_KEYWORDS:
        if keyword in message:
            return {
                "scam_level": "suspected",
                "scam_confidence": 0.6,
            }
    
    # Default: safe
    return {
        "scam_level": "safe",
        "scam_confidence": 0.1,
    }
