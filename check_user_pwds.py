from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import verify_password, get_password_hash

db = SessionLocal()
users = db.query(User).all()
test_pwds = ['customer123', 'Customer@1234', 'AdminSecure@2026!', 'admin123', 'admin', 'password', 'Admin@1234']

print("=== USER PASSWORDS CHECK ===")
for u in users:
    matched = []
    for p in test_pwds:
        if u.password_hash and verify_password(p, u.password_hash):
            matched.append(p)
    print(f"User id={u.id}, email={u.email}, role={u.role}, matched_pwds={matched}")
