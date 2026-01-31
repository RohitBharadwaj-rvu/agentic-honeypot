# 01. Problem Statement: Agentic Honey-Pot

## 1. Executive Summary
We are building an **Agentic Honey-Pot**—an AI-powered system that detects online scams (bank fraud, UPI fraud, phishing) and autonomously engages scammers. The goal is to waste their time and extract useful intelligence (UPI IDs, bank accounts, phone numbers) without revealing that they are talking to an AI.

## 2. Core Objective
Design and deploy a public REST API that:
1.  **Detects** scam intent in incoming messages with confidence scoring.
2.  **Activates** an autonomous AI Agent upon detection.
3.  **Engages** the scammer using a configurable persona (Default: Anxious Retiree).
4.  **Extracts** actionable intelligence (PII, payment details, links).
5.  **Returns** structured JSON responses for immediate replies.
6.  **Reports** final intelligence to a mandatory callback endpoint.

## 3. Scam Detection Levels & Callback Logic
The system must distinguish between suspected and confirmed scams.

* **Level 1: Suspected Scam (Soft Confirmation)**
    * **Criteria:** High-risk keywords ("verify", "urgent", "blocked"), strange sender format.
    * **Action:** Engage cautiously to gather more info. Do NOT trigger final callback yet.
* **Level 2: Confirmed Scam (Hard Confirmation)**
    * **Criteria:** Explicit request for money/credentials, sharing of UPI ID/Phishing Link, or high confidence score from LLM.
    * **Action:** Continue engagement to extract maximum data. **Triggers mandatory callback** upon termination.

## 4. The API Contract (Input/Output)

### 4.1 Input (Webhook)
The system must accept a `POST` request representing an incoming message.
* **Headers:** `x-api-key: <SECRET>`, `Content-Type: application/json`
* **Payload:**
    ```json
    {
      "sessionId": "unique-session-id",
      "message": {
        "sender": "scammer",
        "text": "Your bank account is blocked. Update KYC immediately.",
        "timestamp": "2026-01-21T10:15:30Z"
      },
      "conversationHistory": [ ... ], // Array of previous message objects
      "metadata": { "channel": "SMS", "language": "en", "locale": "IN" }
    }
    ```

### 4.2 Output (Immediate Reply)
The system must respond synchronously with the agent's reply.
* **Payload:**
    ```json
    {
      "status": "success",
      "reply": "Oh my god, blocked? I have my pension in there! What do I do?"
    }
    ```

### 4.3 Mandatory Callback (Final Reporting)
**Trigger:** Sent ONLY when `is_scam_confirmed == True` AND the conversation has ended (extracted info or max turns).
**Endpoint:** `POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult`
**Payload:**
```json
{
  "sessionId": "unique-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 12,
  "extractedIntelligence": {
    "bankAccounts": ["123456789"],
    "upiIds": ["scammer@okaxis"],
    "phishingLinks": ["[http://fake-hdfc-kyc.com](http://fake-hdfc-kyc.com)"],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["blocked", "kyc", "urgent"]
  },
  "agentNotes": "Scammer used fear tactics regarding pension fund blocking."
}

```

## 5. Constraints & Ethics

* ❌ **No Impersonation:** Do not claim to be a real, specific individual.
* ❌ **No Illegal Acts:** Do not agree to commit crimes.
* ✅ **Responsible Data:** Handle PII securely.
