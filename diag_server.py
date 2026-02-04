
import asyncio
from app.main import app
from httpx import AsyncClient
import json

async def test():
    print("Starting integration test...")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "sessionId": "test-session",
            "message": {
                "sender": "scammer",
                "text": "hi",
                "timestamp": "2024-01-01T12:00:00+05:30"
            }
        }
        print(f"Sending payload: {json.dumps(payload)}")
        try:
            response = await ac.post(
                "/webhook", 
                headers={"X-API-KEY": "local-dev-secret-key"}, 
                json=payload
            )
            print(f"STATUS: {response.status_code}")
            print(f"BODY: {response.text}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
