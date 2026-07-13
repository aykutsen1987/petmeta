"""Kimlik doğrulama şemaları - Android RegisterRequestDto/LoginRequestDto/AuthResponseDto ile eşleşir."""
from pydantic import EmailStr, Field

from app.schemas.base import CamelModel


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class RefreshRequest(CamelModel):
    """
    NOT: Android tarafında `refreshToken(@Body refreshToken: String)` şeklinde
    ham bir String gönderilir; FastAPI tarafında bunu bir JSON string body
    (`"eyJhbGciOi..."`) olarak almak için router seviyesinde `Body(embed=False)`
    kullanılır (bkz. routers/auth.py). Bu şema, aynı zamanda `{"refreshToken": "..."}`
    biçiminde bir JSON nesnesi gönderen istemcileri de desteklemek için mevcuttur.
    """

    refresh_token: str


class AuthResponse(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
