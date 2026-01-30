# 07. LangGraph State Schema

## 1. State Definition
The `AgentState` TypedDict defines exactly what data is passed between nodes.

```python
from typing import List, Dict, Optional, TypedDict, Annotated
import operator

class ExtractedData(TypedDict):
    bankAccounts: List[str]
    upiIds: List[str]
    phishingLinks: List[str]
    phoneNumbers: List[str]
    suspiciousKeywords: List[str]

class AgentState(TypedDict):
    # Session Identifiers
    session_id: str
    
    # Message Flow
    messages: Annotated[List[Dict], operator.add] # Append-only log
    current_user_message: str
    
    # Analysis State
    scam_confidence: float # 0.0 to 1.0
    is_scam_confirmed: bool
    scam_level: str # "safe", "suspected", "confirmed"
    
    # Extracted Intel
    extracted_intelligence: ExtractedData
    
    # Control Flow
    turn_count: int
    termination_reason: Optional[str] # "max_turns", "extracted_success", "user_quit"
    agent_notes: str

```

## 2. Transition Logic (Edges)

1. **Start** -> `Node: Detector`
2. `Node: Detector` -> **Conditional Edge**:
* If `Safe`: -> `Node: End` (or Simple Reply)
* If `Suspect` OR `Confirmed`: -> `Node: Extractor`


3. `Node: Extractor` -> `Node: PersonaGenerator`
4. `Node: PersonaGenerator` -> `Node: Output`
5. `Node: Output` -> **End** (Wait for next API call)

*Note: The Callback logic is triggered by the API layer based on the final state of `is_scam_confirmed` and `termination_reason`.*
