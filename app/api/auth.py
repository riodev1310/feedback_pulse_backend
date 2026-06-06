from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db import User, get_db
from app.dependencies.auth import get_current_user
from app.schemas.auth import AuthSessionResponse, LoginRequest, RegisterRequest, UpdateProfileRequest, UserProfileResponse


router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    email = payload.email.lower().strip()
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    _set_auth_cookie(response, token)
    return AuthSessionResponse(message="Registered successfully.", user=user, access_token=token)


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(user.id)
    _set_auth_cookie(response, token)
    return AuthSessionResponse(message="Logged in successfully.", user=user, access_token=token)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    _clear_auth_cookie(response)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return current_user


@router.patch("/profile", response_model=AuthSessionResponse)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    current_user.full_name = payload.full_name.strip()
    current_user.organization = payload.organization.strip()
    current_user.job_title = payload.job_title.strip()
    current_user.bio = payload.bio.strip()
    current_user.avatar_url = payload.avatar_url.strip()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    token = create_access_token(current_user.id)
    return AuthSessionResponse(message="Profile updated successfully.", user=current_user, access_token=token)
