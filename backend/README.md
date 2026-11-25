# Backend

FastAPI + SQLAlchemy. Geliştirmede SQLite, ortak sunucuda PostgreSQL kullanılır.

## Kurulum

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # JWT_SECRET'ı değiştir
uvicorn app.main:app --reload
```

API dokümantasyonu: http://127.0.0.1:8000/docs

Testler: `pytest`

## Klasör yapısı

```
app/
├── main.py          # Uygulama, router'lar burada eklenir
├── database.py      # DB bağlantısı, Base, get_db
├── schemas.py       # İstek/yanıt modelleri
├── models/          # SQLAlchemy tabloları (her alan kendi dosyasını ekler)
├── core/            # Ayarlar, JWT/şifre, ortak hata formatı
└── api/
    ├── deps.py      # get_current_user, get_optional_user (herkes kullanabilir)
    └── routes/      # auth.py, users.py ... (events.py, search.py buraya eklenecek)
```

## Giriş gerektiren endpoint yazmak (Elifnaz, İrem)

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_optional_user
from app.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
def list_notifications(user: User = Depends(get_current_user)):
    ...  # token yoksa otomatik 401 UNAUTHORIZED döner
```

Giriş zorunlu değilse `get_optional_user` kullanın; kullanıcı yoksa `None` gelir.

Yanıtlar `{ "data": ... }`, hatalar `app.core.errors.ApiError` ile
`{ "error": { "code", "message" } }` formatında döner (bkz. `docs/api-contract.md`).

## Hazır endpoint'ler (Seray)

| Method | Endpoint |
|--------|----------|
| POST | `/api/auth/register` |
| POST | `/api/auth/login` |
| POST | `/api/auth/refresh` |
| POST | `/api/auth/logout` |
| GET / PUT | `/api/users/me` |
