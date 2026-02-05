
from openai import OpenAI
import time

def test_model(name, model_id, api_key):
    print(f"\n--- Testing {name} ({model_id}) ---")
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    
    start = time.time()
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hello"}],
            temperature=1,
            top_p=1,
            max_tokens=50,
            stream=True
        )
        
        content = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
                if len(content) > 50: break
        
        lat = time.time() - start
        print(f"Success! Latency: {lat:.2f}s")
        print(f"Response: {content[:100]}...")
        return lat
    except Exception as e:
        print(f"Failed: {e}")
        return None

# Keys
K1 = "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"
K2 = "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"

test_model("MiniMax", "minimaxai/minimax-m2.1", K1)
test_model("GLM 4.7", "z-ai/glm4.7", K2)
test_model("Mistral", "mistralai/mistral-large-3-675b-instruct-2512", K1)
