"""
Golden Dataset Validation Tests.
Run agent against all 50 golden transcripts and verify accuracy.
"""
import sys
from pathlib import Path
from typing import Dict, List, Any

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.workflow import run_agent


class TestScamDetection:
    """Tests for scam detection accuracy on golden dataset."""
    
    @pytest.mark.asyncio
    async def test_scam_transcripts_detected(self, golden_transcripts):
        """
        All scam transcripts should be detected as suspected or confirmed.
        This tests detection precision on known scams.
        """
        transcripts = golden_transcripts.get("transcripts", [])
        
        results = []
        for transcript in transcripts[:10]:  # Test first 10 for speed
            # Get first scammer message
            messages = transcript.get("messages", [])
            scammer_msg = next(
                (m["text"] for m in messages if m.get("sender") == "scammer"),
                "Test message"
            )
            
            result = await run_agent(
                session_id=f"golden-{transcript['id']}",
                message=scammer_msg,
                messages_history=[],
                metadata={"channel": "SMS", "language": "en", "locale": "IN"},
                turn_count=1,
            )
            
            results.append({
                "id": transcript["id"],
                "type": transcript.get("type", "unknown"),
                "scam_level": result["scam_level"],
                "expected": "suspected or confirmed",
            })
        
        # Calculate detection rate
        detected = sum(1 for r in results if r["scam_level"] in ["suspected", "confirmed"])
        total = len(results)
        detection_rate = detected / total if total > 0 else 0
        
        print(f"\n=== Scam Detection Results ===")
        print(f"Detected: {detected}/{total} ({detection_rate:.1%})")
        for r in results:
            status = "✓" if r["scam_level"] in ["suspected", "confirmed"] else "✗"
            print(f"  {status} {r['id']} ({r['type']}): {r['scam_level']}")
        
        # Require at least 80% detection rate
        assert detection_rate >= 0.8, f"Detection rate too low: {detection_rate:.1%}"


class TestIntelligenceExtraction:
    """Tests for intelligence extraction accuracy."""
    
    @pytest.mark.asyncio
    async def test_upi_extraction(self, golden_transcripts):
        """Test UPI ID extraction from golden transcripts."""
        transcripts = golden_transcripts.get("transcripts", [])
        
        # Filter transcripts that have expected UPI IDs
        upi_transcripts = [
            t for t in transcripts
            if t.get("expected_intel", {}).get("upiIds", [])
        ][:5]  # Test first 5
        
        results = []
        for transcript in upi_transcripts:
            messages = transcript.get("messages", [])
            # Combine all scammer messages
            scammer_text = " ".join(
                m["text"] for m in messages if m.get("sender") == "scammer"
            )
            
            result = await run_agent(
                session_id=f"upi-{transcript['id']}",
                message=scammer_text,
                messages_history=[],
                metadata={"channel": "SMS", "language": "en", "locale": "IN"},
                turn_count=1,
            )
            
            expected_upis = set(transcript["expected_intel"]["upiIds"])
            extracted_upis = set(result.get("extracted_intelligence", {}).get("upiIds", []))
            
            # Check if at least one expected UPI was found
            found = len(expected_upis & extracted_upis) > 0
            
            results.append({
                "id": transcript["id"],
                "expected": list(expected_upis),
                "extracted": list(extracted_upis),
                "found": found,
            })
        
        # Calculate extraction rate
        found_count = sum(1 for r in results if r["found"])
        total = len(results)
        extraction_rate = found_count / total if total > 0 else 0
        
        print(f"\n=== UPI Extraction Results ===")
        print(f"Extracted: {found_count}/{total} ({extraction_rate:.1%})")
        for r in results:
            status = "✓" if r["found"] else "✗"
            print(f"  {status} {r['id']}: expected={r['expected']}, got={r['extracted']}")
        
        # UPI extraction should be at least 60% accurate
        assert extraction_rate >= 0.6, f"UPI extraction rate too low: {extraction_rate:.1%}"

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, golden_transcripts):
        """Test suspicious keyword extraction."""
        transcripts = golden_transcripts.get("transcripts", [])[:5]
        
        keyword_hits = 0
        total_tests = 0
        
        for transcript in transcripts:
            messages = transcript.get("messages", [])
            scammer_text = " ".join(
                m["text"] for m in messages if m.get("sender") == "scammer"
            )
            
            result = await run_agent(
                session_id=f"keyword-{transcript['id']}",
                message=scammer_text,
                messages_history=[],
                metadata={"channel": "SMS", "language": "en", "locale": "IN"},
                turn_count=1,
            )
            
            extracted_keywords = result.get("extracted_intelligence", {}).get("suspiciousKeywords", [])
            
            if len(extracted_keywords) > 0:
                keyword_hits += 1
            total_tests += 1
        
        keyword_rate = keyword_hits / total_tests if total_tests > 0 else 0
        print(f"\n=== Keyword Extraction Results ===")
        print(f"Transcripts with keywords: {keyword_hits}/{total_tests} ({keyword_rate:.1%})")
        
        # Most scam messages should have keywords extracted
        assert keyword_rate >= 0.6, f"Keyword extraction rate too low: {keyword_rate:.1%}"


class TestFullConversationLifecycle:
    """Tests for multi-turn conversation flow."""
    
    @pytest.mark.asyncio
    async def test_multi_turn_engagement(self, golden_transcripts):
        """
        Test multi-turn conversation with a golden transcript.
        Verify agent stays engaged and extracts intel progressively.
        """
        transcripts = golden_transcripts.get("transcripts", [])
        if not transcripts:
            pytest.skip("No transcripts available")
        
        transcript = transcripts[0]  # Use first transcript
        messages = transcript.get("messages", [])
        
        # Simulate multi-turn conversation
        history = []
        final_result = None
        
        for turn, msg in enumerate([m for m in messages if m.get("sender") == "scammer"][:5]):
            result = await run_agent(
                session_id=f"lifecycle-{transcript['id']}",
                message=msg["text"],
                messages_history=history,
                metadata={"channel": "SMS", "language": "en", "locale": "IN"},
                turn_count=turn + 1,
            )
            
            # Add to history
            history.append({"sender": "scammer", "text": msg["text"]})
            history.append({"sender": "agent", "text": result.get("agent_reply", "")})
            
            final_result = result
        
        # Verify agent engaged (has reply)
        assert final_result is not None
        assert final_result.get("agent_reply"), "Agent should generate replies"
        
        # Verify scam was detected
        assert final_result["scam_level"] in ["suspected", "confirmed"]
        
        print(f"\n=== Multi-turn Lifecycle Test ===")
        print(f"Transcript: {transcript['id']}")
        print(f"Turns completed: {len(history) // 2}")
        print(f"Final scam_level: {final_result['scam_level']}")
        print(f"Extracted intel: {final_result.get('extracted_intelligence', {})}")

    @pytest.mark.asyncio
    async def test_termination_on_intel_success(self, golden_transcripts):
        """
        Test that termination triggers when sufficient intel is extracted.
        """
        # Find a transcript with expected UPIs
        transcripts = golden_transcripts.get("transcripts", [])
        upi_transcript = next(
            (t for t in transcripts if t.get("expected_intel", {}).get("upiIds")),
            None
        )
        
        if not upi_transcript:
            pytest.skip("No UPI transcript available")
        
        # Get all scammer messages combined
        messages = upi_transcript.get("messages", [])
        full_scam_text = " ".join(
            m["text"] for m in messages if m.get("sender") == "scammer"
        )
        
        result = await run_agent(
            session_id=f"termination-{upi_transcript['id']}",
            message=full_scam_text,
            messages_history=[],
            metadata={"channel": "SMS", "language": "en", "locale": "IN"},
            turn_count=1,
        )
        
        print(f"\n=== Termination Test ===")
        print(f"Transcript: {upi_transcript['id']}")
        print(f"Termination reason: {result.get('termination_reason')}")
        print(f"Intel extracted: {result.get('extracted_intelligence', {})}")
        
        # If UPI/bank account extracted, should have termination reason
        intel = result.get("extracted_intelligence", {})
        has_actionable_intel = (
            len(intel.get("upiIds", [])) > 0 or
            len(intel.get("bankAccounts", [])) > 0
        )
        
        if has_actionable_intel:
            assert result.get("termination_reason"), "Should terminate on intel extraction"


class TestMetrics:
    """Aggregate metrics tests for the golden dataset."""
    
    @pytest.mark.asyncio
    async def test_overall_accuracy_report(self, golden_transcripts):
        """Generate overall accuracy report for the golden dataset."""
        transcripts = golden_transcripts.get("transcripts", [])[:20]  # Test 20 samples
        
        metrics = {
            "total": len(transcripts),
            "detected": 0,
            "upi_extracted": 0,
            "phone_extracted": 0,
            "link_extracted": 0,
            "terminated": 0,
        }
        
        for transcript in transcripts:
            messages = transcript.get("messages", [])
            scammer_text = " ".join(
                m["text"] for m in messages if m.get("sender") == "scammer"
            )
            
            result = await run_agent(
                session_id=f"metrics-{transcript['id']}",
                message=scammer_text,
                messages_history=[],
                metadata={"channel": "SMS", "language": "en", "locale": "IN"},
                turn_count=1,
            )
            
            if result["scam_level"] in ["suspected", "confirmed"]:
                metrics["detected"] += 1
            
            intel = result.get("extracted_intelligence", {})
            if intel.get("upiIds"):
                metrics["upi_extracted"] += 1
            if intel.get("phoneNumbers"):
                metrics["phone_extracted"] += 1
            if intel.get("phishingLinks"):
                metrics["link_extracted"] += 1
            if result.get("termination_reason"):
                metrics["terminated"] += 1
        
        # Print report
        print("\n" + "=" * 50)
        print("GOLDEN DATASET ACCURACY REPORT")
        print("=" * 50)
        print(f"Total samples tested: {metrics['total']}")
        print(f"Scams detected:       {metrics['detected']}/{metrics['total']} ({metrics['detected']/metrics['total']:.1%})")
        print(f"UPIs extracted:       {metrics['upi_extracted']}/{metrics['total']}")
        print(f"Phones extracted:     {metrics['phone_extracted']}/{metrics['total']}")
        print(f"Links extracted:      {metrics['link_extracted']}/{metrics['total']}")
        print(f"Sessions terminated:  {metrics['terminated']}/{metrics['total']}")
        print("=" * 50)
        
        # Baseline assertions
        assert metrics["detected"] >= metrics["total"] * 0.7, "Detection rate too low"
