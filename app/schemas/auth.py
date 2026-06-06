from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    organization: str
    job_title: str
    bio: str
    avatar_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(default="", max_length=255)
    organization: str = Field(default="", max_length=255)
    job_title: str = Field(default="", max_length=255)
    bio: str = Field(default="", max_length=4000)
    avatar_url: str = Field(default="", max_length=500)


class AuthSessionResponse(BaseModel):
    message: str
    user: UserProfileResponse
    access_token: str
    token_type: str = "bearer"
