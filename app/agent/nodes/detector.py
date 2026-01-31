"""
Scam Detector Node.
Analyzes incoming messages to classify as safe/suspected/confirmed scam.
Uses Temperature 0 for deterministic output.
"""
import logging
import re
from typing import Dict, Any

from app.agent.state import AgentState
from app.services import get_llm_client, ModelType, ChatMessage

logger = logging.getLogger(__name__)

# High-risk keywords for initial screening
SCAM_KEYWORDS = [
    # Urgency
    "urgent", "immediately", "blocked", "suspended", "verify", "expire",
    # Financial
    "kyc", "otp", "pin", "password", "bank", "account", "upi", "paytm", "gpay",
    # Threats
    "legal action", "police", "arrest", "blocked", "frozen",
    # Hindi/Hinglish
    "turant", "abhi", "band", "ruk", "jaldi",
]

# Patterns for extraction
UPI_PATTERN = r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9]+\b'
PHONE_PATTERN = r'\+?[0-9]{10,13}'
LINK_PATTERN = r'https?://[^\s]+'
ACCOUNT_PATTERN = r'\b[0-9]{9,18}\b'


def _keyword_score(text: str) -> float:
    """Calculate keyword-based scam score."""
    text_lower = text.lower()
    matches = sum(1 for kw in SCAM_KEYWORDS if kw in text_lower)
    # Normalize: 0 keywords = 0.0, 3+ keywords = 1.0
    return min(matches / 3.0, 1.0)


def _extract_patterns(text: str) -> Dict[str, list]:
    """Extract suspicious patterns from text."""
    return {
        "upiIds": re.findall(UPI_PATTERN, text),
        "phoneNumbers": re.findall(PHONE_PATTERN, text),
        "phishingLinks": re.findall(LINK_PATTERN, text),
        "bankAccounts": re.findall(ACCOUNT_PATTERN, text),
    }


DETECTOR_SYSTEM_PROMPT = """You are a scam detection system. Analyze the message and conversation for scam indicators.

SCAM INDICATORS:
- Urgency/fear tactics (account blocked, legal action)
- Requests for OTP, PIN, passwords
- Suspicious links or UPI IDs
- Impersonation of bank/government officials
- Too-good-to-be-true offers

RESPONSE FORMAT (JSON only):
{
    "scam_level": "safe" | "suspected" | "confirmed",
    "confidence": 0.0-1.0,
    "keywords_found": ["list", "of", "keywords"],
    "reasoning": "brief explanation"
}

Be conservative: only mark "confirmed" if there's clear evidence of scam intent."""


async def detect_scam(state: AgentState) -> Dict[str, Any]:
    """
    Detector node: Analyzes message for scam indicators.
    
    Uses:
    - Keyword matching (fast, deterministic)
    - LLM analysis (when keywords found)
    
    Temperature: 0 (deterministic)
    """
    message = state["current_user_message"]
    messages_history = state.get("messages", [])
    
    logger.info(f"Detecting scam in message: {message[:50]}...")
    
    # Step 1: Fast keyword screening
    keyword_score = _keyword_score(message)
    extracted = _extract_patterns(message)
    keywords_found = [kw for kw in SCAM_KEYWORDS if kw in message.lower()]
    
    # Update extracted intelligence
    current_intel = state.get("extracted_intelligence", {
        "bankAccounts": [],
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "suspiciousKeywords": [],
    })
    
    # Merge new extractions
    for key in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers"]:
        existing = set(current_intel.get(key, []))
        existing.update(extracted.get(key, []))
        current_intel[key] = list(existing)
    
    current_intel["suspiciousKeywords"] = list(
        set(current_intel.get("suspiciousKeywords", [])) | set(keywords_found)
    )
    
    # Step 2: Determine scam level
    # If explicit scam indicators found, mark as confirmed
    if extracted["upiIds"] or extracted["phishingLinks"]:
        scam_level = "confirmed"
        confidence = 0.95
        is_confirmed = True
    elif keyword_score >= 0.7:
        scam_level = "confirmed"
        confidence = 0.85
        is_confirmed = True
    elif keyword_score >= 0.3:
        scam_level = "suspected"
        confidence = 0.5 + keyword_score * 0.3
        is_confirmed = False
    else:
        # Use LLM for ambiguous cases
        try:
            llm = get_llm_client()
            
            # Build context
            context = f"Current message: {message}\n"
            if messages_history:
                recent = messages_history[-5:]  # Last 5 messages
                context += "Recent history:\n"
                for m in recent:
                    context += f"- {m.get('sender', 'unknown')}: {m.get('text', '')[:100]}\n"
            
            response = await llm.chat(
                messages=[
                    ChatMessage(role="system", content=DETECTOR_SYSTEM_PROMPT),
                    ChatMessage(role="user", content=context),
                ],
                model_type=ModelType.REASONING,
                temperature=0.0,  # Deterministic
                max_tokens=200,
            )
            
            # Parse response (simple extraction)
            content = response.content.lower()
            if '"confirmed"' in content:
                scam_level = "confirmed"
                confidence = 0.8
                is_confirmed = True
            elif '"suspected"' in content:
                scam_level = "suspected"
                confidence = 0.5
                is_confirmed = False
            else:
                scam_level = "safe"
                confidence = 0.2
                is_confirmed = False
                
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            # Fallback to keyword-based
            scam_level = "suspected" if keyword_score > 0 else "safe"
            confidence = keyword_score
            is_confirmed = False
    
    logger.info(f"Detection result: level={scam_level}, confidence={confidence:.2f}")
    
    return {
        "scam_level": scam_level,
        "scam_confidence": confidence,
        "is_scam_confirmed": is_confirmed,
        "extracted_intelligence": current_intel,
        "agent_notes": f"Detected {len(keywords_found)} keywords. Level: {scam_level}",
    }
