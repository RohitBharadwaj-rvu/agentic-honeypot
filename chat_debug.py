import requests
import json
import time
from datetime import datetime

url = "http://localhost:8000/webhook"
headers = {
    "X-API-KEY": "local-dev-secret-key",
    "Content-Type": "application/json"
}

session_id = f"test-session-{int(time.time())}"

print("--- Interactive Honeypot Chat ---")
print(f"Session: {session_id}")
print("Type 'quit' or 'exit' to stop.\n")

while True:
    user_input = input("You (as scammer): ")
    
    if user_input.lower() in ['quit', 'exit']:
        break
        
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": user_input,
            "timestamp": datetime.now().isoformat()
        },
        "metadata": {
            "channel": "Interactive"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            # Extract the response text based on WebhookResponse schema
            reply = data.get("reply", "No response text found")
            print(f"\nAgent: {reply}\n")
        else:
            print(f"Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
