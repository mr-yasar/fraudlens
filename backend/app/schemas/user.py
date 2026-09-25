"""Pydantic schemas for authentication and user management."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """System RBAC roles: Customer/User and Fraud Investigator/Admin."""
    CUSTOMER = "CUSTOMER"
    USER = "USER"
    FRAUD_INVESTIGATOR = "FRAUD_INVESTIGATOR"
    ADMIN = "ADMIN"


class Token(BaseModel):
    """JWT Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: int
    email: str
    name: str
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v):
        if isinstance(v, UserRole):
            return v
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ("ADMIN", "SUPERADMIN"):
                return UserRole.ADMIN
            if v_upper in ("FRAUD_INVESTIGATOR", "INVESTIGATOR", "ANALYST"):
                return UserRole.FRAUD_INVESTIGATOR
            if v_upper in ("USER",):
                return UserRole.USER
            return UserRole.CUSTOMER
        return UserRole.CUSTOMER


class TokenPayload(BaseModel):
    """Decoded JWT payload schema."""
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserBase(BaseModel):
    """Shared user properties."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v):
        if isinstance(v, UserRole):
            return v
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ("ADMIN", "SUPERADMIN"):
                return UserRole.ADMIN
            if v_upper in ("FRAUD_INVESTIGATOR", "INVESTIGATOR", "ANALYST"):
                return UserRole.FRAUD_INVESTIGATOR
            if v_upper in ("USER",):
                return UserRole.USER
            return UserRole.CUSTOMER
        return UserRole.CUSTOMER


class UserRegister(BaseModel):
    """Customer self-registration payload."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = UserRole.CUSTOMER


class UserCreate(UserBase):
    """User creation schema (Admin only)."""
    password: str = Field(..., min_length=8)



class UserUpdate(BaseModel):
    """User update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserOut(UserBase):
    """Public user profile schema (safe, no password hashes)."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
