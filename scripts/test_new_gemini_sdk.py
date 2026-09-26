"""Quick test of the new google-genai SDK with the FraudLens Gemini adapter."""
import sys
import os
sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))
from dotenv import load_dotenv
load_dotenv(".env", override=True)

print("=== Testing new google-genai SDK ===")

# Test 1: Direct SDK call
from google import genai
from google.genai import types

key = os.getenv("GEMINI_API_KEY", "")
print(f"API Key present: {bool(key)}, length: {len(key)}")

client = genai.Client(api_key=key)
resp = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say: FraudLens AI is operational!",
    config=types.GenerateContentConfig(max_output_tokens=20),
)
print(f"Response: {resp.text}")
print("SUCCESS - Direct SDK test passed!")

# Test 2: Via the GeminiAdapter
print("\n=== Testing GeminiAdapter ===")
from backend.app.services.intelligence.gemini_adapter import GeminiAdapter

result, model_name = GeminiAdapter.generate(
    messages=[{"role": "user", "content": "Say: FraudLens is ready in 5 words!"}],
    system_instruction="You are FraudLens AI. Be very brief.",
    escalate_to_3_7=False,
    max_tokens=30,
)
print(f"Model used: {model_name}")
print(f"Response: {result}")
print("SUCCESS - GeminiAdapter test passed!")
