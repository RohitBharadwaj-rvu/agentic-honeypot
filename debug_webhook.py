import requests
import json
from datetime import datetime

url = "http://localhost:8000/webhook"
headers = {
    "X-API-KEY": "local-dev-secret-key",
    "Content-Type": "application/json"
}

payload = {
    "sessionId": "test-session",
    "message": {
        "sender": "scammer",
        "text": "Hello",
        "timestamp": datetime.now().isoformat()
    },
    "metadata": {
        "channel": "SMS"
    }
}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
