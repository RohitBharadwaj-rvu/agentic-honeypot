# 04. Testing & Validation Strategy

## 1. Evaluation Parity Test (The Gold Standard)
We must simulate the **exact** lifecycle used by the judges (GUVI).
* **Scenario:** Run a full conversation simulation.
* **Parity Checks:**
    1.  Send multiple webhook `POST` calls (User -> System).
    2.  Assert system replies synchronously.
    3.  **Assert Final Callback is triggered EXACTLY ONCE.**
    4.  Validate Callback Payload Schema matches requirements strictly.
    5.  Assert no further replies are generated after callback.

## 2. Negative Tests (Crucial)
Ensure the system stays quiet when it should.
* **Case A (False Positive):** Send a harmless message ("Hi dad, how are you?").
    * *Expect:* `scamDetected = False`, No Callback sent.
* **Case B (Premature End):** Conversation stops before intelligence is extracted.
    * *Expect:* No Callback sent (or Callback sent with `scamDetected=True` but empty intelligence, depending on business logic).
* **Case C (Resource Limits):** Simulate high volume (10k+) sessions.
    * *Expect:* Session state size must remain < 1KB avg to fit 256MB. System must handle Upstash connection limits gracefully.
* **Case D (TTL & Cleanup):** Check key existence after 61 minutes.
    * *Expect:* Key `honeypot:session:{sessionId}` must be deleted automatically.
* **Case E (Redis Failure):** Simulate Redis outage (wrong credentials/network block).
    * *Expect:* API returns 200 OK. System falls back to local memory. No crash.

## 3. Testing Layers

### Layer A: Unit Tests (Fast, No LLM)
* **Tools:** `pytest`, `hypothesis`.
* **Scope:** Regex extractors, State transitions, JSON validation.
* **Rule:** **Strict Determinism**. Do not call APIs.

### Layer B: LLM Contract Tests
* **Tools:** Mocked OpenRouter or Low-Temp calls.
* **Scope:** Assert `AgentReply` is valid JSON and does not leak system prompt.
* **Configuration:** Use `temperature=0` for these tests.

### Layer C: Adversarial / Red-Teaming
* **Polite Scammer:** "Sir, this is a routine check." (Test sensitivity).
* **Hinglish:** "Tera account band hoga." (Test language adaptability).
* **Gibberish:** "sfdg sfg dfg" (Test robustness).

## 4. Metrics to Log
* **Scam Detection Precision:** (Avoid false accusations).
* **Engagement Depth:** Avg messages per session.
* **Callback Success Rate:** % of confirmed scams that successfully hit the callback endpoint.
