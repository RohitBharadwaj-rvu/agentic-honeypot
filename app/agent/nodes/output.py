"""
Output Node.
Returns the agent reply, updates turn_count, and sets termination_reason.
Final node in all graph paths.
"""
from typing import Dict, Any

from app.agent.state import AgentState


def output_node(state: AgentState) -> Dict[str, Any]:
    """
    Output node: Finalizes response, updates turn count, sets termination reason.
    
    Updates: turn_count, agent_reply, termination_reason
    
    Termination Rules:
    - extracted_intelligence contains UPI, phone, or bank account → "extracted_success"
    - turn_count >= 10 → "max_turns"
    
    Does NOT send callbacks or stop execution early.
    """
    turn_count = state.get("turn_count", 0)
    agent_reply = state.get("agent_reply", "")
    extracted_intel = state.get("extracted_intelligence", {})
    
    # Increment turn count
    new_turn_count = turn_count + 1
    
    # If no reply was generated (safe path), provide a default
    if not agent_reply:
        agent_reply = "Hello, I think you have the wrong number. Who is this?"
    
    # Determine termination reason
    termination_reason = None
    
    # Check for extracted success (UPI, phone, or bank account found)
    upi_ids = extracted_intel.get("upiIds", [])
    phone_numbers = extracted_intel.get("phoneNumbers", [])
    bank_accounts = extracted_intel.get("bankAccounts", [])
    
    if upi_ids or phone_numbers or bank_accounts:
        termination_reason = "extracted_success"
    elif new_turn_count >= 10:
        termination_reason = "max_turns"
    
    return {
        "turn_count": new_turn_count,
        "agent_reply": agent_reply,
        "termination_reason": termination_reason,
    }
