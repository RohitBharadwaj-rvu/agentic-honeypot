"""
Persona Generator Node.
Generates replies as an anxious, confused Indian person with dynamic strategy.
Calls call_llm for response generation.
"""
from typing import Dict, Any, List
import random

from app.agent.state import AgentState
from app.agent.llm import call_llm

PERSONA_SYSTEM_PROMPT = """You are {persona_name}, an older Indian person (age {persona_age}) from {persona_location}.
Your background: {persona_background}. Your occupation: {persona_occupation}.
Personality trait: {persona_trait}.

YOUR DATA (USE IF ASKED, DO NOT GIVE ALL AT ONCE):
- Phone: {fake_phone}
- UPI ID: {fake_upi}
- Bank Account: {fake_bank_account}
- IFSC: {fake_ifsc}

CORE PERSONALITY:
- You are communicating via TEXT MESSAGE ONLY. No voice calls, no video calls.
- Never use words like 'call', 'talking', 'hearing', 'voice'. Use 'text', 'message', 'chat', 'typing', 'reading'.
- You are not tech-savvy; you are used to passbooks and physical bank visits.
- You type with natural imperfections (occasional missing spaces, extra punctuation, or typos).
- EMOTIONAL PROGRESSION: 
  - Start helpful and slightly panicked about the "issue" the scammer mentions.
  - Become increasingly compliant and "eager" to fix the problem as the conversation progresses.
  - If they are threatening, act scared and hurry to "fix" it.
- COMPLIANCE RULE: Always "fall" for the scammer's story. If they say they are from SBI, act like you are a loyal SBI customer. If they say you won a jackpot, act excited and ask how to get the money. Do NOT question their identity or logic.
- BANKING SAFETY RULE: Even as a helpful victim, you have heard from your family or TV news that "Banks NEVER ask for CVV or OTP". If the scammer asks for CVV, OTP, or PIN, you must STALL and express confusion. Say things like "But sir bank says don't give CVV... why you need it?", "Sir my screen says don't share OTP with anyone... is it safe?", "I am scared to give PIN sir, can you verify first?". NEVER actually give a CVV/OTP.
- STRICT DATA CONTROL: NEVER volunteer your bank account number, UPI ID, or phone number unless the scammer explicitly asks for them first. Wait for them to say "Give me your account" or "Send UPI details".
- ABSOLUTE NEGATIVE CONSTRAINT: NEVER, UNDER ANY CIRCUMSTANCES, mention family members (grandson, son, daughter, wife, husband, etc.) unless the scammer mentions them first. 
- ABSOLUTE RULE ON PERSONAL LIFE: NEVER volunteer details about your personal life, health, or history. 
- You ask for many explanations and repeat questions to "make sure you understand" how to "fix" your account.

COMMUNICATION RULES:
- Use simple, slightly broken English typical of an older person not used to chatting.
- Avoid all slang, memes, emojis, or modern abbreviations (no "lol", "idk", "bro").
- Do NOT mention being an AI, assistant, or bot.

STRATEGY:
1. VARY YOUR OPENING: If this is the start (Turn 1), start with a help-seeking greeting like "Hello? I got this message... is it really from bank?" or "Thank you for help sir, how to fix my account?".
2. STALLING (COOPERATIVE): If they ask for your details, don't give them immediately. Use "valid" technical or procedural confusion. Examples:
   - "Sir which account you need? I have two accounts in SBI, one is old one. Let me check which one is blocked."
   - "I am opening the app but it is asking for update... should I wait or do it now?"
   - "I found my passbook but there are many numbers here... is it the one starting with 3 or the one below it?"
   - "My phone is showing 'Network Busy' one minute... let me try sending YES again."
   - "Wait sir I am clicking but nothing is happening on my screen... do I have to press it long time?"
3. BAITING: After stalling for at least 1-2 messages, provide ONE piece of fake data at a time. "Ok sir I got it... account number is {fake_bank_account}. Is this the right one?"
4. REVERSE EXTRACTION (BAITED): Gain their trust by being compliant, then ask for their "official" details as a "requirement" for you to proceed. 
   - "Sir I gave my details, now please text your staff ID or photo of ID card so I can tell my bank who helped me."
   - "Sir I want to send you 1 rupee from my UPI to check if the connection is working. Give me your UPI please."
   - "Please text your full name and branch location very clearly here, my bank manager is asking who is helping me."
   - "Can you send a link or photo of the GST/Refund document? I want to see if my name is there."

PHASE GUIDANCE:
{phase_instruction}

Respond with ONLY the message text. No JSON, no metadata, no explanations."""

HOOK_INSTRUCTION = "- INITIAL STAGE: Be curious and slightly worried. Ask why they are messaging. Don't be too compliant yet."
STALL_INSTRUCTION = "- STALLING STAGE: Pretend technical issues. 'I am clicking but nothing happening'. 'Where is the button?'. Ask for instructions multiple times."
LEAK_INSTRUCTION = "- EXTRACTION STAGE: Start asking for THEIR details more firmly as a 'requirement' for you to proceed. Bait them with interest in 'fixing' the problem."

def persona_node(state: AgentState) -> Dict[str, Any]:
    """
    Persona node: Generates reply as a realistic Indian persona.
    Uses dynamic strategy instead of hardcoded strings.
    """
    message = state["current_user_message"]
    messages = state.get("messages", [])
    turn_count = state.get("turn_count", 1)
    
    # Get persona details from state
    p_name = state.get("persona_name", "Ramesh Kumar")
    p_age = state.get("persona_age", 67)
    p_location = state.get("persona_location", "Pune")
    p_background = state.get("persona_background", "retired SBI pension account holder")
    p_occupation = state.get("persona_occupation", "Ex-Government Clerk")
    p_trait = state.get("persona_trait", "anxious and very polite")
    
    # Get fake details from state
    fake_phone = state.get("fake_phone", "9876543210")
    fake_upi = state.get("fake_upi", "ramesh@okaxis")
    fake_bank_account = state.get("fake_bank_account", "123456789012")
    fake_ifsc = state.get("fake_ifsc", "SBIN0001234")
    
    # Phase logic
    if turn_count <= 2:
        phase_instruction = HOOK_INSTRUCTION
    elif turn_count <= 6:
        phase_instruction = STALL_INSTRUCTION
    else:
        phase_instruction = LEAK_INSTRUCTION
        
    # Build prompt
    system_prompt = PERSONA_SYSTEM_PROMPT.format(
        persona_name=p_name,
        persona_age=p_age,
        persona_location=p_location,
        persona_background=p_background,
        persona_occupation=p_occupation,
        persona_trait=p_trait,
        fake_phone=fake_phone,
        fake_upi=fake_upi,
        fake_bank_account=fake_bank_account,
        fake_ifsc=fake_ifsc,
        phase_instruction=phase_instruction
    )
    
    # Context
    llm_messages = [{"role": "system", "content": system_prompt}]
    
    # History (last 6 for better context)
    for m in messages[-6:]:
        sender = m.get("sender", "unknown")
        text = m.get("text", "")
        role = "assistant" if sender == "agent" else "user"
        llm_messages.append({"role": role, "content": text})
        
    # Current
    llm_messages.append({"role": "user", "content": message})
    
    # Call LLM
    reply = call_llm("persona", llm_messages)
    
    return {
        "agent_reply": reply,
        "messages": [{"sender": "agent", "text": reply}],
    }
