"""
LLM Wrapper Module.
NVIDIA API calls using OpenAI SDK with retry logic and fallback handling.
"""
import logging
import time
from typing import List, Dict, Optional

from openai import OpenAI

from app.config import get_settings
from app.core.rules import SAFE_FALLBACK_RESPONSE, SCRIPT_FALLBACK_RESPONSES

logger = logging.getLogger(__name__)

# Track script fallback index for cycling
_script_fallback_index = 0

# Persistent OpenAI client instance
_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or create a persistent OpenAI client instance."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=settings.NVIDIA_API_KEY,
        )
    return _client

# Retry configuration
MAX_RETRIES = 2
BACKOFF_SECONDS = [1, 2]  # Exponential backoff: 1s, then 2s


def _call_with_retry(
    client: OpenAI,
    model: str,
    messages: List[Dict],
) -> Optional[str]:
    """
    Call model with retry logic for errors.
    
    Retries up to MAX_RETRIES times with exponential backoff.
    Returns response text or None if all retries fail.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            # Use non-streaming for simplicity and reliability
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                top_p=0.9,
                max_tokens=300,
                stream=False,
            )
            
            if completion.choices and completion.choices[0].message:
                return completion.choices[0].message.content
            
            return None
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for rate limit errors
            if "429" in str(e) or "rate" in error_str:
                logger.warning(f"Rate limited on model {model}, attempt {attempt + 1}")
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS[attempt])
                    continue
                return None
            
            # Other errors
            logger.warning(f"Error calling model {model}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS[attempt])
                continue
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
    
    Handles errors with retry + exponential backoff.
    Returns script fallback for persona tasks, safe fallback for extract.
    """
    global _script_fallback_index
    settings = get_settings()
    api_key = settings.NVIDIA_API_KEY
    
    if not api_key:
        logger.error("NVIDIA_API_KEY not configured")
        return SAFE_FALLBACK_RESPONSE
    
    # Dynamic Model Configuration using Settings
    # This allows environment variables to override models (e.g. for benchmarking)
    model_config = {
        "persona": {
            "primary": settings.MODEL_PRIMARY,
            "fallback": settings.MODEL_FALLBACK,
        },
        "extract": {
            "primary": settings.MODEL_PRIMARY,
            "fallback": settings.MODEL_FALLBACK,
        },
    }
    
    # Get model configuration for task
    config = model_config.get(task)
    if not config:
        logger.error(f"Unknown task: {task}")
        return SAFE_FALLBACK_RESPONSE
    
    primary_model = config["primary"]
    fallback_model = config["fallback"]
    
    # Get persistent OpenAI client
    client = get_openai_client()
    
    # Try primary model
    result = _call_with_retry(client, primary_model, messages)
    
    if result:
        return result.strip()
    
    # Try fallback model if different
    if fallback_model and fallback_model != primary_model:
        logger.info(f"Switching to fallback model: {fallback_model}")
        result = _call_with_retry(client, fallback_model, messages)
        
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
