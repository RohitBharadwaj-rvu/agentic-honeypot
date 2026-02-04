"""
API Routes for the Honey-Pot system.
Defines webhook and health check endpoints.
"""
import logging
import json
import time
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import WebhookRequest, WebhookResponse, SessionData, MetadataInput
from app.services import get_session_manager, SessionManager
from app.services import send_final_report, should_send_callback
from app.core.security import verify_api_key
from app.agent import run_agent

logger = logging.getLogger(__name__)

# VERSION: Used to verify build status on Hugging Face
API_VERSION = "0.2.4-final-valuation"

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Does not touch Redis or agent logic.
    """
    return {
        "status": "ok",
        "service": "honeypot-api",
        "version": "0.2.2",
        "api_version": API_VERSION,
        "redis_fallback_mode": session_manager.is_using_fallback(),
    }


@router.api_route(
    "/honeypot/test",
    methods=["GET", "POST"],
    dependencies=[Depends(verify_api_key)],
)
async def honeypot_test():
    """
    Infrastructure test endpoint for hackathon reachability checks.
    Accepts GET/POST, ignores request body, and does not invoke the agent.
    """
    return {
        "status": "ok",
        "service": "agentic-honeypot",
        "message": "endpoint reachable",
    }


@router.post("/webhook")
@router.post("/webhook/")
async def webhook(
    raw_request: Request,
    api_key: str = Depends(verify_api_key),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Main webhook endpoint - hyper-flexible bypass version.
    """
    try:
        data = await raw_request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON body: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "reply": "Invalid JSON payload"})

    # --- GLOBAL SAFEGUARD: Wrap logic to ensure 200 OK always ---
    try:
        session_id = str(data.get("sessionId", data.get("session_id", data.get("id", "session-unknown"))))
        logger.info(f"[{API_VERSION}] Webhook received for session: {session_id}")
        
        # Extract message details
        message_data = data.get("message", data.get("msg", {}))
        if not isinstance(message_data, dict):
            msg_text = data.get("text", "")
            msg_sender = data.get("sender", "scammer")
        else:
            msg_text = message_data.get("text", data.get("text", ""))
            msg_sender = message_data.get("sender", data.get("sender", "scammer"))
        
        if not msg_text and not data.get("text"):
            msg_text = "Hello"

        # Extra check for metadata
        metadata_obj = data.get("metadata", data.get("meta", {}))
        if not isinstance(metadata_obj, dict):
            metadata_obj = {}

        # Get or create session
        session = await session_manager.get_session(session_id)
        
        if session is None:
            session = SessionData(
                session_id=session_id,
                current_user_message=msg_text,
                turn_count=1,
                messages=[],
            )
            logger.info(f"Created new session: {session_id}")
        else:
            session.turn_count += 1
            logger.info(f"Updated session: {session_id}, turn: {session.turn_count}")
        
        # Add incoming message to history
        from datetime import datetime
        session.messages.append({
            "sender": msg_sender,
            "text": msg_text,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Run LangGraph agent
        try:
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
            
            metadata_dict = {
                "channel": metadata_obj.get("channel", "SMS"),
                "language": metadata_obj.get("language", "English"),
                "locale": metadata_obj.get("locale", "IN"),
            }
            
            agent_result = await run_agent(
                session_id=session_id,
                message=msg_text,
                messages_history=session.messages,
                metadata=metadata_dict,
                turn_count=session.turn_count,
                existing_intel=session.extracted_intelligence.model_dump() if hasattr(session.extracted_intelligence, 'model_dump') else dict(session.extracted_intelligence),
                persona_details=persona_details,
            )
            
            # Update session from agent result
            session.scam_level = agent_result.get("scam_level", session.scam_level)
            session.is_scam_confirmed = agent_result.get("is_scam_confirmed", session.is_scam_confirmed)
            
            # Update extracted intelligence
            if "extracted_intelligence" in agent_result:
                from app.schemas.callback import ExtractedIntelligence
                session.extracted_intelligence = ExtractedIntelligence(**agent_result["extracted_intelligence"])
            
            session.termination_reason = agent_result.get("termination_reason", session.termination_reason)
            reply = agent_result.get("agent_reply", "Hello? How can I help you?")
            
        except Exception as e:
            logger.error(f"Agent error in webhook: {e}")
            reply = "Sorry, I am a bit confused today. Can you repeat?"
        
        # Add agent reply to messages
        from datetime import datetime
        session.messages.append({
            "sender": "agent",
            "text": reply,
            "timestamp": datetime.now().isoformat(),
        })
        session.current_user_message = msg_text
        
        # Save session
        await session_manager.save_session(session_id, session)
        
        # Trigger callback if needed
        if should_send_callback(session):
            await send_final_report(session)

    except Exception as e:
        logger.critical(f"UNCAUGHT WEBHOOK ERROR: {e}", exc_info=True)
        session_id = "unknown"
        reply = "Hello... my signal is weak. Can you say again?"

    # ULTIMATE CLEANUP: Remove newlines and extra spaces from reply to avoid JSON parsing issues
    clean_reply = " ".join(reply.split())
    
    content = {
        "status": "success",
        "reply": clean_reply,
    }
    logger.info(f"[{API_VERSION}] Sending ULTIMATE response for {session_id}: {content}")
    return JSONResponse(
        status_code=200,
        content=content,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


@router.post("/api/honeypot")
@router.post("/api/honeypot/")
async def api_honeypot(
    raw_request: Request,
    api_key: str = Depends(verify_api_key),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Hackathon evaluation endpoint.
    """
    return await webhook(raw_request, api_key=api_key, session_manager=session_manager)
