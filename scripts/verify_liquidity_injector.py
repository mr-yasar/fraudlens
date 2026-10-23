"""
Verify Demo Liquidity Injection (5, 10, 20 Lakhs) and Reset across all 4 customer accounts.
"""

import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_liquidity_verification():
    print("=== TESTING DEMO LIQUIDITY INJECTOR (5L, 10L, 20L) ACROSS ALL ACCOUNTS ===")
    
    users = [
        {"email": "monisha@fraudlens.ai", "cid": "CUST_MONISHA_001", "base": 45000.0},
        {"email": "mohana@fraudlens.ai", "cid": "CUST_MOHANA_002", "base": 60000.0},
        {"email": "sowmiya@fraudlens.ai", "cid": "CUST_SOWMIYA_003", "base": 80000.0},
        {"email": "ajay@fraudlens.ai", "cid": "CUST_AJAY_004", "base": 300000.0},
    ]

    for u in users:
        print(f"\n--- Testing Account: {u['cid']} ({u['email']}) ---")
        login_req = urllib.request.Request(
            f"{BASE_URL}/auth/login",
            data=json.dumps({"email": u["email"], "password": "Customer@1234"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        token = json.loads(urllib.request.urlopen(login_req).read().decode())["access_token"]
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        # 1. Test 5 Lakhs Injection
        req_5l = urllib.request.Request(
            f"{BASE_URL}/payment/wallet/{u['cid']}/liquidity",
            data=json.dumps({"amount": 500000.0, "action": "SET"}).encode(),
            headers=headers
        )
        res_5l = json.loads(urllib.request.urlopen(req_5l).read().decode())
        assert res_5l["simulated_balance"] == 500000.0, f"Expected 500,000, got {res_5l['simulated_balance']}"
        print(f"  [OK] Injected 5 Lakhs: Simulated Balance = INR {res_5l['simulated_balance']:,.2f}")

        # Verify wallet endpoint reflects it
        req_w = urllib.request.Request(f"{BASE_URL}/payment/wallet/{u['cid']}", headers=headers)
        res_w = json.loads(urllib.request.urlopen(req_w).read().decode())
        assert res_w["available_balance"] == 500000.0, f"Wallet balance mismatch: {res_w['available_balance']}"

        # 2. Test 10 Lakhs Injection
        req_10l = urllib.request.Request(
            f"{BASE_URL}/payment/wallet/{u['cid']}/liquidity",
            data=json.dumps({"amount": 1000000.0, "action": "SET"}).encode(),
            headers=headers
        )
        res_10l = json.loads(urllib.request.urlopen(req_10l).read().decode())
        assert res_10l["simulated_balance"] == 1000000.0, f"Expected 1,000,000, got {res_10l['simulated_balance']}"
        print(f"  [OK] Injected 10 Lakhs: Simulated Balance = INR {res_10l['simulated_balance']:,.2f}")

        # 3. Test 20 Lakhs Injection
        req_20l = urllib.request.Request(
            f"{BASE_URL}/payment/wallet/{u['cid']}/liquidity",
            data=json.dumps({"amount": 2000000.0, "action": "SET"}).encode(),
            headers=headers
        )
        res_20l = json.loads(urllib.request.urlopen(req_20l).read().decode())
        assert res_20l["simulated_balance"] == 2000000.0, f"Expected 2,000,000, got {res_20l['simulated_balance']}"
        print(f"  [OK] Injected 20 Lakhs: Simulated Balance = INR {res_20l['simulated_balance']:,.2f}")

        # 4. Test Reset to Baseline Limit
        req_reset = urllib.request.Request(
            f"{BASE_URL}/payment/wallet/{u['cid']}/liquidity",
            data=json.dumps({"amount": 0.0, "action": "RESET"}).encode(),
            headers=headers
        )
        res_reset = json.loads(urllib.request.urlopen(req_reset).read().decode())
        assert res_reset["simulated_balance"] == u["base"], f"Expected reset to {u['base']}, got {res_reset['simulated_balance']}"
        print(f"  [OK] Reset to Baseline: Simulated Balance = INR {res_reset['simulated_balance']:,.2f} (Cleanly restored)")

    print("\nALL 4 CUSTOMER ACCOUNTS PASSED DEMO LIQUIDITY INJECTION (5L, 10L, 20L) & RESET VERIFICATION!")

if __name__ == "__main__":
    run_liquidity_verification()
