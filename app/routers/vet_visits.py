"""Veteriner ziyareti uç noktaları - Android VetDao/VetRepository ile eşleşir (Grup 4)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pet import Pet
from app.models.user import User
from app.models.vet_visit import VetVisit
from app.schemas.vet_visit import VetVisitCreate, VetVisitResponse, VetVisitUpdate
from app.security.dependencies import get_current_user
from app.services.pet_service import get_owned_pet_or_404

router = APIRouter(prefix="/vet-visits", tags=["Veteriner Ziyaretleri"])


@router.get("", response_model=list[VetVisitResponse])
def list_vet_visits(
    pet_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[VetVisit]:
    query = db.query(VetVisit).join(Pet).filter(Pet.owner_id == current_user.id)
    if pet_id is not None:
        get_owned_pet_or_404(db, pet_id, current_user)
        query = query.filter(VetVisit.pet_id == pet_id)
    return query.order_by(VetVisit.visit_date.desc()).all()


@router.post("", response_model=VetVisitResponse, status_code=status.HTTP_201_CREATED)
def create_vet_visit(
    data: VetVisitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VetVisit:
    get_owned_pet_or_404(db, data.pet_id, current_user)
    visit = VetVisit(**data.model_dump(exclude_none=True))
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@router.put("/{visit_id}", response_model=VetVisitResponse)
def update_vet_visit(
    visit_id: str,
    data: VetVisitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VetVisit:
    visit = _get_owned_visit_or_404(db, visit_id, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    db.commit()
    db.refresh(visit)
    return visit


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vet_visit(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    visit = _get_owned_visit_or_404(db, visit_id, current_user)
    db.delete(visit)
    db.commit()


def _get_owned_visit_or_404(db: Session, visit_id: str, current_user: User) -> VetVisit:
    visit = (
        db.query(VetVisit)
        .join(Pet)
        .filter(VetVisit.id == visit_id, Pet.owner_id == current_user.id)
        .first()
    )
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veteriner ziyareti bulunamadı.")
    return visit
