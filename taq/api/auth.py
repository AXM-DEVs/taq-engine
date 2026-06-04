from datetime import datetime, timedelta
from typing import Optional
import secrets
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taq.core.config import config
from taq.storage.connection import get_session
from taq.storage.models import UserModel, UserTier
from taq.core.auth_limiter import auth_rate_limiter

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security
security = HTTPBearer()


class UserRegister(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=8, example="secure_password_123")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="secure_password_123")


class UserResponse(BaseModel):
    id: str
    email: str
    tier: UserTier
    is_active: bool
    created_at: datetime
    api_key: str  # Only returned on creation/login


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def hash_password(password: str) -> str:
    """Hash a password for storing using bcrypt"""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_api_key() -> str:
    """Generate a secure random API key"""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    try:
        from jose import jwt
        SECRET_KEY = getattr(config, 'secret_key', '') or secrets.token_urlsafe(32)
        ALGORITHM = "HS256"
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except ImportError:
        # Fallback for development - in production, python-jose should be installed
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        to_encode.update({"exp": expire})
        # Simple encoding for fallback (NOT secure for production)
        import base64
        import json
        data_str = json.dumps(to_encode)
        return f"fallback.{base64.b64encode(data_str.encode()).decode()}.{secrets.token_urlsafe(16)}"


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    """Register a new user"""
    # Check if user already exists
    result = await session.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    api_key = generate_api_key()
    hashed_password = hash_password(user_data.password) if user_data.password else None
    new_user = UserModel(
        email=user_data.email,
        api_key=api_key,
        hashed_password=hashed_password,
        tier=UserTier.FREE  # Default to free tier
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        tier=new_user.tier,
        is_active=bool(new_user.is_active),
        created_at=new_user.created_at,
        api_key=new_user.api_key
    )


@router.post("/login", response_model=UserResponse)
async def login_user(
    request: Request,
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """Login user (verify password and return API key)"""
    # Rate limiting by IP address
    client_ip = auth_rate_limiter.get_client_ip(request)
    if not auth_rate_limiter.is_allowed(f"login:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    result = await session.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password if provided and user has a password set
    if user_data.password is not None and user.hashed_password is not None:
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    elif user_data.password is not None and user.hashed_password is None:
        # User doesn't have password set but tried to authenticate with password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    # If no password provided, fall back to API key auth (existing behavior)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        tier=user.tier,
        is_active=bool(user.is_active),
        created_at=user.created_at,
        api_key=user.api_key
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
):
    """Get current user information"""
    token = credentials.credentials

    # Validate API key
    result = await session.execute(
        select(UserModel).where(
            UserModel.api_key == token,
            UserModel.is_active == 1
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        tier=user.tier,
        is_active=bool(user.is_active),
        created_at=user.created_at,
        api_key=user.api_key
    )


# Dependency to get current user (optional for free tier endpoints)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> Optional[UserModel]:
    """Get current user if authenticated, otherwise None (for free tier)"""
    if not credentials:
        return None

    token = credentials.credentials
    result = await session.execute(
        select(UserModel).where(
            UserModel.api_key == token,
            UserModel.is_active == 1
        )
    )
    return result.scalar_one_or_none()


# Dependency to get current user (required for premium tier endpoints)
async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> UserModel:
    """Get current user, required for premium endpoints"""
    token = credentials.credentials
    result = await session.execute(
        select(UserModel).where(
            UserModel.api_key == token,
            UserModel.is_active == 1
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user