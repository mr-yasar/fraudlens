"""End-to-end test of the AI chat endpoint."""
import requests, json, sys

# Login
r = requests.post('http://127.0.0.1:8000/api/v1/auth/login',
                  json={'email': 'investigator@fraudlens.ai', 'password': 'Investigator@1234'})
token = r.json().get('access_token', '')
print('Login:', 'OK' if token else f'FAIL ({r.text[:100]})')
if not token:
    sys.exit(1)

h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test AI chat
r2 = requests.post('http://127.0.0.1:8000/api/v1/ai/chat', headers=h, json={
    'messages': [{'role': 'user', 'content': 'What is FraudLens AI in 2 sentences?'}],
    'provider': None, 'temperature': 0.7,
}, timeout=30)
d = r2.json()
print(f'Status: {r2.status_code}')
print(f'Provider: {d.get("provider", "?")}')
print(f'Model: {d.get("model", "?")}')
print(f'Used Real API: {d.get("used_real_api", "?")}')
print(f'Routing: {d.get("routing", {})}')
print(f'Response preview: {d.get("response", "")[:200]}')
print('\nTest PASSED!' if r2.status_code == 200 else f'\nTest FAILED! Status: {r2.status_code}')
