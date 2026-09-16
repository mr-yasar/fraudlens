"""Authentication and User Management Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserRole,
    Token,
    LoginRequest,
    UserCreate,
    UserOut,
)
from backend.app.api.deps import get_current_active_user, require_admin

from backend.app.core.rate_limiter import rate_limit

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
    description="Authenticate with email and password to receive a JWT access token.",
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Validate credentials and issue JWT bearer token."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    # Standardize role string
    user_role = UserRole.ADMIN if user.role.upper() == "ADMIN" else UserRole.FRAUD_INVESTIGATOR
    access_token = create_access_token(
        subject=user.id,
        role=user_role.value,
        extra_claims={"email": user.email, "name": user.name},
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=user_role,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Current User Profile",
    description="Fetch profile of the currently authenticated user (no password hash exposed).",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    return current_user


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create User (Admin Only)",
    description="Create a new system user with specific RBAC role. Restricted to ADMIN.",
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> UserOut:
    """Register a new user account (Admin restricted)."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.value,
        is_active=user_in.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/users",
    response_model=List[UserOut],
    summary="List Users (Admin Only)",
    description="Retrieve all registered users. Restricted to ADMIN.",
)
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> List[UserOut]:
    """List all users in the system."""
    return db.query(User).all()
