"""Kimlik Doğrulama Servis Katmanı - kullanıcı kaydı, giriş ve token üretimi."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.security.hashing import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token


def register_user(db: Session, data: RegisterRequest) -> User:
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta adresiyle zaten kayıtlı bir kullanıcı var.",
        )

    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: LoginRequest) -> User:
    user = db.query(User).filter(User.email == data.email.lower()).first()
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-posta veya parola hatalı.",
    )
    if user is None or not verify_password(data.password, user.hashed_password):
        raise invalid_credentials
    return user


def build_auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
    )
