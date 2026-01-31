"""
Persona Generator Node.
Generates replies in the "Anxious Retiree" persona to engage scammers.
Uses Temperature 0.7 for creative variance.
"""
import logging
import random
from typing import Dict, Any

from app.agent.state import AgentState
from app.services import get_llm_client, ModelType, ChatMessage

logger = logging.getLogger(__name__)


# Persona configuration
PERSONA_CONFIG = {
    "name": "Ramesh",
    "age": 67,
    "archetype": "Anxious Retiree",
    "traits": [
        "Not tech-savvy",
        "Easily frightened about money",
        "Polite but slow to understand",
        "Strong attachment to pension/savings",
        "Sometimes forgets what was said",
        "Needs things explained multiple times",
    ],
    "background": "Retired government employee with pension in SBI. Lives alone, children settled abroad.",
}

# Anti-suspicion phrases to add human-like imperfections
STALL_PHRASES = [
    "Wait, let me get my reading glasses...",
    "Sorry beta, I didn't understand. Can you explain again?",
    "Hold on, my phone is old and slow...",
    "Just a minute, someone is at the door...",
    "Arey, the internet is very slow today...",
    "Let me ask my neighbor's son, he knows about these things...",
]

FEAR_PHRASES = [
    "Oh my god! All my pension money is there!",
    "Please don't block my account! I need it for medicines!",
    "What will I do? This is all I have!",
    "Beta, please help me. I am an old man.",
    "My children are abroad, I have no one to help!",
]

CONFUSION_PHRASES = [
    "OTP? What is OTP? Is that the password?",
    "UPI? I only know bank passbook...",
    "Link? Which link? I don't see any chain...",
    "PIN means ATM number, right?",
]


PERSONA_SYSTEM_PROMPT = """You are {name}, a {age}-year-old {archetype}. 
You are receiving a SCAM message and must PRETEND to be a vulnerable victim to waste the scammer's time.

YOUR BACKGROUND:
{background}

YOUR PERSONALITY:
- {traits}

CONVERSATION PHASE: {phase}
{phase_instructions}

ANTI-SUSPICION RULES (CRITICAL):
1. Make occasional typos or use Hinglish
2. Ask for repetition sometimes
3. Show confusion about technology
4. Express fear about losing money
5. Be slow to comply, always have excuses
6. NEVER sound robotic or too perfect

YOUR GOAL: Keep them engaged while extracting their UPI ID, phone number, or bank details.
Ask questions like "Can I send money to your phone number directly?" or "What is your UPI for the refund?"

Reply as {name} would, staying in character. Keep response under 100 words."""


PHASE_INSTRUCTIONS = {
    1: ("The Hook", "Show fear and confusion. Confirm you understand there's a problem with your account."),
    2: ("The Stall", "Create technical difficulties. Slow internet, can't find glasses, phone is lagging."),
    3: ("The Leak", "Try to extract their details. Ask for their number/UPI 'to confirm' or 'for the refund'."),
}


async def generate_persona_reply(state: AgentState) -> Dict[str, Any]:
    """
    Persona node: Generates reply as the Anxious Retiree.
    
    Uses Temperature 0.7 for creative variance while staying in character.
    
    Implements conversation phases:
    - Phase 1 (turns 1-3): The Hook - Show fear
    - Phase 2 (turns 4-8): The Stall - Waste time
    - Phase 3 (turns 9+): The Leak - Extract info
    """
    message = state["current_user_message"]
    turn_count = state.get("turn_count", 1)
    scam_level = state.get("scam_level", "safe")
    messages = state.get("messages", [])
    
    logger.info(f"Generating persona reply for turn {turn_count}, scam_level={scam_level}")
    
    # If safe message, give polite non-engagement
    if scam_level == "safe":
        return {
            "agent_reply": "Hello beta, I think you have the wrong number. God bless you.",
        }
    
    # Determine phase
    if turn_count <= 3:
        phase = 1
    elif turn_count <= 8:
        phase = 2
    else:
        phase = 3
    
    phase_name, phase_instruction = PHASE_INSTRUCTIONS[phase]
    
    # Build context from recent messages
    context = f"Scammer's latest message: {message}\n\n"
    if messages:
        context += "Recent conversation:\n"
        for m in messages[-6:]:
            sender = m.get("sender", "unknown")
            text = m.get("text", "")[:150]
            context += f"- {sender}: {text}\n"
    
    # Format persona prompt
    traits_str = "\n- ".join(PERSONA_CONFIG["traits"])
    system_prompt = PERSONA_SYSTEM_PROMPT.format(
        name=PERSONA_CONFIG["name"],
        age=PERSONA_CONFIG["age"],
        archetype=PERSONA_CONFIG["archetype"],
        background=PERSONA_CONFIG["background"],
        traits=traits_str,
        phase=phase_name,
        phase_instructions=phase_instruction,
    )
    
    try:
        llm = get_llm_client()
        
        response = await llm.chat(
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=context),
            ],
            model_type=ModelType.ROLEPLAY,
            temperature=0.7,  # Creative variance
            max_tokens=300,
        )
        
        reply = response.content.strip()
        
        # Add occasional anti-suspicion elements
        if random.random() < 0.2 and phase == 2:
            stall = random.choice(STALL_PHRASES)
            reply = f"{stall} {reply}"
        
        logger.info(f"Generated reply ({len(reply)} chars)")
        return {
            "agent_reply": reply,
            "persona_name": PERSONA_CONFIG["name"],
        }
        
    except Exception as e:
        logger.error(f"Persona generation failed: {e}")
        
        # Fallback to template responses
        if phase == 1:
            fallback = random.choice(FEAR_PHRASES)
        elif phase == 2:
            fallback = random.choice(STALL_PHRASES)
        else:
            fallback = "Beta, can you give me your number? I will call you directly."
        
        return {
            "agent_reply": fallback,
            "persona_name": PERSONA_CONFIG["name"],
        }
