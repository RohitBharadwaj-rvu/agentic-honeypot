
import time
import asyncio
from openai import OpenAI
from app.agent.nodes.persona import PERSONA_SYSTEM_PROMPT

# Confirmed Keys from Screenshots (Type: TV9v)
KEY1 = "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"
KEY2 = "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"

MODELS = [
    {"name": "Mistral Large 3", "id": "mistralai/mistral-large-3-675b-instruct-2512", "key": KEY1},
    {"name": "MiniMax-M2.1", "id": "minimaxai/minimax-m2.1", "key": KEY1},
    {"name": "Kimi k2.5", "id": "moonshotai/kimi-k2.5", "key": KEY1},
    {"name": "GLM 4.7", "id": "z-ai/glm4.7", "key": KEY2},
    {"name": "Step-1.5 16k", "id": "stepfun/step-1.5-16k", "key": KEY1}, 
]

async def run_benchmark():
    p_details = {
        "persona_name": "Ramesh Kumar", "persona_age": 67, "persona_location": "Pune",
        "persona_background": "retired SBI pension account holder", "persona_occupation": "Ex-Government Clerk",
        "persona_trait": "anxious and very polite", "fake_phone": "9876543210",
        "fake_upi": "ramesh@okaxis", "fake_bank_account": "123456789012", "fake_ifsc": "SBIN0001234"
    }

    print(f"\n{'Model':<18} | {'Lat (s)':<8} | {'Persona Snippet'}")
    print("-" * 85)

    for m in MODELS:
        client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=m["key"])
        prompt = PERSONA_SYSTEM_PROMPT.format(**p_details, phase_instruction="- INITIAL STAGE: Be curious.")
        
        start = time.time()
        try:
            res = client.chat.completions.create(
                model=m["id"],
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": "Hello who are you?"}],
                temperature=0.7, max_tokens=100
            )
            lat = time.time() - start
            text = res.choices[0].message.content.strip().replace('\n', ' ')
            print(f"{m['name']:<18} | {lat:<8.2f} | {text[:60]}...")
        except Exception as e:
            print(f"{m['name']:<18} | ERROR    | {str(e)[:60]}...")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
