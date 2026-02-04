
from app.schemas.message import WebhookRequest
import json

def test_pydantic_aliases():
    payload = {
        "session_id": "test-alias",
        "msg": {
            "sender": "scammer",
            "text": "Hello",
            "time": "2024-01-01T12:00:00Z"
        }
    }
    print(f"Validating payload: {json.dumps(payload, indent=2)}")
    try:
        req = WebhookRequest(**payload)
        print("SUCCESS: Aliases work!")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_pydantic_aliases()
