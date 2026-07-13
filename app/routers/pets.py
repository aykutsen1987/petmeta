"""Evcil hayvan profili uç noktaları - Android PetMetaApiService.getPets/createPet/updatePet/deletePet ile eşleşir."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pet import Pet
from app.models.user import User
from app.schemas.pet import PetCreate, PetResponse, PetUpdate
from app.security.dependencies import get_current_user
from app.services.pet_service import get_owned_pet_or_404

router = APIRouter(prefix="/pets", tags=["Evcil Hayvanlar"])


@router.get("", response_model=list[PetResponse])
def list_pets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Pet]:
    return db.query(Pet).filter(Pet.owner_id == current_user.id).order_by(Pet.created_at.desc()).all()


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
def create_pet(
    data: PetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Pet:
    pet = Pet(owner_id=current_user.id, **data.model_dump(exclude_none=True))
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Pet:
    return get_owned_pet_or_404(db, pet_id, current_user)


@router.put("/{pet_id}", response_model=PetResponse)
def update_pet(
    pet_id: str,
    data: PetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Pet:
    pet = get_owned_pet_or_404(db, pet_id, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pet, field, value)
    db.commit()
    db.refresh(pet)
    return pet


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    pet = get_owned_pet_or_404(db, pet_id, current_user)
    db.delete(pet)
    db.commit()
