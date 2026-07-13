"""
PetMeta Backend - FastAPI Uygulama Girişi

Bu dosya; uygulamayı oluşturur, CORS/middleware ayarlarını yapar, tüm
router'ları /api/v1 öneki altında bağlar ve (yalnızca ilk kurulum/geliştirme
kolaylığı için) veritabanı tablolarını otomatik oluşturur.

Çalıştırma (yerel):
    uvicorn app.main:app --reload

Çalıştırma (üretim, bkz. Procfile):
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import Base, engine
from app.routers import analysis, auth, logs, medicines, pets, vaccines, vet_visits

# app/models/__init__.py içindeki import zinciri, create_all'ın tüm tabloları
# görebilmesi için gereklidir (bkz. o dosyadaki açıklama).
from app import models  # noqa: F401

logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger("petmeta")

app = FastAPI(
    title=settings.app_name,
    description=(
        "PetMeta mobil uygulamasının backend API'si. Evcil hayvan profilleri, "
        "aşı/ilaç/veteriner takibi, mama/su/egzersiz/kilo kayıtları ve Groq "
        "destekli yapay zekâ fotoğraf analizi için uç noktalar sağlar."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """
    Basit kurulumlar (özellikle ücretsiz Render/SQLite ortamları) için tabloları
    otomatik oluşturur. Üretimde şema değişiklikleri için Alembic migration
    kullanılması önerilir; bu satır mevcut tabloları etkilemez (yalnızca eksik
    olanları oluşturur).

    NOT: Gunicorn birden fazla worker ile çalıştığında (bkz. Procfile/render.yaml),
    her worker kendi startup event'ini bağımsız çalıştırır. Bu da aynı anda
    birden fazla worker'ın "tablo var mı?" kontrolünü eş zamanlı yapıp
    hepsinin "yok" görüp CREATE TABLE denemesine (ve SQLite'ta
    "table already exists" hatasına) yol açabilir. Bu yarış durumunu (race
    condition) uygulamayı çökertmeden atlatmak için hatayı yakalayıp
    yalnızca logluyoruz; tablo zaten başka bir worker tarafından oluşturulmuş
    olur.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Veritabanı tabloları hazır (%s).", settings.database_url.split("://")[0])
    except OperationalError as exc:
        logger.warning(
            "Veritabanı tabloları oluşturulurken bir uyarı alındı (muhtemelen "
            "başka bir worker tarafından zaten oluşturuldu, göz ardı ediliyor): %s",
            exc,
        )


@app.get("/", tags=["Sağlık Kontrolü"])
def read_root() -> dict:
    return {"service": settings.app_name, "status": "ok", "environment": settings.environment}


@app.get("/health", tags=["Sağlık Kontrolü"])
def health_check() -> dict:
    return {"status": "ok"}


# ---------- Router Kayıtları (/api/v1 öneki ile) ----------

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(pets.router, prefix=settings.api_v1_prefix)
app.include_router(vaccines.router, prefix=settings.api_v1_prefix)
app.include_router(medicines.router, prefix=settings.api_v1_prefix)
app.include_router(vet_visits.router, prefix=settings.api_v1_prefix)
app.include_router(logs.food_router, prefix=settings.api_v1_prefix)
app.include_router(logs.water_router, prefix=settings.api_v1_prefix)
app.include_router(logs.exercise_router, prefix=settings.api_v1_prefix)
app.include_router(logs.weight_router, prefix=settings.api_v1_prefix)
app.include_router(analysis.router, prefix=settings.api_v1_prefix)
