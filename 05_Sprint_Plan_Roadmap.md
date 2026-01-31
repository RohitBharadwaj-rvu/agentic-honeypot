# 05. Project Roadmap & Sprints

## Sprint 1: Foundation & Infrastructure
**Goal:** Working "Echo" API with Redis.
1.  Setup FastAPI + Uvicorn + Upstash Redis.
2.  Implement `SessionManager` (Upstash Redis) - ensuring efficient serialization.
3.  Create Pydantic models for Input/Output.
4.  **Deliverable:** API accepts JSON, saves to Redis, returns dummy JSON.

## Sprint 2: The Agentic Core & Synthetic Data
**Goal:** The Agent "Thinks" + Initial Data.
1.  **Synthetic Data (Early Win):** Generate 20 "Golden" scam transcripts using a superior LLM (e.g., Claude 3.5 Sonnet / GPT-4o). Use these for prompt tuning immediately.
2.  **LangGraph:** Implement `Detect` (Temp 0) and `Engage` (Temp 0.7) nodes.
3.  **Model Integration:** Connect `kimi-k2` and `mistral-nemo`.

## Sprint 3: The Spy (Intelligence & Logic)
**Goal:** Extraction and Scam Confidence Levels.
1.  **Extraction Node:** Implement Regex + `r1t-chimera` for extraction.
2.  **Logic:** Implement "Suspected" vs "Confirmed" scam logic.
3.  **State Management:** Update `extractedIntelligence` in Redis.

## Sprint 4: The Reporter (Callback & Polish)
**Goal:** Competition Compliance.
1.  **Callback:** Implement `updateHoneyPotFinalResult` logic.
2.  **Logic:** Ensure Callback triggers **only** on Confirmed Scam + End of Chat.
3.  **Refinement:** Expand Golden Dataset to 50 conversations.

## Sprint 5: Testing & CI/CD
**Goal:** Reliability.
1.  **Regression:** Add test to ensure callback fires exactly once.
2.  **Load Test:** 10k-50k simulated sessions. Verify session JSON size stays <1KB to fit 256MB free tier limit.
3.  **Final Dry Run:** Run the agent against the full Golden Dataset.
