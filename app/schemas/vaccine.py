"""Aşı şemaları - Android VaccineEntity ile alan bazında eşleşir."""
from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class VaccineBase(CamelModel):
    vaccine_name: str = Field(min_length=1, max_length=150)
    due_date: datetime
    administered_date: datetime | None = None
    is_completed: bool = False
    vet_clinic_name: str | None = None
    batch_number: str | None = None
    notes: str | None = None
    reminder_enabled: bool = True


class VaccineCreate(VaccineBase):
    pet_id: str


class VaccineUpdate(CamelModel):
    vaccine_name: str | None = None
    due_date: datetime | None = None
    administered_date: datetime | None = None
    is_completed: bool | None = None
    vet_clinic_name: str | None = None
    batch_number: str | None = None
    notes: str | None = None
    reminder_enabled: bool | None = None


class VaccineResponse(VaccineBase):
    id: str
    pet_id: str
    created_at: datetime
