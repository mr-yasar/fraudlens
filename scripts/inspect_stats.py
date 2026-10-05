import urllib.request
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.core.security import create_access_token

token = create_access_token(subject="1", role="admin")
req = urllib.request.Request("http://127.0.0.1:8000/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
res = urllib.request.urlopen(req)
data = json.loads(res.read())

print("Total transactions:", data.get("total_transactions"))
print("High risk:", data.get("high_risk_transactions"))
print("Med risk:", data.get("medium_risk_transactions"))
print("Low risk:", data.get("low_risk_transactions"))
print("Risk distribution:", data.get("risk_distribution"))
print("\nTransaction type risk count:", len(data.get("transaction_type_risk", [])))
for r in data.get("transaction_type_risk", []):
    print(" ", r)

print("\nDevice risk count:", len(data.get("device_risk", [])))
for r in data.get("device_risk", []):
    print(" ", r)
