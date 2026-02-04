
import requests
import json

URL = "http://localhost:8000/webhook"
API_KEY = "local-dev-secret-key"

def test_alias_fail():
    # This payload uses "session_id" instead of "sessionId"
    # and "msg" instead of "message"
    # These were likely aliases before but might fail now.
    payload = {
        "session_id": "diagnostic-session",
        "msg": {
            "sender": "scammer",
            "text": "Hello",
            "time": "2024-01-01T12:00:00Z"
        }
    }
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    
    print(f"Testing with old aliases...")
    try:
        response = requests.post(URL, headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_alias_fail()
