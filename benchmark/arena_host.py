import asyncio
import json
import logging
import os
import uuid
import sys
from typing import List, Dict

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.agent.workflow import run_agent

# Initialize Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Supabase (We use the client to POLLING for now as realtime-py is complex to set up in one go without deps)
# Actually, for an MVP, polling every 1-2 seconds is fine and robust.
try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase: pip install supabase")
    sys.exit(1)

BENCHMARK_CONFIG_FILE = "benchmark/benchmark_config.json"

class ArenaHost:
    def __init__(self):
        self.supabase: Client = None
        self.contestants = []
        self.processed_message_ids = set()
        
    def load_config(self):
        if not os.path.exists(BENCHMARK_CONFIG_FILE):
            logger.error(f"Config not found: {BENCHMARK_CONFIG_FILE}")
            return False
        with open(BENCHMARK_CONFIG_FILE, "r") as f:
            data = json.load(f)
            self.contestants = data.get("contestants", [])
        logger.info(f"Loaded {len(self.contestants)} contestants.")
        return True

    def connect_supabase(self):
        # We expect these in env or ask user. 
        # Since user provided URL, we might need Key.
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("ERROR: SUPABASE_URL and SUPABASE_KEY environment variables required.")
            print("Please set them in your terminal before running.")
            return False
            
        self.supabase = create_client(url, key)
        logger.info("Connected to Supabase.")
        return True

    async def generate_reply(self, contestant, message, history):
        """Run a single agent."""
        name = contestant.get("name")
        api_key = contestant.get("api_key")
        base_url = contestant.get("base_url")
        model = contestant.get("model")
        
        # Inject Config
        os.environ["NVIDIA_API_KEY"] = api_key
        if base_url: os.environ["NVIDIA_BASE_URL"] = base_url
        if model: 
            os.environ["MODEL_PRIMARY"] = model
            os.environ["MODEL_FALLBACK"] = model
            
        get_settings.cache_clear()
        
        try:
            # We use a temp session ID for the agent logic, but we might want to keep state?
            # For this benchmark, let's treat each message as a new turn or passed history.
            # Passing history is better.
            
            result = await run_agent(
                session_id=f"arena-{uuid.uuid4()}",
                message=message,
                messages_history=history,
                metadata={"channel": "Arena", "language": "en", "locale": "IN"},
                turn_count=len(history) + 1
            )
            return {
                "sender": f"Agent {name}", # We might want to mask this for voters, but DB needs to know.
                "alias": name, # We will let the frontend mask it or we assign an ephemeral alias here?
                               # Let's assign an ephemeral alias ID stored in the session maybe?
                               # For now, let's just send the name and let UI mask it.
                "content": result.get("agent_reply", "Error"),
                "scam_level": result.get("scam_level", "unknown")
            }
        except Exception as e:
            logger.error(f"Error {name}: {e}")
            return {"sender": name, "content": f"[Error] {e}", "scam_level": "error"}

    async def run_loop(self):
        logger.info("Arena Host Started. Waiting for USER messages...")
        
        while True:
            try:
                # Poll for new messages where is_bot = FALSE and processed = FALSE (or we track IDs)
                # We need a way to mark processed. 
                # Let's assume we look for messages created in last 5 seconds that we haven't seen?
                # Better: SELECT * FROM messages WHERE is_bot = FALSE AND created_at > LAST_CHECK
                # But creating a 'processed' flag in DB is better. 
                # For this MVP, let's keep it simple: "responses" table? 
                # or just 'processed' array in memory? Memory is fragile.
                # Let's just look for messages without replies? 
                # Query: Get last user message. If it's new, process it.
                
                response = self.supabase.table("messages").select("*").eq("is_bot", False).order("timestamp", desc=True).limit(1).execute()
                
                if response.data:
                    last_msg = response.data[0]
                    msg_id = last_msg['id']
                    content = last_msg['content']
                    session_id = last_msg['session_id']
                    
                    if msg_id not in self.processed_message_ids:
                        logger.info(f"New User Message: {content}")
                        self.processed_message_ids.add(msg_id)
                        
                        # 1. Fetch History for this session
                        hist_res = self.supabase.table("messages").select("*").eq("session_id", session_id).order("timestamp", desc=False).execute()
                        history = [] # Convert DB messages to Agent format if needed
                        
                        # 2. Generate Replies
                        tasks = [self.generate_reply(c, content, history) for c in self.contestants]
                        results = await asyncio.gather(*tasks)
                        
                        # 3. Post Replies
                        for res in results:
                            # We might want to anonymize here?
                            # Actually, let's just insert them.
                            self.supabase.table("messages").insert({
                                "session_id": session_id,
                                "content": res["content"],
                                "sender": res["sender"], # This contains Model Name
                                "is_bot": True,
                                "timestamp": "now()" # Let Supabase handle? Or isoformat
                            }).execute()
                            
                        logger.info("Replies posted.")
                        
            except Exception as e:
                logger.error(f"Loop error: {e}")
                
            await asyncio.sleep(2)

if __name__ == "__main__":
    host = ArenaHost()
    if host.load_config() and host.connect_supabase():
        asyncio.run(host.run_loop())
