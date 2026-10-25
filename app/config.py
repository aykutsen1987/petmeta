"""
PetMeta Backend - Uygulama Ayarları

Tüm ortam değişkenleri (environment variables) bu modül üzerinden,
pydantic-settings kullanılarak tip güvenli şekilde okunur. Yerel geliştirmede
.env dosyası (bkz. .env.example) kullanılır; Render.com üzerinde ise bu
değerler Dashboard > Environment sekmesinden veya render.yaml üzerinden enjekte edilir.
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------- Genel ----------
    app_name: str = "PetMeta API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"  # development | production
    debug: bool = True

    # ---------- Veritabanı ----------
    # Yerelde SQLite, Render'da Postgres (DATABASE_URL Render tarafından otomatik sağlanır).
    database_url: str = "sqlite:///./petmeta.db"

    # ---------- JWT / Kimlik Doğrulama ----------
    secret_key: str = "CHANGE_ME_INSECURE_DEFAULT_SECRET_KEY"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # ---------- CORS ----------
    # Virgülle ayrılmış origin listesi, örn: "https://app.petmeta.com,http://localhost:3000"
    cors_allow_origins: str = "*"

    # ---------- Yapay Zekâ Analizi (Groq) ----------
    # NOT: Bu anahtar YALNIZCA backend'de tutulur; Android istemcisi asla erişemez.
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    groq_api_base_url: str = "https://api.groq.com/openai/v1"

    # ---------- Dosya Yükleme ----------
    max_upload_size_mb: int = 8
    upload_dir: str = "uploads"

    # ---------- Yapay Zekâ Analizi - Kötüye Kullanım Koruması ----------
    # Analiz endpoint'i artık hesap/giriş gerektirmediğinden (bkz. routers/analysis.py),
    # aynı IP adresinin günde en fazla kaç analiz isteği yapabileceğini sınırlar.
    # 0 veya negatif bir değer limiti tamamen devre dışı bırakır.
    analysis_daily_limit_per_ip: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        """Production'da güvensiz varsayılan JWT anahtarıyla açılmayı engeller."""
        if self.environment == "production" and (
            self.secret_key.startswith("CHANGE_ME") or len(self.secret_key) < 32
        ):
            raise ValueError("Production için güçlü bir SECRET_KEY tanımlanmalıdır (en az 32 karakter).")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Settings nesnesini süreç boyunca tek seferlik oluşturup önbelleğe alır."""
    return Settings()


settings = get_settings()
