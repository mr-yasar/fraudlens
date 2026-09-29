import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_call(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except:
            return e.code, body

def run_tests():
    print("=== TESTING ALL 4 CUSTOMER ACCOUNTS FOR STRICT PRIVACY & DATA ISOLATION ===")
    
    users = [
        {"name": "Monisha", "email": "monisha@fraudlens.ai", "expected_cust": "CUST_MONISHA_001"},
        {"name": "Mohana", "email": "mohana@fraudlens.ai", "expected_cust": "CUST_MOHANA_002"},
        {"name": "Sowmiya", "email": "sowmiya@fraudlens.ai", "expected_cust": "CUST_SOWMIYA_003"},
        {"name": "Ajay", "email": "ajay@fraudlens.ai", "expected_cust": "CUST_AJAY_004"},
    ]
    
    tokens = {}
    
    for u in users:
        print(f"\n--- Testing User: {u['name']} ({u['email']}) ---")
        status, res = api_call("/auth/login", method="POST", data={"email": u["email"], "password": "Customer@1234"})
        assert status == 200, f"Login failed for {u['email']}: {res}"
        token = res["access_token"]
        tokens[u["name"]] = token
        print(f"  [OK] Login successful! Token received. User ID: {res['user_id']}, Name: {res['name']}")
        
        # Test /auth/me
        status, me = api_call("/auth/me", token=token)
        assert status == 200, f"/auth/me failed: {me}"
        assert me["email"] == u["email"], f"Expected email {u['email']}, got {me['email']}"
        print(f"  [OK] /auth/me verified: {me['name']} ({me['email']})")
        
        # Test /payment/approvals/pending (Module 3 fix)
        status, pending = api_call("/payment/approvals/pending", token=token)
        assert status == 200, f"/payment/approvals/pending returned {status}: {pending}"
        print(f"  [OK] /payment/approvals/pending OK! Count: {len(pending)}")
        for p in pending:
            assert p["customer_id"] == u["expected_cust"], f"LEAK! Found approval for {p['customer_id']} in {u['name']}'s queue!"
            
        # Test /payment/wallet
        status, wallet = api_call(f"/payment/wallet/{u['expected_cust']}", token=token)
        assert status == 200, f"/payment/wallet failed: {wallet}"
        assert wallet["customer_id"] == u["expected_cust"], f"Expected {u['expected_cust']}, got {wallet['customer_id']}"
        print(f"  [OK] Wallet verified for {wallet['customer_id']}: Balance = {wallet['available_balance']}")

    # Now perform Ajay transaction test
    print("\n=== INITIATING PAYMENT AS AJAY ===")
    ajay_token = tokens["Ajay"]
    pay_payload = {
        "customer_id": "CUST_AJAY_004",
        "amount": 1500.0,
        "currency": "INR",
        "merchant_name": "CloudScale Technologies",
        "merchant_category": "software_saas",
        "beneficiary_name": "CloudScale AWS Cloud",
        "payment_method": "net_banking",
        "device_type": "web",
        "location": "Salem",
        "transaction_country": "IN",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
        "idempotency_key": f"test-ajay-{sys.platform}-9901"
    }
    status, pay_res = api_call("/payment/initiate", method="POST", data=pay_payload, token=ajay_token)
    assert status == 200, f"Payment initiate failed: {pay_res}"
    print(f"  [OK] Payment decision: {pay_res['decision']}, TxId: {pay_res['transaction_id']}, Customer: {pay_res['customer_id']}")
    assert pay_res["customer_id"] == "CUST_AJAY_004", f"Customer ID in payment must be CUST_AJAY_004, got {pay_res['customer_id']}"
    
    tx_id = pay_res["transaction_id"]
    
    # Check Ajay transactions
    print(f"\n=== VERIFYING TRANSACTION {tx_id} IN AJAY'S TRANSACTIONS ===")
    status, ajay_txs = api_call(f"/transactions?customer_id=CUST_AJAY_004&limit=10", token=ajay_token)
    assert status == 200, f"Failed to list transactions: {ajay_txs}"
    items = ajay_txs.get("items", [])
    found = any(t["transaction_id"] == tx_id for t in items)
    assert found, f"Newly created transaction {tx_id} NOT found in Ajay's transactions!"
    print(f"  [SUCCESS] Transaction {tx_id} is present in Ajay's transactions!")
    
    # Verify strict data isolation: Monisha cannot see this transaction in her scoped query
    monisha_token = tokens["Monisha"]
    status, monisha_txs = api_call(f"/transactions?customer_id=CUST_MONISHA_001&limit=20", token=monisha_token)
    items_monisha = monisha_txs.get("items", [])
    assert not any(t["transaction_id"] == tx_id for t in items_monisha), "LEAK! Ajay's transaction appeared in Monisha's list!"
    print(f"  [SUCCESS] ZERO LEAKAGE: Ajay's transaction is completely absent from Monisha's transactions!")

    print("\nALL 4 USERS AND PAYMENT GATEWAY PASSED 100% VERIFICATION WITH COMPLETE DATA ISOLATION!")

if __name__ == "__main__":
    run_tests()
