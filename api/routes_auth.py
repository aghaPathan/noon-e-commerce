"""
Authentication API Routes for Noon-E-Commerce
Phase 3: Backend Authentication

Endpoints:
- POST /api/auth/register - Register new user
- POST /api/auth/login - Login and get tokens
- POST /api/auth/refresh - Refresh access token
- GET /api/auth/me - Get current user profile
"""

import os
import time
from typing import Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import (
    UserCreate, UserLogin, RefreshRequest, TokenResponse, UserResponse,
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user, TokenPayload, JWT_EXPIRY_MINUTES
)

# ============================================
# Database Connection (direct for auth)
# ============================================

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# PostgreSQL configuration for noon_app
PG_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.environ.get('POSTGRES_PORT', '5433'))
PG_USER = os.environ.get('POSTGRES_USER', 'noon_user')
PG_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
PG_DATABASE = os.environ.get('POSTGRES_DB', 'noon_app')

if not PG_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD environment variable is required")


@contextmanager
def get_db():
    """Get database connection"""
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=PG_DATABASE,
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================
# Rate Limiting
# ============================================

limiter = Limiter(key_func=get_remote_address)

# Rate limit config (stricter for auth endpoints)
AUTH_RATE_LIMIT = os.environ.get('AUTH_RATE_LIMIT', '10/minute')
LOGIN_RATE_LIMIT = os.environ.get('LOGIN_RATE_LIMIT', '5/minute')


# ============================================
# User Database Operations
# ============================================

def get_user_by_email(email: str) -> Dict:
    """Get user by email"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, email, password_hash, full_name, role, is_active, created_at
            FROM users WHERE email = %s
        """, (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Dict:
    """Get user by ID"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, email, full_name, role, is_active, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(email: str, password_hash: str, full_name: str = None) -> Dict:
    """Create new user"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, role, is_active)
            VALUES (%s, %s, %s, 'user', true)
            RETURNING id, email, full_name, role, is_active, created_at
        """, (email, password_hash, full_name))
        return dict(cur.fetchone())


def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
        """, (user_id,))


# ============================================
# Router
# ============================================

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(request: Request, data: UserCreate):
    """
    Register a new user.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters
    - **full_name**: Optional display name
    """
    # Check if email exists
    existing = get_user_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
    password_hash = hash_password(data.password)
    user = create_user(data.email, password_hash, data.full_name)
    
    return UserResponse(**user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(request: Request, data: UserLogin):
    """
    Login and get JWT tokens.
    
    Returns access_token (30 min) and refresh_token (7 days).
    """
    user = get_user_by_email(data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    if not verify_password(data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    update_last_login(user['id'])
    
    # Generate tokens
    access_token = create_access_token(
        str(user['id']), user['email'], user['role']
    )
    refresh_token = create_refresh_token(
        str(user['id']), user['email'], user['role']
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=JWT_EXPIRY_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh_token(request: Request, data: RefreshRequest):
    """
    Refresh access token using refresh token.
    
    Returns new access_token and refresh_token.
    """
    payload = decode_token(data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    if payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user = get_user_by_id(int(payload['sub']))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Generate new tokens
    access_token = create_access_token(
        str(user['id']), user['email'], user['role']
    )
    new_refresh_token = create_refresh_token(
        str(user['id']), user['email'], user['role']
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=JWT_EXPIRY_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    """
    Get current user profile.
    
    Requires valid access token in Authorization header.
    """
    user = get_user_by_id(int(current_user.sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse(**user)
