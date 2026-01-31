# 06. Kanban Task Board

# 06. Kanban Task Board

## 🚨 High Priority (Overhaul)
- [ ] **[Infra]** Implement `LocalFileStore` for persistent fallback (SQLite/JSON).
- [ ] **[Config]** Externalize Rules: Move regex/keywords to `app/core/rules.py`.
- [ ] **[Test]** Implement `MockLLMClient` for deterministic testing.
- [ ] **[AI]** Implement "Script Fallback" for LLM rate limit exhaustion.

## 🚧 Medium Priority (Remaining Features)
- [ ] **[Logic]** Implement "Anti-Suspicion" delays/typos.
- [ ] **[API]** Implement Mandatory Callback (`POST` to Guvi).
- [ ] **[Test]** Write **Evaluation Parity Test** (Full Lifecycle Simulation).

## ✅ Completed
- [x] **[Infra]** Setup FastAPI + Upstash Redis + Pydantic.
- [x] **[AI]** Implement `ScamDetector` Node.
- [x] **[AI]** Implement `PersonaGenerator` Node.
- [x] **[AI]** Create `LangGraph` workflow.
- [x] **[Logic]** Implement `IntelligenceExtractor` (Regex + LLM).
- [x] **[Logic]** Implement Bank Account & Keyword Extraction.
