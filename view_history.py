import asyncio
import json
import logging
from app.services import get_session_manager
from app.config import get_settings

# Silence logs for clean output
logging.basicConfig(level=logging.ERROR)

async def view_session(session_id: str):
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        print(f"\n❌ Session '{session_id}' not found.")
        return

    print(f"\n" + "="*50)
    print(f"CONVERSATION HISTORY: {session_id}")
    print(f"Scam Level: {session.scam_level} (Confidence: {session.scam_confidence})")
    print(f"Is Confirmed: {session.is_scam_confirmed}")
    print("="*50 + "\n")

    for i, msg in enumerate(session.messages):
        sender = msg.get("sender", "unknown").upper()
        text = msg.get("text", "")
        timestamp = msg.get("timestamp", "")
        
        color = "\033[94m" if sender == "AGENT" else "\033[91m"
        reset = "\033[0m"
        
        print(f"[{i+1}] {color}{sender}{reset} ({timestamp}):")
        print(f"    {text}\n")

    if session.extracted_intelligence:
        print("="*50)
        print("EXTRACTED INTELLIGENCE:")
        intel = session.extracted_intelligence
        if hasattr(intel, 'model_dump'):
            intel_dict = intel.model_dump()
        else:
            intel_dict = dict(intel)
            
        for key, val in intel_dict.items():
            if val:
                print(f"- {key}: {', '.join(val) if isinstance(val, list) else val}")
    print("="*50 + "\n")

async def list_sessions():
    """Lists all available sessions from the local data directory."""
    data_dir = "data/sessions"
    print("\n" + "="*50)
    print("AVAILABLE LOCAL SESSIONS")
    print("="*50)
    
    import os
    if not os.path.exists(data_dir):
        print("No local sessions found.")
        return
        
    files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
    if not files:
        print("No local sessions found.")
    else:
        for f in files:
            session_id = f.replace(".json", "")
            print(f"- {session_id}")
    print("="*50 + "\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        asyncio.run(list_sessions())
        print("Usage: python view_history.py <session_id>")
    else:
        session_id = sys.argv[1]
        asyncio.run(view_session(session_id))
