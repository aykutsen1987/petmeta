"""Aşı takibi uç noktaları - Android VaccineDao/VaccineRepository ile eşleşir (Grup 4)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pet import Pet
from app.models.user import User
from app.models.vaccine import Vaccine
from app.schemas.vaccine import VaccineCreate, VaccineResponse, VaccineUpdate
from app.security.dependencies import get_current_user
from app.services.pet_service import get_owned_pet_or_404

router = APIRouter(prefix="/vaccines", tags=["Aşılar"])


@router.get("", response_model=list[VaccineResponse])
def list_vaccines(
    pet_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Vaccine]:
    """`pet_id` verilirse yalnızca o hayvanın aşıları, verilmezse kullanıcının TÜM hayvanlarının aşıları döner."""
    query = db.query(Vaccine).join(Pet).filter(Pet.owner_id == current_user.id)
    if pet_id is not None:
        get_owned_pet_or_404(db, pet_id, current_user)
        query = query.filter(Vaccine.pet_id == pet_id)
    return query.order_by(Vaccine.due_date.asc()).all()


@router.post("", response_model=VaccineResponse, status_code=status.HTTP_201_CREATED)
def create_vaccine(
    data: VaccineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vaccine:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    vaccine = Vaccine(**data.model_dump(exclude_none=True))
    db.add(vaccine)
    db.commit()
    db.refresh(vaccine)
    return vaccine


@router.put("/{vaccine_id}", response_model=VaccineResponse)
def update_vaccine(
    vaccine_id: str,
    data: VaccineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vaccine:
    vaccine = _get_owned_vaccine_or_404(db, vaccine_id, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vaccine, field, value)
    db.commit()
    db.refresh(vaccine)
    return vaccine


@router.delete("/{vaccine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vaccine(
    vaccine_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    vaccine = _get_owned_vaccine_or_404(db, vaccine_id, current_user)
    db.delete(vaccine)
    db.commit()


def _get_owned_vaccine_or_404(db: Session, vaccine_id: str, current_user: User) -> Vaccine:
    vaccine = (
        db.query(Vaccine)
        .join(Pet)
        .filter(Vaccine.id == vaccine_id, Pet.owner_id == current_user.id)
        .first()
    )
    if vaccine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aşı kaydı bulunamadı.")
    return vaccine
