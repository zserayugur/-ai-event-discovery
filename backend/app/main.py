from fastapi import FastAPI

from app.api.routes import auth, users
from app.core.errors import register_error_handlers
from app.database import Base, engine
import app.models  # noqa: F401  (tabloların Base'e kaydolması için)

# Alembic eklenene kadar tablolar uygulama açılırken oluşturulur.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ankara Etkinlik Platformu API")
register_error_handlers(app)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"data": {"status": "ok"}}
