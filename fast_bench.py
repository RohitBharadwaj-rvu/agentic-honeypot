
import time
import asyncio
from openai import OpenAI
from app.agent.nodes.persona import PERSONA_SYSTEM_PROMPT

K1 = "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"
K2 = "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"

MODELS = [
    {"name": "MiniMax", "id": "minimaxai/minimax-m2.1", "key": K1},
    {"name": "GLM 4.7", "id": "z-ai/glm4.7", "key": K2},
    {"name": "Step 3.5", "id": "stepfun/step-1.5-16k", "key": K1},
    {"name": "Mistral", "id": "mistralai/mistral-large-3-675b-instruct-2512", "key": K1}
]

async def fast_bench():
    p_details = {
        "persona_name": "Ramesh Kumar", "persona_age": 67, "persona_location": "Pune",
        "persona_background": "retired SBI pension account holder", "persona_occupation": "Ex-Government Clerk",
        "persona_trait": "anxious and very polite", "fake_phone": "9876543210",
        "fake_upi": "ramesh@okaxis", "fake_bank_account": "123456789012", "fake_ifsc": "SBIN0001234"
    }

    print(f"\n{'Model':<12} | {'Lat (s)':<8} | {'Snippet'}")
    print("-" * 60)

    for m in MODELS:
        client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=m["key"])
        prompt = PERSONA_SYSTEM_PROMPT.format(**p_details, phase_instruction="- INITIAL: Be curious.")
        start = time.time()
        try:
            res = client.chat.completions.create(
                model=m["id"],
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": "Hello sir"}],
                max_tokens=50
            )
            lat = time.time() - start
            text = res.choices[0].message.content.strip().replace('\n', ' ')
            print(f"{m['name']:<12} | {lat:<8.2f} | {text[:40]}...")
        except Exception as e:
            print(f"{m['name']:<12} | ERROR    | {str(e)[:40]}...")

if __name__ == "__main__":
    asyncio.run(fast_bench())
