"""
Quick test to verify termination logic is working.
"""
import asyncio
from app.agent.workflow import run_agent

async def test_termination():
    """Test if termination_reason gets set when intel is extracted."""
    
    # Simulate a scammer message with UPI ID
    scammer_message = "Please send money to scammer@paytm urgently. Your account will be blocked!"
    
    result = await run_agent(
        session_id="test-termination-001",
        message=scammer_message,
        messages_history=[],
        metadata={"channel": "SMS", "language": "en", "locale": "IN"},
        turn_count=1,
    )
    
    print("\n" + "="*60)
    print("TERMINATION LOGIC TEST")
    print("="*60)
    print(f"Message: {scammer_message}")
    print(f"\nScam Level: {result.get('scam_level')}")
    print(f"Scam Confirmed: {result.get('is_scam_confirmed')}")
    print(f"\nExtracted Intelligence:")
    intel = result.get('extracted_intelligence', {})
    print(f"  UPI IDs: {intel.get('upiIds', [])}")
    print(f"  Phone Numbers: {intel.get('phoneNumbers', [])}")
    print(f"  Bank Accounts: {intel.get('bankAccounts', [])}")
    print(f"  Phishing Links: {intel.get('phishingLinks', [])}")
    print(f"\nTermination Reason: {result.get('termination_reason')}")
    print(f"Agent Notes: {result.get('agent_notes')}")
    print("="*60)
    
    # Check if termination should have triggered
    has_intel = any([
        intel.get('upiIds'),
        intel.get('phoneNumbers'),
        intel.get('bankAccounts'),
        intel.get('phishingLinks')
    ])
    
    if has_intel and result.get('is_scam_confirmed'):
        if result.get('termination_reason'):
            print("✅ PASS: Termination reason was set correctly!")
        else:
            print("❌ FAIL: Termination reason should be set but is None!")
            print("\nDEBUG INFO:")
            print(f"  has_intel: {has_intel}")
            print(f"  is_scam_confirmed: {result.get('is_scam_confirmed')}")
            print(f"  Expected: termination_reason = 'extracted_success'")
            print(f"  Actual: termination_reason = {result.get('termination_reason')}")
    else:
        print(f"⚠️  No intel extracted or scam not confirmed (expected for this test)")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_termination())
