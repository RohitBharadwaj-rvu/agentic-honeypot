# How to Use the Honey-Pot API

## Option 1: Interactive Chat (Recommended)
The easiest way to test is to run the chat script in your terminal. This mimics a real conversation.

1.  Make sure your server is running (if not, run `python -m uvicorn app.main:app --reload`).
2.  Open a **new terminal**.
3.  Run:
    ```powershell
    python chat_debug.py
    ```
4.  Type messages as if you are the scammer. The agent will reply instantly.

---

## Option 2: Swagger UI (Manual Testing)
If you want to use the browser ("Post Section"):

1.  Go to **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.
2.  **Click the "Authorize" button** (green unlock icon) at the top right.
3.  Type `local-dev-secret-key` in the **value** box and click **Authorize**, then **Close**.
4.  Click on **`POST /webhook`** to expand it.
5.  Click the **Try it out** button (top right of the box).
4.  In the **Request body** box, paste this valid JSON:
    ```json
    {
      "sessionId": "manual-test-01",
      "message": {
        "sender": "scammer",
        "text": "Hello, I am calling from your bank.",
        "timestamp": "2024-02-01T12:00:00Z"
      },
      "conversationHistory": [],
      "metadata": {
        "channel": "WhatsApp"
      }
    }
    ```
5.  Click the big blue **Execute** button.
6.  Scroll down to **Server response**.
    *   **Code 200** means success.
    *   Look at the **Response body** JSON. The agent's answer is in the `"reply"` field.

---

## Where to Check Logs
*   Look at the terminal where you ran `uvicorn`.
*   You will see logs like:
    *   `INFO: Webhook received for session...`
    *   `INFO: Calculated scam level: suspected`
    *   `INFO: Session saved...`
