"""
JWT üretim/çözümleme yardımcıları.

İki farklı token türü kullanılır:
- access_token: Kısa ömürlü (varsayılan 30 dk), her API isteğinde Authorization
  header'ında (Bearer) gönderilir.
- refresh_token: Uzun ömürlü (varsayılan 30 gün), yalnızca /auth/refresh
  endpoint'ine gönderilerek yeni bir access_token almak için kullanılır.

Her iki token da `sub` (subject = user id) ve `type` (access|refresh) claim'lerini
taşır; bu sayede bir refresh token'ın yanlışlıkla access token yerine kullanılması
(`type` kontrolü ile) engellenir.
"""
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from jose import JWTError, jwt

from app.config import settings


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    """Token süresi dolmuş, imzası geçersiz veya beklenmeyen bir türde olduğunda fırlatılır."""


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return _create_token(
        user_id, TokenType.ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        user_id, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: TokenType) -> str:
    """Token'ı çözer, türünü doğrular ve içindeki kullanıcı ID'sini (sub) döndürür."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Token çözümlenemedi veya süresi dolmuş.") from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"Beklenen token türü '{expected_type.value}' değil.")

    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Token içinde geçerli bir kullanıcı bilgisi bulunamadı.")

    return subject
