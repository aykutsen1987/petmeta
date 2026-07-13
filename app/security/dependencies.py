"""
FastAPI Dependency'leri - İstek başına kimlik doğrulama.

`get_current_user`, korumalı (protected) her endpoint'te
`current_user: User = Depends(get_current_user)` şeklinde kullanılır.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security.jwt import InvalidTokenError, TokenType, decode_token

_bearer_scheme = HTTPBearer(auto_error=True, description="Access token'ı 'Bearer <token>' biçiminde gönderin.")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulanamadı. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user
