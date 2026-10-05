import urllib.request
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.core.security import create_access_token

token = create_access_token(subject="1", role="admin")

tx_ids = ["PAY-5BC5F77D1626", "PAY-492D07210932", "PAY-88CD5A73D1B6", "TX-PREM-AA17BB0D"]

for tx_id in tx_ids:
    url = f"http://127.0.0.1:8000/api/v1/transactions/{tx_id}/explanation"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        pos_cnt = len(data.get("top_risk_increasing_factors", []))
        neg_cnt = len(data.get("top_risk_decreasing_factors", []))
        pred = data.get("prediction")
        risk = data.get("risk_score")
        print(f"[{tx_id}] STATUS {res.status} | Pred: {pred} | Risk: {risk} | PosFactors: {pos_cnt} | NegFactors: {neg_cnt}")
    except Exception as e:
        print(f"[{tx_id}] FAILED: {e}")
