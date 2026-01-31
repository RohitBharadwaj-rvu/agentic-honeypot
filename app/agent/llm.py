"""
LLM Wrapper Module.
OpenRouter-compatible HTTP calls with retry logic and fallback handling.
"""
import logging
import random
import time
from typing import List, Dict, Optional

import httpx

from app.config import get_settings
from app.core.rules import SAFE_FALLBACK_RESPONSE, SCRIPT_FALLBACK_RESPONSES

logger = logging.getLogger(__name__)

# Track script fallback index for cycling
_script_fallback_index = 0


# Model routing configuration
MODEL_CONFIG = {
    "persona": {
        "primary": "tngtech/deepseek-r1t2-chimera:free",
        "fallback": "arcee-ai/trinity-mini:free",
    },
    "extract": {
        "primary": "tngtech/deepseek-r1t2-chimera:free",
        "fallback": "arcee-ai/trinity-mini:free",
    },
}

# Retry configuration
MAX_RETRIES = 2
BACKOFF_SECONDS = [1, 2]  # Exponential backoff: 1s, then 2s



def _make_request(
    client: httpx.Client,
    model: str,
    messages: List[Dict],
    api_key: str,
) -> Optional[str]:
    """
    Make a single HTTP request to OpenRouter.
    
    Returns response text or None on failure.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://honeypot.local",
        "X-Title": "Agentic Honeypot",
    }
    
    try:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60.0,
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        return None
        
    except Exception:
        return None


def _call_with_retry(
    client: httpx.Client,
    model: str,
    messages: List[Dict],
    api_key: str,
) -> Optional[str]:
    """
    Call model with retry logic for HTTP 429.
    
    Retries up to MAX_RETRIES times with exponential backoff.
    Returns response text or None if all retries fail.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://honeypot.local",
        "X-Title": "Agentic Honeypot",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300,
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            
            if response.status_code == 429:
                logger.warning(f"Rate limited (429) on model {model}, attempt {attempt + 1}")
                
                if attempt < MAX_RETRIES:
                    sleep_time = BACKOFF_SECONDS[attempt]
                    time.sleep(sleep_time)
                    continue
                else:
                    return None
            
            # Other error codes
            logger.warning(f"HTTP {response.status_code} from model {model}")
            return None
            
        except httpx.TimeoutException:
            logger.warning(f"Timeout on model {model}, attempt {attempt + 1}")
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS[attempt])
                continue
            return None
            
        except Exception as e:
            logger.warning(f"Error calling model {model}: {e}")
            return None
    
    return None


def call_llm(task: str, messages: List[Dict]) -> str:
    """
    Call LLM with task-based model routing.
    
    Args:
        task: "persona" or "extract"
        messages: List of message dicts with "role" and "content"
    
    Returns:
        Response text (plain string)
    
    Model Routing:
        - persona: primary → fallback → script fallback (cycling)
        - extract: primary → fallback → JSON fallback
    
    Handles HTTP 429 with retry + exponential backoff.
    Returns script fallback for persona tasks, safe fallback for extract.
    """
    global _script_fallback_index
    
    settings = get_settings()
    api_key = settings.OPENROUTER_API_KEY
    
    if not api_key:
        logger.error("OPENROUTER_API_KEY not configured")
        return SAFE_FALLBACK_RESPONSE
    
    # Get model configuration for task
    config = MODEL_CONFIG.get(task)
    if not config:
        logger.error(f"Unknown task: {task}")
        return SAFE_FALLBACK_RESPONSE
    
    primary_model = config["primary"]
    fallback_model = config["fallback"]
    
    with httpx.Client() as client:
        # Try primary model
        result = _call_with_retry(client, primary_model, messages, api_key)
        
        if result:
            return result.strip()
        
        # Try fallback model if available
        if fallback_model:
            logger.info(f"Switching to fallback model: {fallback_model}")
            result = _call_with_retry(client, fallback_model, messages, api_key)
            
            if result:
                return result.strip()
    
    # All attempts failed - use script fallback for persona tasks
    logger.error(f"All LLM attempts failed for task: {task}")
    
    if task == "persona" and SCRIPT_FALLBACK_RESPONSES:
        # Cycle through script fallback responses to maintain engagement
        response = SCRIPT_FALLBACK_RESPONSES[_script_fallback_index % len(SCRIPT_FALLBACK_RESPONSES)]
        _script_fallback_index += 1
        logger.info(f"Using script fallback response: {response}")
        return response
    
    return SAFE_FALLBACK_RESPONSE
