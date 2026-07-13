"""
Mama / Su / Egzersiz / Kilo kayıt şemaları.

Bu dört modül son derece basit "log" tablolarını temsil ettiğinden
(Android tarafında da FoodEntity/WaterEntity/ExerciseEntity/WeightEntity
birbirine çok benzer), tek bir dosyada gruplanmıştır.
"""
from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel

# ---------- Mama (Food) ----------


class FoodLogBase(CamelModel):
    food_name: str = Field(min_length=1, max_length=150)
    amount_grams: float = Field(gt=0)
    logged_at: datetime | None = None
    notes: str | None = None


class FoodLogCreate(FoodLogBase):
    pet_id: str


class FoodLogResponse(FoodLogBase):
    id: str
    pet_id: str
    logged_at: datetime


# ---------- Su (Water) ----------


class WaterLogBase(CamelModel):
    amount_ml: float = Field(gt=0)
    logged_at: datetime | None = None


class WaterLogCreate(WaterLogBase):
    pet_id: str


class WaterLogResponse(WaterLogBase):
    id: str
    pet_id: str
    logged_at: datetime


# ---------- Egzersiz (Exercise) ----------


class ExerciseLogBase(CamelModel):
    activity_type: str = Field(min_length=1, max_length=80)
    duration_minutes: int = Field(gt=0)
    estimated_calories: float = 0.0
    logged_at: datetime | None = None
    notes: str | None = None


class ExerciseLogCreate(ExerciseLogBase):
    pet_id: str


class ExerciseLogResponse(ExerciseLogBase):
    id: str
    pet_id: str
    logged_at: datetime


# ---------- Kilo (Weight) ----------


class WeightLogBase(CamelModel):
    weight_kg: float = Field(gt=0)
    measured_at: datetime | None = None
    notes: str | None = None


class WeightLogCreate(WeightLogBase):
    pet_id: str


class WeightLogResponse(WeightLogBase):
    id: str
    pet_id: str
    measured_at: datetime
