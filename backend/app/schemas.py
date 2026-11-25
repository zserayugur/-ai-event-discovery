from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """Başarılı yanıt formatı: { "data": ... } (docs/api-contract.md)."""

    data: T


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    district: str | None
    onboarding_done: bool
    created_at: datetime


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)


class AuthOut(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
