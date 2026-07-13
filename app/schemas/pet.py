"""Evcil hayvan şemaları - Android PetDto ile alan bazında birebir eşleşir."""
from datetime import date, datetime

from pydantic import Field

from app.schemas.base import CamelModel


class PetBase(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    species: str = Field(min_length=1, max_length=50)
    breed: str | None = None
    color: str | None = None
    gender: str | None = None
    is_neutered: bool = False
    microchip_number: str | None = None
    birth_date: date | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
    owner_info: str | None = None
    notes: str | None = None
    photo_url: str | None = None


class PetCreate(PetBase):
    """POST /pets isteğinde kullanılır."""


class PetUpdate(PetBase):
    """PUT /pets/{id} isteğinde kullanılır (kısmi güncelleme için tüm alanlar opsiyoneldir)."""

    name: str | None = None
    species: str | None = None


class PetResponse(PetBase):
    id: str
    created_at: datetime
    updated_at: datetime
