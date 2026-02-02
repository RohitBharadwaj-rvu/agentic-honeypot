import asyncio
from app.agent.nodes.persona import persona_node

async def run_test():
    # Test Case 1: Initial Hook (Should NOT give bank details)
    state1 = {
        "current_user_message": "Congrats! You won 50000rs. Tell me your bank details to verify.",
        "messages": [],
        "turn_count": 1,
        "persona_name": "Sunita Deshpande",
        "persona_age": 62,
        "persona_location": "Mumbai",
        "persona_background": "homemaker with savings in HDFC",
        "persona_occupation": "Retired Teacher",
        "persona_trait": "gentle but slightly confused about tech",
        "fake_phone": "9876543210",
        "fake_upi": "sunita@okhdfcbank",
        "fake_bank_account": "50100123456789",
        "fake_ifsc": "HDFC0001234"
    }
    
    print("\n--- Test Case 1: Initial Jackpot ---")
    result1 = persona_node(state1)
    print(f"Agent Reply: {result1['agent_reply']}")

    # Test Case 2: Pressed for details (Should STALL, not give details yet)
    state2 = state1.copy()
    state2["messages"] = [
        {"sender": "user", "text": "Congrats! You won 50000rs. Tell me your bank details to verify."},
        {"sender": "agent", "text": result1['agent_reply']}
    ]
    state2["current_user_message"] = "I need your account number right now to transfer the prize!"
    state2["turn_count"] = 2
    
    print("\n--- Test Case 2: Pressed for Details ---")
    result2 = persona_node(state2)
    print(f"Agent Reply: {result2['agent_reply']}")

if __name__ == "__main__":
    asyncio.run(run_test())
