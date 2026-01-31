"""
LangGraph Workflow Definition.
Orchestrates the Detect -> Engage flow with conditional routing.
"""
import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.detector import detect_scam
from app.agent.nodes.persona import generate_persona_reply

logger = logging.getLogger(__name__)


def route_after_detection(state: AgentState) -> Literal["persona", "end"]:
    """
    Conditional edge: Route based on scam detection result.
    
    - If safe: End (simple reply)
    - If suspected/confirmed: Continue to persona engagement
    """
    scam_level = state.get("scam_level", "safe")
    
    if scam_level == "safe":
        logger.info("Routing to END (safe message)")
        return "end"
    else:
        logger.info(f"Routing to PERSONA (scam_level={scam_level})")
        return "persona"


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Flow:
    1. Start -> Detector
    2. Detector -> (safe -> End) | (suspect/confirmed -> Persona)
    3. Persona -> End
    """
    # Create graph with AgentState
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("detector", detect_scam)
    graph.add_node("persona", generate_persona_reply)
    
    # Set entry point
    graph.set_entry_point("detector")
    
    # Add conditional edge from detector
    graph.add_conditional_edges(
        "detector",
        route_after_detection,
        {
            "persona": "persona",
            "end": END,
        }
    )
    
    # Persona always ends
    graph.add_edge("persona", END)
    
    return graph


# Compile the graph once
_compiled_graph = None


def get_compiled_graph():
    """Get the compiled graph (lazy initialization)."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = create_agent_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


async def run_agent(
    session_id: str,
    message: str,
    messages_history: list,
    metadata: Dict[str, str],
    turn_count: int = 1,
    existing_intel: Dict = None,
) -> Dict[str, Any]:
    """
    Run the agent workflow for a single turn.
    
    Args:
        session_id: Unique session identifier
        message: Current user message
        messages_history: Previous messages in conversation
        metadata: Channel, language, locale info
        turn_count: Current turn number
        existing_intel: Previously extracted intelligence
    
    Returns:
        Updated agent state with reply
    """
    logger.info(f"Running agent for session {session_id}, turn {turn_count}")
    
    # Initialize state
    initial_state: AgentState = {
        "session_id": session_id,
        "current_user_message": message,
        "messages": messages_history or [],
        "scam_confidence": 0.0,
        "is_scam_confirmed": False,
        "scam_level": "safe",
        "extracted_intelligence": existing_intel or {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": [],
        },
        "turn_count": turn_count,
        "termination_reason": None,
        "agent_notes": "",
        "agent_reply": "",
        "persona_name": "Ramesh",
        "channel": metadata.get("channel", "SMS"),
        "language": metadata.get("language", "en"),
        "locale": metadata.get("locale", "IN"),
    }
    
    # Run the graph
    graph = get_compiled_graph()
    result = await graph.ainvoke(initial_state)
    
    # Ensure we have a reply
    if not result.get("agent_reply"):
        result["agent_reply"] = "Hello, I think there is some confusion. Who is this?"
    
    logger.info(f"Agent completed. Reply: {result['agent_reply'][:50]}...")
    
    return result
