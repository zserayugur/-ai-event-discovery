"""Diğer ekiplerin de kullanacağı ortak bağımlılıklar.

Örnek (İrem - bildirimler):

    from app.api.deps import get_current_user

    @router.get("/notifications")
    def list_notifications(user: User = Depends(get_current_user)):
        ...

Giriş zorunlu değilse (örn. Elifnaz'ın /events listesi) get_optional_user kullanılabilir.
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import decode_token
from app.database import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if creds is None:
        return None
    user_id = decode_token(creds.credentials, "access")
    if user_id is None:
        raise ApiError(401, "INVALID_TOKEN", "Oturum geçersiz veya süresi dolmuş.")
    user = db.get(User, user_id)
    if user is None:
        raise ApiError(401, "INVALID_TOKEN", "Kullanıcı bulunamadı.")
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "Bu işlem için giriş yapmalısınız.")
    return user
