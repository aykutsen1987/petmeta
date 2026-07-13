"""Kimlik doğrulama uç noktaları - Android PetMetaApiService.register/login/refreshToken ile eşleşir."""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.security.jwt import InvalidTokenError, TokenType, create_access_token, create_refresh_token, decode_token
from app.services.auth_service import authenticate_user, build_auth_response, register_user

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = register_user(db, data)
    return build_auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(db, data)
    return build_auth_response(user)


@router.post("/refresh", response_model=AuthResponse)
def refresh(refresh_token: str = Body(..., embed=False), db: Session = Depends(get_db)) -> AuthResponse:
    """
    Android tarafında `refreshToken(@Body refreshToken: String)` şeklinde
    tanımlıdır; bu nedenle body doğrudan bir JSON string'dir (`"eyJhbGciOi..."`),
    bir nesne değil. `embed=False` bu ham string body'yi kabul etmek içindir.
    """
    try:
        user_id = decode_token(refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı.")

    return AuthResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
    )
