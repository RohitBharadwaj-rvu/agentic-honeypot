"""
Pytest fixtures for Agentic Honey-Pot tests.
Provides shared fixtures for regression, load, and golden dataset tests.
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, patch

import pytest

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture
def golden_transcripts() -> Dict[str, Any]:
    """Load golden transcripts dataset."""
    transcripts_file = DATA_DIR / "golden_transcripts.json"
    with open(transcripts_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_scam_message() -> str:
    """A confirmed scam message with UPI request."""
    return "Your KYC is pending! Send Rs 1 to verify@upi immediately or account will be blocked!"


@pytest.fixture
def sample_safe_message() -> str:
    """A harmless non-scam message."""
    return "Hi, how are you doing today?"


@pytest.fixture
def sample_metadata() -> Dict[str, str]:
    """Standard metadata for tests."""
    return {
        "channel": "SMS",
        "language": "en",
        "locale": "IN",
    }


@pytest.fixture
def mock_callback_tracker():
    """
    Track callback invocations for regression testing.
    Returns a dict with 'count' and 'payloads' to verify callback behavior.
    """
    tracker = {
        "count": 0,
        "payloads": [],
    }
    return tracker


@pytest.fixture
def mock_send_callback(mock_callback_tracker):
    """
    Mock the send_final_report function to track callback calls.
    Use this to verify callback fires exactly once.
    """
    async def _mock_send(session):
        mock_callback_tracker["count"] += 1
        mock_callback_tracker["payloads"].append({
            "sessionId": session.session_id,
            "scamDetected": session.is_scam_confirmed,
            "extractedIntelligence": session.extracted_intelligence,
            "totalMessagesExchanged": len(session.messages),
            "agentNotes": session.agent_notes or "",
        })
        return True
    
    return _mock_send


@pytest.fixture
def session_factory():
    """
    Factory to create SessionData objects for testing.
    """
    from app.schemas.session import SessionData
    
    def _create_session(
        session_id: str = "test-session-001",
        is_scam_confirmed: bool = False,
        termination_reason: str = None,
        callback_sent: bool = False,
        messages: List[Dict] = None,
        extracted_intelligence: Dict = None,
    ) -> SessionData:
        return SessionData(
            session_id=session_id,
            messages=messages or [],
            is_scam_confirmed=is_scam_confirmed,
            termination_reason=termination_reason,
            callback_sent=callback_sent,
            extracted_intelligence=extracted_intelligence or {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": [],
            },
        )
    
    return _create_session


@pytest.fixture
def mock_llm_responses():
    """
    Pre-defined LLM responses for deterministic testing.
    Maps input patterns to expected outputs.
    """
    return {
        "scam_detected": {
            "scam_level": "confirmed",
            "confidence": 0.95,
        },
        "safe_detected": {
            "scam_level": "safe",
            "confidence": 0.1,
        },
        "persona_reply": "Acha acha, please wait one minute, I need to find my glasses...",
    }


@pytest.fixture
def run_agent_with_mock():
    """
    Run agent workflow with mocked LLM for deterministic tests.
    """
    from app.agent.workflow import run_agent
    from app.agent.llm_mock import call_llm_mock
    
    async def _run(
        session_id: str,
        message: str,
        messages_history: List = None,
        metadata: Dict = None,
        turn_count: int = 1,
    ):
        # Patch the LLM to use mock
        with patch("app.agent.llm.call_llm", side_effect=call_llm_mock):
            return await run_agent(
                session_id=session_id,
                message=message,
                messages_history=messages_history or [],
                metadata=metadata or {"channel": "SMS", "language": "en", "locale": "IN"},
                turn_count=turn_count,
            )
    
    return _run
