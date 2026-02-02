import requests
import json
import time

URL = "http://localhost:8000/webhook"
API_KEY = "local-dev-secret-key" # Default in .env or config

def start_session(session_id):
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Hi, I am from SBI. Your account is blocked.",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        "metadata": {"channel": "Testing"}
    }
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    response = requests.post(URL, headers=headers, json=payload)
    return response.json()

def test_variations():
    print("Testing Persona Variations...")
    personalities = []
    initial_replies = []
    
    for i in range(4):
        session_id = f"verify-session-{i}-{int(time.time())}"
        result = start_session(session_id)
        reply = result.get("reply", "")
        initial_replies.append(reply)
        
        print(f"Session {i} Reply: {reply}")
        # To verify the personality, we'd need to check the DB/Redis, 
        # but we can infer from the response style if it's working.
    
    print("\nInitial Replies Summary:")
    for r in initial_replies:
        print(f"- {r}")

    # Check if they are at least somewhat different (LLM vary + different personas)
    unique_replies = len(set(initial_replies))
    print(f"\nUnique Initial Replies: {unique_replies}/4")

if __name__ == "__main__":
    try:
        test_variations()
    except Exception as e:
        print(f"Verification failed: {e}")
        print("Make sure the server is running on http://localhost:8000")
