"""İlaç takibi uç noktaları - Android MedicineDao/MedicineRepository ile eşleşir (Grup 5)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medicine import Medicine
from app.models.pet import Pet
from app.models.user import User
from app.schemas.medicine import MedicineCreate, MedicineResponse, MedicineUpdate
from app.security.dependencies import get_current_user
from app.services.pet_service import get_owned_pet_or_404

router = APIRouter(prefix="/medicines", tags=["İlaçlar"])


@router.get("", response_model=list[MedicineResponse])
def list_medicines(
    pet_id: str | None = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Medicine]:
    query = db.query(Medicine).join(Pet).filter(Pet.owner_id == current_user.id)
    if pet_id is not None:
        get_owned_pet_or_404(db, pet_id, current_user)
        query = query.filter(Medicine.pet_id == pet_id)
    if active_only:
        query = query.filter(Medicine.is_active.is_(True))
    return query.order_by(Medicine.next_dose.asc()).all()


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(
    data: MedicineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    medicine = Medicine(**data.model_dump(exclude_none=True))
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_id: str,
    data: MedicineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    medicine = _get_owned_medicine_or_404(db, medicine_id, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(medicine, field, value)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(
    medicine_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    medicine = _get_owned_medicine_or_404(db, medicine_id, current_user)
    db.delete(medicine)
    db.commit()


def _get_owned_medicine_or_404(db: Session, medicine_id: str, current_user: User) -> Medicine:
    medicine = (
        db.query(Medicine)
        .join(Pet)
        .filter(Medicine.id == medicine_id, Pet.owner_id == current_user.id)
        .first()
    )
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İlaç kaydı bulunamadı.")
    return medicine
