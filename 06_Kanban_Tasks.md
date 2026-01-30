# 06. Kanban Task Board

## 🚨 High Priority
- [ ] **[Infra]** Setup FastAPI + Upstash Redis + Pydantic.
- [ ] **[Data]** Generate 20 Synthetic Scam Transcripts (The "Golden Set").
- [ ] **[AI]** Implement `ScamDetector` Node (Temp 0, Output: Enum[Safe, Suspect, Confirmed]).
- [ ] **[AI]** Implement `PersonaGenerator` Node (Temp 0.7, Configurable Persona).
- [ ] **[AI]** Create `LangGraph` workflow.

## 🚧 Medium Priority
- [ ] **[Logic]** Implement `IntelligenceExtractor` (Regex + LLM).
- [ ] **[Logic]** Implement "Anti-Suspicion" delays/typos.
- [ ] **[API]** Implement Mandatory Callback (`POST` to Guvi).
- [ ] **[Test]** Write **Evaluation Parity Test** (Full Lifecycle Simulation).

## 🧪 Testing & Validation
- [ ] **[Test]** **Regression:** Ensure callback is sent exactly once per session.
- [ ] **[Test]** **Negative:** Ensure innocent messages trigger no callback.
- [ ] **[Test]** Run "Golden Set" simulation and calculate detection score.
