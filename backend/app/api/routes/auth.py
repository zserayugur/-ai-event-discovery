from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.schemas import AccessTokenOut, AuthOut, Envelope, LoginIn, RefreshIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_response(user: User) -> Envelope[AuthOut]:
    return Envelope(
        data=AuthOut(
            user=UserOut.model_validate(user),
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Envelope[AuthOut])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ApiError(409, "EMAIL_TAKEN", "Bu e-posta adresiyle zaten bir hesap var.")
    user = User(email=email, password_hash=hash_password(body.password), name=body.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_response(user)


@router.post("/login", response_model=Envelope[AuthOut])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "E-posta veya şifre hatalı.")
    return _auth_response(user)


@router.post("/refresh", response_model=Envelope[AccessTokenOut])
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    user_id = decode_token(body.refresh_token, "refresh")
    if user_id is None or db.get(User, user_id) is None:
        raise ApiError(401, "INVALID_TOKEN", "Oturum geçersiz veya süresi dolmuş.")
    return Envelope(data=AccessTokenOut(access_token=create_access_token(user_id)))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # JWT durumsuz olduğu için çıkışta istemci token'ları siler.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
