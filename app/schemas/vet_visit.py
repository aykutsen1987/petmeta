"""Veteriner ziyareti şemaları - Android VetEntity ile alan bazında eşleşir."""
from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class VetVisitBase(CamelModel):
    clinic_name: str = Field(min_length=1, max_length=150)
    vet_name: str | None = None
    visit_date: datetime
    reason: str | None = None
    diagnosis: str | None = None
    prescription: str | None = None
    cost: float | None = None
    next_appointment: datetime | None = None
    notes: str | None = None


class VetVisitCreate(VetVisitBase):
    pet_id: str


class VetVisitUpdate(CamelModel):
    clinic_name: str | None = None
    vet_name: str | None = None
    visit_date: datetime | None = None
    reason: str | None = None
    diagnosis: str | None = None
    prescription: str | None = None
    cost: float | None = None
    next_appointment: datetime | None = None
    notes: str | None = None


class VetVisitResponse(VetVisitBase):
    id: str
    pet_id: str
    created_at: datetime
