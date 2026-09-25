"""Authentication and User Management Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.schemas.user import (
    UserRole,
    Token,
    LoginRequest,
    UserCreate,
    UserRegister,
    UserOut,
)
from backend.app.api.deps import get_current_active_user, require_admin

from backend.app.core.rate_limiter import rate_limit

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Customer Self-Registration",
    description="Allows a new customer to register an account and immediately receive authentication credentials.",
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
def register(
    register_data: UserRegister,
    db: Session = Depends(get_db),
) -> Token:
    """Register a new customer account and create linked customer profile."""
    # Check if user with email already exists
    existing = db.query(User).filter(User.email == register_data.email.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in.",
        )

    # 1. Create User record
    assigned_role = UserRole.CUSTOMER.value
    new_user = User(
        name=register_data.name.strip(),
        email=register_data.email.strip().lower(),
        password_hash=get_password_hash(register_data.password),
        role=assigned_role,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    # 2. Create or link Customer profile
    cust_id = f"CUST-{new_user.id:04d}"
    existing_cust = db.query(Customer).filter(Customer.email == new_user.email).first()
    if not existing_cust:
        new_cust = Customer(
            customer_id=cust_id,
            name=new_user.name,
            email=new_user.email,
            simulated_balance=50000.0,
            currency="USD",
            account_age_days=30,
            risk_segment="Standard",
        )
        db.add(new_cust)

    db.commit()
    db.refresh(new_user)

    # 3. Issue Token for immediate login
    access_token = create_access_token(
        subject=new_user.id,
        role=UserRole.CUSTOMER.value,
        extra_claims={"email": new_user.email, "name": new_user.name},
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user_id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=UserRole.CUSTOMER,
    )


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
    user = db.query(User).filter(User.email == login_data.email.strip().lower()).first()
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

    # Standardize role string cleanly
    role_str = (user.role or "CUSTOMER").upper()
    if role_str == "ADMIN":
        user_role = UserRole.ADMIN
    elif role_str == "FRAUD_INVESTIGATOR":
        user_role = UserRole.FRAUD_INVESTIGATOR
    elif role_str == "USER":
        user_role = UserRole.USER
    else:
        user_role = UserRole.CUSTOMER

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
