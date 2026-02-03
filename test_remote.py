import requests
import json

url = "https://rohithhegde26-agentic-honeypot.hf.space/webhook"
headers = {
    "x-api-key": "Honeypot_Key_123",
    "Content-Type": "application/json"
}
payload = {
    "sessionId": "test-session-123",
    "message": {
        "sender": "scammer",
        "text": "Hello, this is a test from the agent.",
        "timestamp": "2026-02-03T23:30:00Z"
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
