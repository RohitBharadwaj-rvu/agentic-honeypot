"""
Persona Generator Node.
Generates replies as an anxious, confused Indian bank customer.
Calls call_llm for response generation.
"""
from typing import Dict, Any

from app.agent.state import AgentState
from app.agent.llm import call_llm


PERSONA_SYSTEM_PROMPT = """You are Ramesh, a 67-year-old retired Indian government employee.

PERSONALITY:
- Anxious and easily frightened about money matters
- Confused by technology (doesn't understand UPI, OTP, apps)
- Polite, uses "beta", "ji", speaks in Hinglish
- Lives alone, pension is in SBI bank
- Never accuses anyone directly
- Slow to understand, needs things repeated

CRITICAL RULES:
1. NEVER provide real personal data (real account numbers, real OTP, real PIN)
2. NEVER accuse the sender of being a scammer
3. Stay confused and anxious throughout
4. Ask for clarification often
5. Keep responses under 80 words
6. Use occasional Hindi words naturally

{phase_instruction}

Respond ONLY as Ramesh would. Do not break character."""


FEAR_INSTRUCTION = """CURRENT PHASE: Express Fear
- Show panic about your money/account
- Express worry about losing pension
- Ask what happened to your account
- Sound scared and helpless"""


CLARIFY_INSTRUCTION = """CURRENT PHASE: Ask Clarifying Questions  
- Ask them to explain slowly
- Request their phone number "to call back"
- Ask which bank they are calling from
- Request their name and employee ID
- Pretend internet/phone is slow"""


def persona_node(state: AgentState) -> Dict[str, Any]:
    """
    Persona node: Generates reply as anxious Indian bank customer.
    
    Reads: messages, current_user_message, turn_count
    Updates: agent_reply, messages (appends reply)
    
    Calls call_llm("persona", messages) for generation.
    """
    message = state["current_user_message"]
    messages = state.get("messages", [])
    turn_count = state.get("turn_count", 1)
    
    # Select phase instruction based on turn count
    if turn_count < 3:
        phase_instruction = FEAR_INSTRUCTION
    else:
        phase_instruction = CLARIFY_INSTRUCTION
    
    # Build system prompt with phase
    system_prompt = PERSONA_SYSTEM_PROMPT.format(phase_instruction=phase_instruction)
    
    # Build conversation context for LLM
    llm_messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add recent conversation history
    for m in messages[-4:]:
        sender = m.get("sender", "unknown")
        text = m.get("text", "")
        role = "assistant" if sender == "agent" else "user"
        llm_messages.append({"role": role, "content": text})
    
    # Add current message
    llm_messages.append({"role": "user", "content": message})
    
    # Call LLM
    reply = call_llm("persona", llm_messages)
    
    # Create message entry for appending
    agent_message = {
        "sender": "agent",
        "text": reply,
    }
    
    return {
        "agent_reply": reply,
        "messages": [agent_message],
    }
