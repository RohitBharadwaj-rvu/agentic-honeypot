"""
Output Node.
Returns the agent reply, updates turn_count, and sets termination_reason.
Final node in all graph paths.
"""
from typing import Dict, Any, List

from app.agent.state import AgentState


def _generate_agent_notes(state: AgentState) -> str:
    """
    Generate agent notes summarizing scam tactics observed.
    
    Returns:
        Summary string for agentNotes field in callback.
    """
    scam_level = state.get("scam_level", "safe")
    extracted = state.get("extracted_intelligence", {})
    
    if scam_level == "safe":
        return ""
    
    tactics: List[str] = []
    
    # Analyze extracted keywords for tactics
    keywords = extracted.get("suspiciousKeywords", [])
    if any(k in keywords for k in ["urgent", "immediately", "blocked", "suspend"]):
        tactics.append("urgency/fear tactics")
    if any(k in keywords for k in ["kyc", "verify", "update"]):
        tactics.append("KYC/verification pretext")
    if any(k in keywords for k in ["otp", "pin", "password"]):
        tactics.append("credential harvesting attempt")
    if any(k in keywords for k in ["lottery", "prize", "won", "cashback"]):
        tactics.append("prize/lottery fraud")
    
    # Check what was extracted
    if extracted.get("upiIds"):
        tactics.append("UPI ID collection")
    if extracted.get("bankAccounts"):
        tactics.append("bank account solicitation")
    if extracted.get("phishingLinks"):
        tactics.append("phishing link distribution")
    if extracted.get("phoneNumbers"):
        tactics.append("phone number provided for further contact")
    
    if not tactics:
        return f"Scam engagement completed. Level: {scam_level}."
    
    return f"Scammer used: {', '.join(tactics)}."


def output_node(state: AgentState) -> Dict[str, Any]:
    """
    Output node: Finalizes response, updates turn count, sets termination reason.
    
    Updates: turn_count, agent_reply, termination_reason, agent_notes
    
    Termination Rules (intel-based, no turn limit):
    - extracted_intelligence contains UPI, phone, bank account, or phishing link
      AND is_scam_confirmed == True → "extracted_success"
    
    Does NOT send callbacks or stop execution early.
    """
    turn_count = state.get("turn_count", 0)
    agent_reply = state.get("agent_reply", "")
    extracted_intel = state.get("extracted_intelligence", {})
    is_scam_confirmed = state.get("is_scam_confirmed", False)
    
    # Increment turn count
    new_turn_count = turn_count + 1
    
    # If no reply was generated (safe path), provide a default
    if not agent_reply:
         import random
         fallbacks = [
             "Hello, I think you have the wrong number. Who is this?",
             "Sorry, I don't know you. Are you from the bank?",
             "I think you messaged wrong number beta.",
             "Who is this? I am confused."
         ]
         agent_reply = random.choice(fallbacks)
    
    # Determine termination reason (intel-based, no turn limit)
    termination_reason = None
    
    # Check for extracted success - key intel found AND scam confirmed
    upi_ids = extracted_intel.get("upiIds", [])
    phone_numbers = extracted_intel.get("phoneNumbers", [])
    bank_accounts = extracted_intel.get("bankAccounts", [])
    phishing_links = extracted_intel.get("phishingLinks", [])
    
    key_intel_found = bool(upi_ids or phone_numbers or bank_accounts or phishing_links)
    
    if key_intel_found and is_scam_confirmed:
        termination_reason = "extracted_success"
    
    # Generate agent notes for callback
    agent_notes = _generate_agent_notes(state)
    
    return {
        "turn_count": new_turn_count,
        "agent_reply": agent_reply,
        "termination_reason": termination_reason,
        "agent_notes": agent_notes,
    }

