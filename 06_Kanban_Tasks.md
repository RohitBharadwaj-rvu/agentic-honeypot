# 06. Kanban Task Board

# 06. Kanban Task Board

## 🚨 High Priority (Overhaul)
- [ ] **[Infra]** Implement `LocalFileStore` for persistent fallback (SQLite/JSON).
- [ ] **[Config]** Externalize Rules: Move regex/keywords to `app/core/rules.py`.

## 🚧 Medium Priority (Remaining Features)
- [ ] **[Logic]** Implement "Anti-Suspicion" delays/typos.
- [ ] **[Test]** Expand test coverage to 100% passing.

## ✅ Completed
- [x] **[Infra]** Setup FastAPI + Upstash Redis + Pydantic.
- [x] **[AI]** Implement `ScamDetector` Node.
- [x] **[AI]** Implement `PersonaGenerator` Node.
- [x] **[AI]** Create `LangGraph` workflow.
- [x] **[Logic]** Implement `IntelligenceExtractor` (Regex + LLM).
- [x] **[Logic]** Implement Bank Account & Keyword Extraction.
- [x] **[API]** Implement Mandatory Callback (`POST` to Guvi).
- [x] **[Data]** Expand Golden Dataset (20 -> 50) with diverse scam types.
- [x] **[Logic]** Implement Intel-Based Termination Logic (extracted_success).
- [x] **[Test]** Implement `MockLLMClient` for deterministic testing.
- [x] **[Test]** Create pytest infrastructure (conftest.py, pytest.ini).
- [x] **[Test]** Implement regression tests - callback fires exactly once.
- [x] **[Test]** Implement load tests - session size & concurrency.
- [x] **[Test]** Implement golden dataset validation (20 transcripts).

