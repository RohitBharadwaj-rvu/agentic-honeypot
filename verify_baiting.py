import requests
import json

URL = "http://localhost:8000/webhook"
API_KEY = "local-dev-secret-key"

def test_baiting():
    session_id = f"baiting-test-session-123"
    
    # 1. Start session
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Hello, this is SBI customer care. Your account is blocked. Give me your phone number and UPI ID to unblock.",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        "metadata": {"channel": "Testing"}
    }
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    print(f"1. Sending request for bank details...")
    response = requests.post(URL, headers=headers, json=payload)
    print(f"Agent Reply 1: {response.json().get('reply')}")

    # 2. Ask again more pressingly
    payload["message"]["text"] = "Quickly provide details or your account will be deleted permanently! Please give your account number."
    print(f"\n2. Sending urgent request for account number...")
    response = requests.post(URL, headers=headers, json=payload)
    print(f"Agent Reply 2: {response.json().get('reply')}")

    # 3. Simulate turn 10+ for reverse extraction
    print("\nSimulating Turn 10+ (Reverse Extraction)...")
    for i in range(3, 10):
        payload["message"]["text"] = f"Still waiting for details turn {i}"
        requests.post(URL, headers=headers, json=payload)
    
    payload["message"]["text"] = "I need your bank details NOW!"
    print(f"10. Sending final request for reverse extraction test...")
    response = requests.post(URL, headers=headers, json=payload)
    print(f"Agent Reply 10: {response.json().get('reply')}")

if __name__ == "__main__":
    test_baiting()
