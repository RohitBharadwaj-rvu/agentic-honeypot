"""
Load Tests for Upstash Free Tier Compliance.
Tests session size limits and concurrent session handling.
"""
import sys
import json
import asyncio
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.workflow import run_agent
from app.services.session_manager import SessionManager
from app.schemas.session import SessionData


class TestSessionSize:
    """Tests for session JSON size limits (Upstash free tier: 256MB total)."""
    
    def test_empty_session_size(self, session_factory):
        """Verify empty session serializes to reasonable size."""
        session = session_factory(session_id="size-001")
        
        # Serialize to JSON
        json_str = session.model_dump_json()
        size_bytes = len(json_str.encode("utf-8"))
        
        # Empty session should be < 500 bytes
        assert size_bytes < 500, f"Empty session too large: {size_bytes} bytes"
    
    def test_session_with_max_messages(self, session_factory):
        """
        Verify session with 10 messages (max turns) stays under 1KB.
        Competition allows ~10 turns, so total messages ≈ 20 (scammer + agent).
        """
        # Simulate 20 messages (10 exchanges)
        messages = []
        for i in range(20):
            sender = "scammer" if i % 2 == 0 else "agent"
            # Average message ~100 chars
            text = f"This is test message number {i} with some padding text to simulate real content."
            messages.append({"sender": sender, "text": text})
        
        session = session_factory(
            session_id="size-002",
            messages=messages,
            is_scam_confirmed=True,
            termination_reason="max_turns",
            extracted_intelligence={
                "bankAccounts": ["12345678901234"],
                "upiIds": ["scammer@upi", "another@paytm"],
                "phishingLinks": ["fake-bank.com", "kyc-update.tk"],
                "phoneNumbers": ["9876543210", "8765432109"],
                "suspiciousKeywords": ["urgent", "blocked", "verify", "kyc", "otp"],
            },
        )
        
        json_str = session.model_dump_json()
        size_bytes = len(json_str.encode("utf-8"))
        
        # Full session should stay under 3KB for free tier efficiency
        # 256MB / 3KB ≈ 85,000 sessions - plenty for competition
        assert size_bytes < 3072, f"Session too large: {size_bytes} bytes (limit: 3072)"
        print(f"Session with 20 messages: {size_bytes} bytes")

    def test_realistic_scam_session_size(self, session_factory):
        """Test with realistic scam conversation content."""
        messages = [
            {"sender": "scammer", "text": "Dear customer, your account is blocked due to KYC expiry!"},
            {"sender": "agent", "text": "Oh my god! What should I do? I am very worried now."},
            {"sender": "scammer", "text": "Send Rs 1 to verify@paytm for verification immediately!"},
            {"sender": "agent", "text": "Wait wait, let me find my phone. Where did I keep it..."},
            {"sender": "scammer", "text": "Hurry up! Your account will be permanently suspended!"},
            {"sender": "agent", "text": "Please sir, I am an old person. Can you come to my house?"},
        ]
        
        session = session_factory(
            session_id="realistic-001",
            messages=messages,
            is_scam_confirmed=True,
            termination_reason="extracted_success",
            extracted_intelligence={
                "upiIds": ["verify@paytm"],
                "suspiciousKeywords": ["blocked", "kyc", "suspended", "immediately"],
                "bankAccounts": [],
                "phoneNumbers": [],
                "phishingLinks": [],
            },
        )
        
        json_str = session.model_dump_json()
        size_bytes = len(json_str.encode("utf-8"))
        
        assert size_bytes < 1024, f"Realistic session too large: {size_bytes} bytes"
        print(f"Realistic scam session: {size_bytes} bytes")


class TestConcurrentSessions:
    """Tests for handling multiple concurrent sessions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_runs(self, sample_metadata):
        """
        Simulate 20 concurrent agent runs.
        Verifies no crashes or race conditions.
        """
        async def run_single_session(session_num: int):
            try:
                result = await run_agent(
                    session_id=f"concurrent-{session_num:03d}",
                    message=f"Test message for session {session_num}",
                    messages_history=[],
                    metadata=sample_metadata,
                    turn_count=1,
                )
                return {"session": session_num, "success": True, "result": result}
            except Exception as e:
                return {"session": session_num, "success": False, "error": str(e)}
        
        # Run 20 concurrent sessions
        tasks = [run_single_session(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Count successes
        successes = sum(1 for r in results if r["success"])
        failures = [r for r in results if not r["success"]]
        
        # All should succeed
        assert successes == 20, f"Expected 20 successes, got {successes}. Failures: {failures}"

    @pytest.mark.asyncio
    async def test_varying_scam_levels_concurrent(self, sample_metadata):
        """
        Run concurrent sessions with different message types.
        Verifies correct classification under load.
        """
        test_cases = [
            {"msg": "Hello, how are you?", "expected": "safe"},
            {"msg": "Your account is blocked!", "expected": "suspected"},
            {"msg": "Send OTP to verify@upi now!", "expected": "suspected"},
            {"msg": "Hi friend, good morning!", "expected": "safe"},
            {"msg": "Urgent: KYC update required immediately!", "expected": "suspected"},
        ]
        
        async def run_test_case(case_num: int, case: dict):
            result = await run_agent(
                session_id=f"classify-{case_num:03d}",
                message=case["msg"],
                messages_history=[],
                metadata=sample_metadata,
                turn_count=1,
            )
            return {
                "case": case_num,
                "message": case["msg"],
                "expected": case["expected"],
                "actual": result["scam_level"],
            }
        
        # Run all test cases concurrently
        tasks = [run_test_case(i, case) for i, case in enumerate(test_cases)]
        results = await asyncio.gather(*tasks)
        
        # Verify results
        for r in results:
            if r["expected"] == "safe":
                assert r["actual"] == "safe", f"False positive: {r}"
            else:
                assert r["actual"] in ["suspected", "confirmed"], f"False negative: {r}"


class TestSessionManagerFallback:
    """Tests for local file store fallback when Redis fails."""
    
    def test_local_store_exists(self):
        """Verify LocalFileStore module exists and is importable."""
        from app.services.local_store import LocalFileStore
        
        store = LocalFileStore()
        assert store is not None
    
    def test_local_store_save_and_load(self, session_factory):
        """Test LocalFileStore can save and retrieve sessions."""
        from app.services.local_store import LocalFileStore
        
        store = LocalFileStore()
        
        # Create test session
        session = session_factory(
            session_id="local-store-001",
            is_scam_confirmed=True,
            messages=[{"sender": "test", "text": "Hello"}],
        )
        
        # Save using set() - sync method
        result = store.set(session.session_id, session.model_dump())
        assert result is True
        
        # Load using get() - sync method
        loaded = store.get(session.session_id)
        
        # Verify
        assert loaded is not None
        assert loaded["session_id"] == session.session_id
        assert loaded["is_scam_confirmed"] == session.is_scam_confirmed
        
        # Cleanup
        store.delete(session.session_id)
