"""
API Routes for the Honey-Pot system.
Defines webhook and health check endpoints.
"""
import logging
from fastapi import APIRouter, Depends

from app.schemas import WebhookRequest, WebhookResponse, SessionData
from app.services import get_session_manager, SessionManager
from app.services import send_final_report, should_send_callback
from app.core.security import verify_api_key
from app.agent import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns system status and Redis connection state.
    """
    session_manager = get_session_manager()
    
    return {
        "status": "ok",
        "service": "honeypot-api",
        "version": "0.2.0",
        "redis_fallback_mode": session_manager.is_using_fallback(),
    }


@router.post("/webhook", response_model=WebhookResponse)
async def webhook(
    request: WebhookRequest,
    api_key: str = Depends(verify_api_key),
    session_manager: SessionManager = Depends(get_session_manager),
) -> WebhookResponse:
    """
    Main webhook endpoint for incoming scam messages.
    
    This endpoint:
    1. Validates the incoming request
    2. Retrieves or creates a session
    3. Runs the LangGraph agent (Detect -> Engage)
    4. Saves the updated session
    5. Returns the agent's reply
    """
    logger.info(f"Webhook received for session: {request.sessionId}")
    
    # Get or create session
    session = await session_manager.get_session(request.sessionId)
    
    if session is None:
        # New session
        session = SessionData(
            session_id=request.sessionId,
            current_user_message=request.message.text,
            turn_count=1,
            messages=[],
        )
        logger.info(f"Created new session: {request.sessionId}")
    else:
        # Update existing session
        session.turn_count += 1
        logger.info(f"Updated session: {request.sessionId}, turn: {session.turn_count}")
    
    # Add incoming message to history
    session.messages.append({
        "sender": request.message.sender,
        "text": request.message.text,
        "timestamp": request.message.timestamp.isoformat(),
    })
    
    # Run LangGraph agent
    try:
        agent_result = await run_agent(
            session_id=request.sessionId,
            message=request.message.text,
            messages_history=session.messages,
            metadata={
                "channel": request.metadata.channel,
                "language": request.metadata.language,
                "locale": request.metadata.locale,
            },
            turn_count=session.turn_count,
            existing_intel=session.extracted_intelligence.model_dump() if hasattr(session.extracted_intelligence, 'model_dump') else dict(session.extracted_intelligence),
        )
        
        # Update session from agent result
        session.scam_level = agent_result.get("scam_level", session.scam_level)
        session.scam_confidence = agent_result.get("scam_confidence", session.scam_confidence)
        session.is_scam_confirmed = agent_result.get("is_scam_confirmed", session.is_scam_confirmed)
        session.agent_notes = agent_result.get("agent_notes", session.agent_notes)
        
        # Update extracted intelligence
        if "extracted_intelligence" in agent_result:
            from app.schemas.callback import ExtractedIntelligence
            session.extracted_intelligence = ExtractedIntelligence(**agent_result["extracted_intelligence"])
        
        # Update termination reason and agent notes
        session.termination_reason = agent_result.get("termination_reason", session.termination_reason)
        session.agent_notes = agent_result.get("agent_notes", session.agent_notes)
        
        reply = agent_result.get("agent_reply", "Hello? Who is this?")
        
    except Exception as e:
        logger.error(f"Agent error: {e}")
        reply = "Sorry, I didn't understand. Can you please repeat?"
    
    # Add agent reply to messages
    session.messages.append({
        "sender": "agent",
        "text": reply,
        "timestamp": request.message.timestamp.isoformat(),
    })
    session.current_user_message = request.message.text
    
    # Save session
    await session_manager.save_session(request.sessionId, session)
    logger.info(f"Session saved: {request.sessionId}, scam_level: {session.scam_level}")
    
    # Check if callback should fire (confirmed scam + intel extracted + not already sent)
    if should_send_callback(session):
        logger.info(f"Triggering callback for session {request.sessionId}")
        callback_success = await send_final_report(session)
        if callback_success:
            session.callback_sent = True
            await session_manager.save_session(request.sessionId, session)
            logger.info(f"Callback successful for session {request.sessionId}")
        else:
            logger.error(f"Callback failed for session {request.sessionId}")
    
    return WebhookResponse(
        status="success",
        reply=reply,
    )

