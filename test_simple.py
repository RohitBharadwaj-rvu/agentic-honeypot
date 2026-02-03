import requests
import json

URL = "http://localhost:8000/webhook"
API_KEY = "local-dev-secret-key"

def test_sync():
    payload = {
        "sessionId": "sync-test-session",
        "message": {
            "sender": "scammer",
            "text": "Hello, this is from the bank. We need your UPI ID.",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        "metadata": {"channel": "SMS"}
    }
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    print(f"Sending request to {URL}...")
    response = requests.post(URL, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_sync()
