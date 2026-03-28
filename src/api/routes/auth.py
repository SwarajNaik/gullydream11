"""Auth routes: register, login, refresh token."""

import bcrypt

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.dependencies.auth import create_access_token
from src.api.exceptions import ConflictException, UnauthorizedException
from src.api.schemas.common import APIResponse
from src.config import settings
from src.db.models import User, UserRole, Wallet
from src.db.session import get_session

router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --- Schemas ---


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    display_name: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    username: str
    display_name: str
    role: str


# --- Routes ---


@router.post("/register", response_model=APIResponse[AuthResponse], status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    """Register a new user with email and password."""
    # Check existing email
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalars().first():
        raise ConflictException("Email already registered")

    # Check existing username
    result = await session.execute(select(User).where(User.username == body.username))
    if result.scalars().first():
        raise ConflictException("Username already taken")

    # Determine role
    admin_emails = [e.strip() for e in settings.ADMIN_EMAILS.split(",")]
    role = UserRole.ADMIN if body.email in admin_emails else UserRole.USER

    # Create user
    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        phone=body.phone,
        role=role,
    )
    session.add(user)
    await session.flush()

    # Create wallet
    wallet = Wallet(user_id=user.id)
    session.add(wallet)
    await session.commit()
    await session.refresh(user)

    # Generate token
    token = create_access_token(user.id, user.email, user.role.value)

    return APIResponse(
        success=True,
        message="Registration successful",
        data=AuthResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            role=user.role.value,
        ),
    )


@router.post("/login", response_model=APIResponse[AuthResponse])
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Login with email/username and password."""
    # Find user by email or username
    result = await session.execute(
        select(User).where(
            (User.email == body.email_or_username) | (User.username == body.email_or_username)
        )
    )
    user = result.scalars().first()

    if not user or not verify_password(body.password, user.password_hash):
        raise UnauthorizedException("Invalid credentials")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    token = create_access_token(user.id, user.email, user.role.value)

    return APIResponse(
        success=True,
        message="Login successful",
        data=AuthResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            role=user.role.value,
        ),
    )
