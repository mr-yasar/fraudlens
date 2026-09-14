"""Pydantic schemas for authentication and user management."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """System RBAC roles."""
    ADMIN = "ADMIN"
    FRAUD_INVESTIGATOR = "FRAUD_INVESTIGATOR"


class Token(BaseModel):
    """JWT Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: int
    email: str
    name: str
    role: UserRole


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
    role: UserRole = UserRole.FRAUD_INVESTIGATOR
    is_active: bool = True


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
