from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.database import get_db
from app.models import User
from app.schemas import Envelope, EventSummaryOut, RecommendationOut
from app.services.recommender import recommend

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=Envelope[list[RecommendationOut]])
def get_recommendations(
    limit: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """'Senin için' listesi. Giriş yapılmamışsa popüler ve yakın tarihli etkinlikler döner."""
    items = recommend(db, user, limit)
    return Envelope(
        data=[
            RecommendationOut(event=EventSummaryOut.model_validate(r.event), score=r.score, reason=r.reason)
            for r in items
        ]
    )
