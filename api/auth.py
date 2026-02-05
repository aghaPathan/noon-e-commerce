"""
JWT Authentication for Noon-E-Commerce API
Phase 3: Backend Authentication

Uses passlib for password hashing and python-jose for JWT.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

# ============================================
# Configuration
# ============================================

JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. Set it before starting the application.")
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_MINUTES = int(os.environ.get('JWT_EXPIRY_MINUTES', '30'))
REFRESH_TOKEN_EXPIRY_DAYS = int(os.environ.get('REFRESH_TOKEN_EXPIRY_DAYS', '7'))

# Password hashing context (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


# ============================================
# Pydantic Schemas
# ============================================

class UserCreate(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class UserResponse(BaseModel):
    """User profile response"""
    id: int
    email: str
    full_name: Optional[str] = None
    role: str = 'user'
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """Decoded JWT token payload"""
    sub: str  # user_id
    email: Optional[str] = None
    role: str = 'user'
    exp: Optional[datetime] = None
    type: str = 'access'  # 'access' or 'refresh'


# ============================================
# Password Utilities
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt via passlib"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash.
    
    Note: Legacy SHA256 fallback removed for security (rainbow table vulnerability).
    Users with old hashes must reset their password.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Don't fall back to insecure hash verification
        return False


# ============================================
# JWT Utilities
# ============================================

def create_access_token(user_id: str, email: str, role: str = 'user') -> str:
    """Create JWT access token"""
    expires = datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {
        'sub': str(user_id),
        'email': email,
        'role': role,
        'exp': expires,
        'type': 'access'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, email: str = None, role: str = 'user') -> str:
    """Create JWT refresh token"""
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
    payload = {
        'sub': str(user_id),
        'email': email,
        'role': role,
        'exp': expires,
        'type': 'refresh'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_tokens(user_id: str, email: str, role: str = 'user') -> TokenResponse:
    """Create both access and refresh tokens"""
    access_token = create_access_token(user_id, email, role)
    refresh_token = create_refresh_token(user_id, email, role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=JWT_EXPIRY_MINUTES * 60
    )


# ============================================
# Authentication Dependencies
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    Get current user from JWT token.
    Use as dependency: current_user: TokenPayload = Depends(get_current_user)
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    
    if payload.get('type') != 'access':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token type (expected access token)',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    
    return TokenPayload(**payload)


async def get_current_admin(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """
    Require admin privileges.
    Use as dependency: admin: TokenPayload = Depends(get_current_admin)
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin privileges required'
        )
    return current_user


# Optional: Get user if token provided, None otherwise
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[TokenPayload]:
    """
    Get current user if token provided, None otherwise.
    Useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    if not payload or payload.get('type') != 'access':
        return None
    
    return TokenPayload(**payload)
