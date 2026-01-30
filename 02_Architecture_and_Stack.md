# 02. Architecture & Tech Stack

## 1. Core Technology
* **Language:** Python 3.10+
* **Web Framework:** FastAPI (Async is mandatory).
* **WSGI/ASGI:** Uvicorn.
* **Data Validation:** Pydantic V2 (Strict typing is required).
* **Session Storage:** Upstash Redis (Free Tier). Handles ~250k daily commands. Session size <1KB. **TTL: 1 hour** (Mandatory).
* **Orchestrator:** **LangGraph** (State machine based).

## 2. Model Selection Strategy (OpenRouter)
We prioritize free-tier models that excel at specific tasks. The system **MUST** degrade gracefully if a preferred model is unavailable.

### Primary Models
* **Roleplay / Engagement:** `kimi-k2` (Excellent at maintaining long context and persona).
* **Extraction / Reasoning:** `r1t-chimera` (Strong logic for JSON extraction and scam scoring).

### Fallback Model
* **Safety / Speed:** `mistral-nemo` (Low cost, fast, reliable fallback).

## 3. Determinism & Temperature Rules
To ensure testing reliability and system stability, strict parameters apply:

1.  **Extraction Node:** `Temperature = 0`. (Must be deterministic).
2.  **Detector Node:** `Temperature = 0`. (Must return strict Boolean/Enum).
3.  **Persona Node:** `Temperature = 0.6 - 0.8`. (Allowed variance for creativity).

## 4. System Components
1.  **Ingress (FastAPI):** Validates keys and schema.
2.  **Session Manager (Upstash):** 
    *   **Key Schema:** `honeypot:session:{sessionId}`
    *   **Robustness:** Monitor key size/count.
    *   **Degradation:** Falls back to in-process memory store (LRU Cache) if Redis is unavailable.
3.  **The Brain (LangGraph):** Orchestrates the `Detect -> Engage -> Extract` flow.
4.  **Egress (Callback Manager):** Handles the final POST to the evaluation server.
