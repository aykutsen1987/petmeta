"""
Mama / Su / Egzersiz / Kilo kayıt uç noktaları (Grup 5-6).

Bu dört kaynak da aynı basit CRUD desenini (pet_id'ye göre listele, oluştur, sil)
izlediğinden, tek bir dosyada dört ayrı APIRouter olarak tanımlanır ve
`app.main` içinde ayrı prefix'lerle (/food, /water, /exercise, /weight) bağlanır.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.exercise_log import ExerciseLog
from app.models.food_log import FoodLog
from app.models.pet import Pet
from app.models.user import User
from app.models.water_log import WaterLog
from app.models.weight_log import WeightLog
from app.schemas.logs import (
    ExerciseLogCreate,
    ExerciseLogResponse,
    FoodLogCreate,
    FoodLogResponse,
    WaterLogCreate,
    WaterLogResponse,
    WeightLogCreate,
    WeightLogResponse,
)
from app.security.dependencies import get_current_user
from app.services.pet_service import get_owned_pet_or_404

food_router = APIRouter(prefix="/food", tags=["Mama"])
water_router = APIRouter(prefix="/water", tags=["Su"])
exercise_router = APIRouter(prefix="/exercise", tags=["Egzersiz"])
weight_router = APIRouter(prefix="/weight", tags=["Kilo"])


def _require_owned_log(db: Session, model, log_id: str, current_user: User, not_found_message: str):
    record = db.query(model).join(Pet).filter(model.id == log_id, Pet.owner_id == current_user.id).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message)
    return record


# ---------- Mama (Food) ----------


@food_router.get("", response_model=list[FoodLogResponse])
def list_food_logs(
    pet_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[FoodLog]:
    get_owned_pet_or_404(db, pet_id, current_user)
    return db.query(FoodLog).filter(FoodLog.pet_id == pet_id).order_by(FoodLog.logged_at.desc()).all()


@food_router.post("", response_model=FoodLogResponse, status_code=status.HTTP_201_CREATED)
def create_food_log(
    data: FoodLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FoodLog:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    log = FoodLog(**data.model_dump(exclude_none=True))
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@food_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food_log(
    log_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    log = _require_owned_log(db, FoodLog, log_id, current_user, "Mama kaydı bulunamadı.")
    db.delete(log)
    db.commit()


# ---------- Su (Water) ----------


@water_router.get("", response_model=list[WaterLogResponse])
def list_water_logs(
    pet_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[WaterLog]:
    get_owned_pet_or_404(db, pet_id, current_user)
    return db.query(WaterLog).filter(WaterLog.pet_id == pet_id).order_by(WaterLog.logged_at.desc()).all()


@water_router.post("", response_model=WaterLogResponse, status_code=status.HTTP_201_CREATED)
def create_water_log(
    data: WaterLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WaterLog:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    log = WaterLog(**data.model_dump(exclude_none=True))
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@water_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_water_log(
    log_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    log = _require_owned_log(db, WaterLog, log_id, current_user, "Su kaydı bulunamadı.")
    db.delete(log)
    db.commit()


# ---------- Egzersiz (Exercise) ----------


@exercise_router.get("", response_model=list[ExerciseLogResponse])
def list_exercise_logs(
    pet_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ExerciseLog]:
    get_owned_pet_or_404(db, pet_id, current_user)
    return db.query(ExerciseLog).filter(ExerciseLog.pet_id == pet_id).order_by(ExerciseLog.logged_at.desc()).all()


@exercise_router.post("", response_model=ExerciseLogResponse, status_code=status.HTTP_201_CREATED)
def create_exercise_log(
    data: ExerciseLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ExerciseLog:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    log = ExerciseLog(**data.model_dump(exclude_none=True))
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@exercise_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_log(
    log_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    log = _require_owned_log(db, ExerciseLog, log_id, current_user, "Egzersiz kaydı bulunamadı.")
    db.delete(log)
    db.commit()


# ---------- Kilo (Weight) ----------


@weight_router.get("", response_model=list[WeightLogResponse])
def list_weight_logs(
    pet_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[WeightLog]:
    get_owned_pet_or_404(db, pet_id, current_user)
    return db.query(WeightLog).filter(WeightLog.pet_id == pet_id).order_by(WeightLog.measured_at.asc()).all()


@weight_router.post("", response_model=WeightLogResponse, status_code=status.HTTP_201_CREATED)
def create_weight_log(
    data: WeightLogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WeightLog:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    log = WeightLog(**data.model_dump(exclude_none=True))
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@weight_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight_log(
    log_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    log = _require_owned_log(db, WeightLog, log_id, current_user, "Kilo kaydı bulunamadı.")
    db.delete(log)
    db.commit()
