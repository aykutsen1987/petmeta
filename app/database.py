"""
PetMeta Backend - Veritabanı Bağlantısı

SQLAlchemy engine ve Session yönetimini merkezileştirir. `DATABASE_URL`
"postgres://" ile başlıyorsa (Render/Heroku'nun eski biçimi), SQLAlchemy 1.4+
ile uyumlu olması için "postgresql://" biçimine dönüştürülür.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


_DATABASE_URL = _normalize_database_url(settings.database_url)

_connect_args: dict = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(_DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Tüm ORM modellerinin miras aldığı temel sınıf (bkz. app/models/*.py)."""


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection için kullanılan veritabanı oturumu üreticisi.
    İstek tamamlandığında (başarılı ya da hatalı) oturum her zaman kapatılır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
