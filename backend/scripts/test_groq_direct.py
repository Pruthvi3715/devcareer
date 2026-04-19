"""Direct Groq API test — no pipeline, just one LLM call."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from services.claude_engine import _get_client, get_llm_model, get_llm_provider

print("Provider:", get_llm_provider())
print("Model:", get_llm_model())

client = _get_client()
if not client:
    print("ERROR: No client created. Check API key.")
    sys.exit(1)

print("Client OK. Making test call...")
try:
    r = client.chat.completions.create(
        model=get_llm_model(),
        messages=[{"role": "user", "content": 'Respond with only this JSON: {"status":"ok"}'}],
        max_tokens=50,
    )
    print("SUCCESS:", r.choices[0].message.content)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
