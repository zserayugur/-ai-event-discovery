from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import Envelope, UserOut, UserUpdateIn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=Envelope[UserOut])
def get_me(user: User = Depends(get_current_user)):
    return Envelope(data=UserOut.model_validate(user))


@router.put("/me", response_model=Envelope[UserOut])
def update_me(body: UserUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return Envelope(data=UserOut.model_validate(user))
