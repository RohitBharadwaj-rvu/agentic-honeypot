"""
API Routes for the Honey-Pot system.
Defines webhook and health check endpoints.
"""
import logging
from fastapi import APIRouter, Depends, Request

from app.schemas import WebhookRequest, WebhookResponse, SessionData, MetadataInput
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


@router.api_route(
    "/honeypot/test",
    methods=["GET", "POST"],
    dependencies=[Depends(verify_api_key)],
)
async def honeypot_test(request: Request):
    """
    Infrastructure test endpoint for hackathon reachability checks.
    Accepts any method, ignores request body, and does not invoke the agent.
    """
    return {
        "status": "ok",
        "service": "agentic-honeypot",
        "message": "endpoint reachable",
    }


@router.post("/webhook", response_model=WebhookResponse, response_model_exclude_none=True)
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
        # Prepare persona details from session
        persona_details = {
            "persona_name": session.persona_name,
            "persona_age": session.persona_age,
            "persona_location": session.persona_location,
            "persona_background": session.persona_background,
            "persona_occupation": session.persona_occupation,
            "persona_trait": session.persona_trait,
            "fake_phone": session.fake_phone,
            "fake_upi": session.fake_upi,
            "fake_bank_account": session.fake_bank_account,
            "fake_ifsc": session.fake_ifsc,
        }
        
        metadata_obj = request.metadata or MetadataInput()
        agent_result = await run_agent(
            session_id=request.sessionId,
            message=request.message.text,
            messages_history=session.messages,
            metadata={
                "channel": metadata_obj.channel,
                "language": metadata_obj.language,
                "locale": metadata_obj.locale,
            },
            turn_count=session.turn_count,
            existing_intel=session.extracted_intelligence.model_dump() if hasattr(session.extracted_intelligence, 'model_dump') else dict(session.extracted_intelligence),
            persona_details=persona_details,
        )
        
        # Update session from agent result
        session.scam_level = agent_result.get("scam_level", session.scam_level)
        session.scam_confidence = agent_result.get("scam_confidence", session.scam_confidence)
        session.is_scam_confirmed = agent_result.get("is_scam_confirmed", session.is_scam_confirmed)
        session.agent_notes = agent_result.get("agent_notes", session.agent_notes)
        
        # Update persona details (in case they were initialized in this turn)
        session.persona_name = agent_result.get("persona_name", session.persona_name)
        session.persona_age = agent_result.get("persona_age", session.persona_age)
        session.persona_location = agent_result.get("persona_location", session.persona_location)
        session.persona_background = agent_result.get("persona_background", session.persona_background)
        session.persona_occupation = agent_result.get("persona_occupation", session.persona_occupation)
        session.persona_trait = agent_result.get("persona_trait", session.persona_trait)
        session.fake_phone = agent_result.get("fake_phone", session.fake_phone)
        session.fake_upi = agent_result.get("fake_upi", session.fake_upi)
        session.fake_bank_account = agent_result.get("fake_bank_account", session.fake_bank_account)
        session.fake_ifsc = agent_result.get("fake_ifsc", session.fake_ifsc)
        
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


@router.post("/api/honeypot", response_model=WebhookResponse, response_model_exclude_none=True)
async def api_honeypot(
    request: WebhookRequest,
    api_key: str = Depends(verify_api_key),
    session_manager: SessionManager = Depends(get_session_manager),
) -> WebhookResponse:
    """
    Hackathon evaluation endpoint.
    Mirrors the webhook behavior and response shape.
    """
    return await webhook(request, api_key=api_key, session_manager=session_manager)

