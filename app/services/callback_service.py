"""
Callback Service for reporting scam intelligence to GUVI evaluation endpoint.
Implements async HTTP client with retry logic and rate limiting awareness.
"""
import logging
import asyncio
from typing import Optional

import httpx

from app.config import get_settings
from app.schemas.session import SessionData
from app.schemas.callback import CallbackPayload

logger = logging.getLogger(__name__)


async def send_final_report(session: SessionData) -> bool:
    """
    Send final scam intelligence report to GUVI evaluation endpoint.
    
    This should ONLY be called when:
    1. scam_detected == True (confirmed scam)
    2. AI Agent has completed sufficient engagement
    3. Intelligence extraction is finished (termination_reason set)
    
    Args:
        session: SessionData with extracted intelligence
        
    Returns:
        True if callback was successful, False otherwise
    """
    settings = get_settings()
    
    # Build the callback payload per competition spec
    payload = CallbackPayload(
        sessionId=session.session_id,
        scamDetected=session.is_scam_confirmed,
        totalMessagesExchanged=len(session.messages),
        extractedIntelligence=session.extracted_intelligence,
        agentNotes=session.agent_notes or "Scam engagement completed.",
    )
    
    logger.info(f"Sending callback for session {session.session_id}")
    logger.debug(f"Callback payload: {payload.model_dump_json()}")
    
    # Retry logic with exponential backoff
    max_retries = settings.CALLBACK_MAX_RETRIES
    timeout = settings.CALLBACK_TIMEOUT
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    settings.CALLBACK_URL,
                    json=payload.model_dump(),
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code == 200:
                    logger.info(
                        f"Callback successful for session {session.session_id}. "
                        f"Status: {response.status_code}"
                    )
                    return True
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Rate limited. Waiting {wait_time}s before retry. "
                        f"Attempt {attempt + 1}/{max_retries}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Callback failed for session {session.session_id}. "
                        f"Status: {response.status_code}, Body: {response.text}"
                    )
                    # Don't retry on client errors (4xx except 429)
                    if 400 <= response.status_code < 500:
                        return False
                        
        except httpx.TimeoutException:
            logger.warning(
                f"Callback timeout for session {session.session_id}. "
                f"Attempt {attempt + 1}/{max_retries}"
            )
            await asyncio.sleep(2 ** attempt)
            
        except httpx.RequestError as e:
            logger.error(
                f"Callback request error for session {session.session_id}: {e}. "
                f"Attempt {attempt + 1}/{max_retries}"
            )
            await asyncio.sleep(2 ** attempt)
    
    logger.error(
        f"Callback failed after {max_retries} attempts for session {session.session_id}"
    )
    return False


def should_send_callback(session: SessionData) -> bool:
    """
    Check if callback should be sent for this session.
    
    Conditions:
    1. is_scam_confirmed == True
    2. termination_reason is set (intel extracted)
    3. callback_sent == False (not already sent)
    
    Returns:
        True if callback should be sent
    """
    if not session.is_scam_confirmed:
        logger.debug(f"Session {session.session_id}: Scam not confirmed, skipping callback")
        return False
        
    if not session.termination_reason:
        logger.debug(f"Session {session.session_id}: No termination reason, skipping callback")
        return False
        
    if session.callback_sent:
        logger.debug(f"Session {session.session_id}: Callback already sent, skipping")
        return False
    
    logger.info(
        f"Session {session.session_id}: Callback conditions met. "
        f"Reason: {session.termination_reason}"
    )
    return True
