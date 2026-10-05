"""
Verification script for Dashboard Matrix Modals:
1. Risk Tier Classification Matrix
2. Channel & Device Anomaly Matrix
"""

import sys
from pathlib import Path

REPO_ROOT = Path(r"E:\fraudinvestigation")

def verify_dashboard_modals():
    dash_jsx = REPO_ROOT / "frontend" / "src" / "components" / "DashboardView.jsx"
    code = dash_jsx.read_text(encoding='utf-8')
    
    # 1. Verify Donut / Risk Tier modal handling
    assert "activeModal.type === 'DONUT'" in code, "DashboardView must handle DONUT modal type"
    assert "Risk Classification Matrix & Policy Enforcement" in code, "Must render Risk Tier matrix table"
    assert "activeModal.data.totalAssessed" in code, "Must dynamically bind totalAssessed"
    assert "activeModal.data.lowCount" in code, "Must dynamically bind lowCount"
    assert "activeModal.data.medCount" in code, "Must dynamically bind medCount"
    assert "activeModal.data.highCount" in code, "Must dynamically bind highCount"
    print("[PASSED] Risk Tier Classification Matrix modal body verified!")

    # 2. Verify Channel & Device Anomaly modal handling
    assert "activeModal.type === 'CHANNEL'" in code, "DashboardView must handle CHANNEL modal type"
    assert "Payment Channels (" in code, "Must render Payment Channels tab"
    assert "Device & Bot Signatures (" in code, "Must render Device & Bot Signatures tab"
    assert "highestRiskChannel" in code, "Must compute highest risk channel indicator"
    assert "highestRiskDevice" in code, "Must compute highest risk device signature indicator"
    assert "formatINR(c.total_volume" in code, "Must format financial volumes"
    assert "modalSearch" in code, "Must include instant search filter"
    print("[PASSED] Channel & Device Anomaly Matrix modal body verified!")

    return True

if __name__ == "__main__":
    if verify_dashboard_modals():
        print("\nALL DASHBOARD MODAL CHECKS PASSED!")
        sys.exit(0)
    else:
        sys.exit(1)
