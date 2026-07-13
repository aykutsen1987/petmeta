"""İlaç şemaları - Android MedicineEntity ile alan bazında eşleşir."""
from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class MedicineBase(CamelModel):
    medicine_name: str = Field(min_length=1, max_length=150)
    dosage: str | None = None
    frequency_hours: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    next_dose: datetime | None = None
    is_active: bool = True
    notes: str | None = None


class MedicineCreate(MedicineBase):
    pet_id: str


class MedicineUpdate(CamelModel):
    medicine_name: str | None = None
    dosage: str | None = None
    frequency_hours: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    next_dose: datetime | None = None
    is_active: bool | None = None
    notes: str | None = None


class MedicineResponse(MedicineBase):
    id: str
    pet_id: str
