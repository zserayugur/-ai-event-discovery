from datetime import datetime
from typing import Generic, Literal, TypeVar

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


# --- Kişiselleştirme ---

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class InterestOut(CategoryOut):
    weight: float


class InterestsIn(BaseModel):
    category_ids: list[int] = Field(min_length=1)


class EventSummaryOut(BaseModel):
    """Favori ve öneri listelerinde kullanılan kısa etkinlik formatı.
    Elifnaz /events için kendi formatını belirleyince buna uyarlanacak."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: CategoryOut
    start_date: datetime
    price: float | None
    image_url: str | None


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=5)


class RatingOut(BaseModel):
    event_id: int
    rating: int


class InteractionIn(BaseModel):
    event_id: int
    type: Literal["view", "click", "dismiss", "ticket_click"]


class PageMeta(BaseModel):
    total: int
    page: int
    limit: int


class PagedEnvelope(BaseModel, Generic[T]):
    data: T
    meta: PageMeta


class RecommendationOut(BaseModel):
    event: EventSummaryOut
    score: float
    reason: str
