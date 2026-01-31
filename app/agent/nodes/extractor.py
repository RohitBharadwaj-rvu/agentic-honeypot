"""
Extractor Node.
Extracts intelligence from scammer messages using regex and optional LLM reinforcement.
Only updates extracted_intelligence, never overwrites existing values.
"""
import re
import json
from typing import Dict, Any, List

from app.agent.state import AgentState
from app.agent.llm import call_llm


# Regex patterns
UPI_PATTERN = re.compile(r'\b[a-zA-Z0-9._-]+@[a-zA-Z]{2,}\b')
PHONE_PATTERN = re.compile(r'(?:\+91[\s-]?)?[6-9]\d{9}\b|\b\d{10}\b')
LINK_PATTERN = re.compile(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+')

# Email domains to exclude from UPI detection
EMAIL_DOMAINS = {'gmail', 'yahoo', 'hotmail', 'outlook', 'email', 'mail', 'proton'}


EXTRACT_SYSTEM_PROMPT = """Extract any suspicious data from the message.

Return JSON only:
{
    "upiIds": ["list of UPI IDs like abc@upi, xyz@paytm"],
    "phoneNumbers": ["list of 10-digit phone numbers"],
    "phishingLinks": ["list of URLs"]
}

If nothing found, return empty lists. JSON only, no explanation."""


def _extract_upi_ids(text: str) -> List[str]:
    """Extract UPI IDs from text using regex."""
    matches = UPI_PATTERN.findall(text)
    return [m for m in matches if m.split('@')[1].lower() not in EMAIL_DOMAINS]


def _extract_phone_numbers(text: str) -> List[str]:
    """Extract Indian phone numbers from text using regex."""
    matches = PHONE_PATTERN.findall(text)
    normalized = []
    for m in matches:
        clean = re.sub(r'[\s-]', '', m)
        if clean.startswith('+91'):
            clean = clean[3:]
        if len(clean) == 10:
            normalized.append(clean)
    return normalized


def _extract_links(text: str) -> List[str]:
    """Extract phishing links from text using regex."""
    return LINK_PATTERN.findall(text)


def _parse_llm_extraction(response: str) -> Dict[str, List[str]]:
    """Parse LLM JSON response for extracted data."""
    result = {"upiIds": [], "phoneNumbers": [], "phishingLinks": []}
    
    # Try to find JSON in response
    try:
        # Handle markdown code blocks
        if "```" in response:
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
        
        data = json.loads(response.strip())
        
        if isinstance(data.get("upiIds"), list):
            result["upiIds"] = [str(x) for x in data["upiIds"] if x]
        if isinstance(data.get("phoneNumbers"), list):
            result["phoneNumbers"] = [str(x) for x in data["phoneNumbers"] if x]
        if isinstance(data.get("phishingLinks"), list):
            result["phishingLinks"] = [str(x) for x in data["phishingLinks"] if x]
            
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return result


def extractor_node(state: AgentState) -> Dict[str, Any]:
    """
    Extractor node: Extracts intelligence using regex + optional LLM reinforcement.
    
    Only updates: extracted_intelligence
    Never overwrites existing values.
    
    Does NOT modify: scam_level, termination_reason
    """
    message = state["current_user_message"]
    messages = state.get("messages", [])
    
    # Step 1: Regex extraction (deterministic)
    regex_upi = _extract_upi_ids(message)
    regex_phones = _extract_phone_numbers(message)
    regex_links = _extract_links(message)
    
    # Step 2: LLM reinforcement (optional)
    llm_upi = []
    llm_phones = []
    llm_links = []
    
    # Build context for LLM
    context = f"Message to analyze: {message}"
    if messages:
        recent_texts = [m.get("text", "") for m in messages[-3:]]
        context += f"\n\nRecent context: {' | '.join(recent_texts)}"
    
    llm_messages = [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]
    
    llm_response = call_llm("extract", llm_messages)
    llm_data = _parse_llm_extraction(llm_response)
    
    llm_upi = llm_data["upiIds"]
    llm_phones = llm_data["phoneNumbers"]
    llm_links = llm_data["phishingLinks"]
    
    # Step 3: Merge all extractions
    all_upi = set(regex_upi) | set(llm_upi)
    all_phones = set(regex_phones) | set(llm_phones)
    all_links = set(regex_links) | set(llm_links)
    
    # Step 4: Merge with existing intelligence (never overwrite)
    existing = state.get("extracted_intelligence", {})
    existing_upi = set(existing.get("upiIds", []))
    existing_phones = set(existing.get("phoneNumbers", []))
    existing_links = set(existing.get("phishingLinks", []))
    existing_accounts = existing.get("bankAccounts", [])
    existing_keywords = existing.get("suspiciousKeywords", [])
    
    merged_intel = {
        "upiIds": list(existing_upi | all_upi),
        "phoneNumbers": list(existing_phones | all_phones),
        "phishingLinks": list(existing_links | all_links),
        "bankAccounts": existing_accounts,
        "suspiciousKeywords": existing_keywords,
    }
    
    return {
        "extracted_intelligence": merged_intel,
    }
