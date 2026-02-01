"""
LangGraph Workflow Definition.
Orchestrates the Detect -> Extract -> Engage flow with conditional routing.
"""
import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END

from app.config import get_settings
from app.agent.state import AgentState
from app.agent.nodes.detector import detector_node
from app.agent.nodes.extractor import extractor_node
from app.agent.nodes.persona import persona_node
from app.agent.nodes.output import output_node

logger = logging.getLogger(__name__)


def route_after_detection(state: AgentState) -> Literal["extractor", "output"]:
    """
    Conditional edge: Route based on scam detection result.
    
    - If safe: Go directly to output_node
    - If suspected/confirmed: Continue to extractor_node
    """
    scam_level = state.get("scam_level", "safe")
    turn_count = state.get("turn_count", 0)
    
    # If conversation has started (turn > 1), keep engaging even if "safe"
    # This prevents the agent from staying silent or giving default responses in the middle of a chat
    if scam_level == "safe" and turn_count <= 1:
        logger.info("Routing to OUTPUT (safe message, initial turn)")
        return "output"
    else:
        logger.info(f"Routing to EXTRACTOR (scam_level={scam_level}, turn={turn_count})")
        return "extractor"


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Flow:
    1. Start -> detector_node
    2. detector_node -> (safe -> output_node) | (suspected/confirmed -> extractor_node)
    3. extractor_node -> persona_node
    4. persona_node -> output_node
    5. output_node -> End
    
    Node Responsibilities:
    - detector_node: Sets scam_level only
    - extractor_node: Updates extracted_intelligence only
    - persona_node: Generates reply text (agent_reply) only
    - output_node: Returns reply and updates turn_count
    """
    # Create graph with AgentState
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("detector", detector_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("persona", persona_node)
    graph.add_node("output", output_node)
    
    # Set entry point
    graph.set_entry_point("detector")
    
    # Add conditional edge from detector
    graph.add_conditional_edges(
        "detector",
        route_after_detection,
        {
            "extractor": "extractor",
            "output": "output",
        }
    )
    
    # Extractor -> Persona
    graph.add_edge("extractor", "persona")
    
    # Persona -> Output
    graph.add_edge("persona", "output")
    
    # Output always ends
    graph.add_edge("output", END)
    
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
    
    # Get settings for persona configuration
    settings = get_settings()
    
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
        "persona_name": settings.PERSONA_NAME,
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
