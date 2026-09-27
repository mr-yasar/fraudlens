from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import get_password_hash

db = SessionLocal()
target_users = {
    'monisha@fraudlens.ai': 'Customer@1234',
    'mohana@fraudlens.ai': 'Customer@1234',
    'sowmiya@fraudlens.ai': 'Customer@1234',
    'customer@fraudlens.ai': 'Customer@1234',
    'customer@fraudlens.internal': 'Customer@1234',
    'user@fraudlens.ai': 'Customer@1234',
    'admin@fraudlens.internal': 'AdminSecure@2026!',
    'admin@fraudlens.ai': 'Admin@1234',
}

for email, pwd in target_users.items():
    u = db.query(User).filter(User.email == email).first()
    if u:
        u.password_hash = get_password_hash(pwd)
        print(f'Updated: {email} -> {pwd}')
    else:
        print(f'Not found: {email}')

db.commit()
print('\nAll user passwords updated successfully!')
