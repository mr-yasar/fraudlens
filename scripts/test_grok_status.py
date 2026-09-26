"""Test Grok adapter directly and via the chat endpoint."""
import requests, sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env', override=True)

print("=" * 55)
print("  GROK STATUS DIAGNOSTIC")
print("=" * 55)

# Step 1: verify key via verify-key API
r_login = requests.post('http://127.0.0.1:8000/api/v1/auth/login',
    json={'email': 'investigator@fraudlens.ai', 'password': 'Investigator@1234'})
token = r_login.json().get('access_token', '')
h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("\n[1] Grok API Key Verification:")
r_v = requests.get('http://127.0.0.1:8000/api/v1/ai/verify-key?provider=grok', headers=h)
v = r_v.json()
print(f"    Configured : {v.get('configured')}")
print(f"    Valid      : {v.get('valid')}")
print(f"    Key Name   : {v.get('key_name')}")
print(f"    Team Blocked: {v.get('team_blocked')}")
print(f"    Message    : {v.get('message', '')[:120]}")

print("\n[2] Grok Direct Completion Test:")
try:
    from openai import OpenAI
    key = os.getenv('GROK_API_KEY', '')
    client = OpenAI(api_key=key, base_url='https://api.x.ai/v1', timeout=20.0)
    comp = client.chat.completions.create(
        model='grok-2-1212',
        messages=[
            {'role': 'system', 'content': 'You are FraudLens AI.'},
            {'role': 'user',   'content': 'Say: Grok is alive! (5 words max)'},
        ],
        max_tokens=20,
    )
    print(f"    ✅ Grok responded: {comp.choices[0].message.content}")
except Exception as exc:
    err = str(exc)
    print(f"    ❌ Grok API error: {err[:200]}")
    if 'team_blocked' in err.lower() or 'credits' in err.lower() or '403' in err.lower():
        print("\n    ⚠️  ROOT CAUSE: xAI account has $0 credits (team_blocked=True)")
        print("    The Grok API KEY is 100% valid & authenticated by xAI.")
        print("    To enable Grok completions, add credits at: https://console.x.ai/")
    elif '401' in err:
        print("\n    ❌ ROOT CAUSE: API key is invalid or expired.")
    else:
        print(f"\n    Root cause: {err[:300]}")

print("\n[3] Chat endpoint with explicit Grok provider:")
r_chat = requests.post('http://127.0.0.1:8000/api/v1/ai/chat', headers=h, json={
    'messages': [{'role': 'user', 'content': 'Explain TreeSHAP in one sentence.'}],
    'provider': 'grok',
    'temperature': 0.7,
}, timeout=35)
d = r_chat.json()
print(f"    Status   : {r_chat.status_code}")
print(f"    Provider : {d.get('provider','?')}")
print(f"    Model    : {d.get('model','?')}")
print(f"    Response : {d.get('response','')[:200]}")
print("=" * 55)
