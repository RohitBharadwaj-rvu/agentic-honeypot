"""
Local LLM Benchmark Arena - FastAPI Server
Run: python benchmark/server.py
Open: http://localhost:8080
"""
import asyncio
import json
import os
import sys
import random
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.agent.workflow import run_agent

app = FastAPI(title="LLM Benchmark Arena")

# --- Game State ---
class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.num_voters = 0
        self.contestants = []  # List of {name, model, api_key, base_url}
        self.turns = []        # List of turns, each turn has responses and votes
        self.current_turn = -1
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        
game = GameState()

# --- Load Contestants from Config ---
def load_contestants():
    config_path = os.path.join(os.path.dirname(__file__), "benchmark_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            data = json.load(f)
            game.contestants = data.get("contestants", [])
    else:
        game.contestants = []

# --- Models ---
class SetupRequest(BaseModel):
    num_voters: int

class MessageRequest(BaseModel):
    message: str

class VoteRequest(BaseModel):
    voter_id: int
    agent_alias: str  # e.g., "Agent A"

# --- API Endpoints ---

@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

@app.post("/api/setup")
async def setup_game(req: SetupRequest):
    """Initialize a new game session."""
    game.reset()
    game.num_voters = req.num_voters
    load_contestants()
    return {
        "status": "ok",
        "num_voters": game.num_voters,
        "num_contestants": len(game.contestants)
    }

@app.post("/api/send")
async def send_message(req: MessageRequest):
    """Send a message to all agents and get their replies."""
    if not game.contestants:
        raise HTTPException(status_code=400, detail="No contestants configured")
    
    message = req.message
    game.current_turn += 1
    
    # Add user message to history
    game.conversation_history.append({"role": "user", "content": message})
    
    # Generate replies from all contestants
    responses = []
    for contestant in game.contestants:
        # Inject config
        os.environ["NVIDIA_API_KEY"] = contestant.get("api_key", "")
        if contestant.get("base_url"):
            os.environ["NVIDIA_BASE_URL"] = contestant["base_url"]
        if contestant.get("model"):
            os.environ["MODEL_PRIMARY"] = contestant["model"]
            os.environ["MODEL_FALLBACK"] = contestant["model"]
        
        get_settings.cache_clear()
        
        try:
            result = await run_agent(
                session_id=f"arena-{game.session_id}-{game.current_turn}",
                message=message,
                messages_history=game.conversation_history[:-1],  # Exclude current
                metadata={"channel": "Arena", "language": "en", "locale": "IN"},
                turn_count=game.current_turn + 1
            )
            reply = result.get("agent_reply", "[No response]")
        except Exception as e:
            reply = f"[Error: {str(e)[:50]}]"
        
        responses.append({
            "contestant_name": contestant["name"],  # Hidden from UI
            "model": contestant.get("model", "unknown"),
            "reply": reply
        })
    
    # Shuffle for blind voting
    random.shuffle(responses)
    
    # Assign aliases (Agent A, B, C...)
    for i, resp in enumerate(responses):
        resp["alias"] = f"Agent {chr(65 + i)}"
    
    # Create turn record
    turn_data = {
        "turn_number": game.current_turn,
        "user_message": message,
        "responses": responses,
        "votes": {}  # {voter_id: alias}
    }
    game.turns.append(turn_data)
    
    # Return only what the UI needs (hide real names)
    return {
        "turn": game.current_turn,
        "message": message,
        "responses": [{"alias": r["alias"], "reply": r["reply"]} for r in responses],
        "num_voters": game.num_voters
    }

@app.post("/api/vote")
async def cast_vote(req: VoteRequest):
    """Record a vote from a voter."""
    if game.current_turn < 0 or game.current_turn >= len(game.turns):
        raise HTTPException(status_code=400, detail="No active turn")
    
    turn = game.turns[game.current_turn]
    
    # Check if voter already voted
    if req.voter_id in turn["votes"]:
        raise HTTPException(status_code=400, detail="Already voted")
    
    # Record vote
    turn["votes"][req.voter_id] = req.agent_alias
    
    # Check if all voted
    all_voted = len(turn["votes"]) >= game.num_voters
    
    return {
        "status": "ok",
        "votes_cast": len(turn["votes"]),
        "all_voted": all_voted
    }

@app.get("/api/status")
async def get_status():
    """Get current game status."""
    if game.current_turn < 0:
        return {"status": "waiting", "turn": -1}
    
    turn = game.turns[game.current_turn]
    return {
        "status": "active",
        "turn": game.current_turn,
        "votes_cast": len(turn["votes"]),
        "all_voted": len(turn["votes"]) >= game.num_voters
    }

@app.get("/api/results")
async def get_results():
    """Get final results - which model won."""
    # Tally votes per actual model
    tally = {}  # {contestant_name: vote_count}
    
    for turn in game.turns:
        # Create alias -> contestant mapping for this turn
        alias_map = {r["alias"]: r["contestant_name"] for r in turn["responses"]}
        
        for voter_id, voted_alias in turn["votes"].items():
            contestant = alias_map.get(voted_alias)
            if contestant:
                tally[contestant] = tally.get(contestant, 0) + 1
    
    # Sort by votes
    sorted_results = sorted(tally.items(), key=lambda x: -x[1])
    
    return {
        "total_turns": len(game.turns),
        "total_votes": sum(tally.values()),
        "results": [{"name": name, "votes": count} for name, count in sorted_results],
        "turns": [
            {
                "turn": t["turn_number"],
                "message": t["user_message"],
                "votes": t["votes"]
            } for t in game.turns
        ]
    }

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

if __name__ == "__main__":
    import uvicorn
    print("\n🎮 LLM Benchmark Arena")
    print("   Open http://localhost:8080 in your browser\n")
    uvicorn.run(app, host="0.0.0.0", port=8080)
