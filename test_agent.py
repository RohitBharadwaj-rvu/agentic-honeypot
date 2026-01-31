"""
Test script for the LangGraph agent.
Run: python test_agent.py
"""
import asyncio
from app.agent.graph import run_agent


async def test_agent():
    print("=" * 50)
    print("Testing LangGraph Agent")
    print("=" * 50)
    
    # Test 1: Safe message
    print("\n[TEST 1] Safe message")
    result = await run_agent(
        session_id="test-001",
        message="Hello, how are you?",
        messages_history=[],
        metadata={"channel": "SMS", "language": "en", "locale": "IN"},
        turn_count=1,
    )
    print(f"  scam_level: {result.get('scam_level')}")
    print(f"  reply: {result.get('agent_reply')[:80]}...")
    print(f"  turn_count: {result.get('turn_count')}")
    
    # Test 2: Suspected scam (urgency keywords)
    print("\n[TEST 2] Suspected scam (urgency)")
    result = await run_agent(
        session_id="test-002",
        message="Your account is blocked! Verify immediately!",
        messages_history=[],
        metadata={"channel": "SMS", "language": "en", "locale": "IN"},
        turn_count=1,
    )
    print(f"  scam_level: {result.get('scam_level')}")
    print(f"  reply: {result.get('agent_reply')[:80]}...")
    print(f"  extracted: {result.get('extracted_intelligence')}")
    
    # Test 3: Confirmed scam (UPI/OTP request)
    print("\n[TEST 3] Confirmed scam (UPI/OTP)")
    result = await run_agent(
        session_id="test-003",
        message="Send OTP to verify. Pay Rs 10 to abc@upi for refund.",
        messages_history=[],
        metadata={"channel": "SMS", "language": "en", "locale": "IN"},
        turn_count=1,
    )
    print(f"  scam_level: {result.get('scam_level')}")
    print(f"  reply: {result.get('agent_reply')[:80]}...")
    print(f"  extracted UPIs: {result.get('extracted_intelligence', {}).get('upiIds')}")
    print(f"  termination_reason: {result.get('termination_reason')}")
    
    # Test 4: Phone number extraction
    print("\n[TEST 4] Phone number extraction")
    result = await run_agent(
        session_id="test-004",
        message="Call me urgently at 9876543210 for KYC update",
        messages_history=[],
        metadata={"channel": "SMS", "language": "en", "locale": "IN"},
        turn_count=1,
    )
    print(f"  scam_level: {result.get('scam_level')}")
    print(f"  extracted phones: {result.get('extracted_intelligence', {}).get('phoneNumbers')}")
    print(f"  termination_reason: {result.get('termination_reason')}")
    
    # Test 5: Max turns termination
    print("\n[TEST 5] Max turns check (turn 10)")
    result = await run_agent(
        session_id="test-005",
        message="Hello again",
        messages_history=[],
        metadata={"channel": "SMS", "language": "en", "locale": "IN"},
        turn_count=9,  # After increment will be 10
    )
    print(f"  turn_count: {result.get('turn_count')}")
    print(f"  termination_reason: {result.get('termination_reason')}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_agent())
