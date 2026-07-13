"""
Evcil Hayvan Servis Katmanı.

Aşı, ilaç, veteriner, mama, su, egzersiz, kilo gibi tüm alt kaynaklar
(sub-resource) her zaman bir `pet_id` üzerinden erişildiğinden; bu modüldeki
`get_owned_pet_or_404` fonksiyonu tüm ilgili router'lar tarafından ortak bir
yetkilendirme (authorization) kontrolü olarak kullanılır: İstek yapan kullanıcı,
yalnızca KENDİ evcil hayvanlarının alt kayıtlarına erişebilir.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pet import Pet
from app.models.user import User


def get_owned_pet_or_404(db: Session, pet_id: str, current_user: User) -> Pet:
    pet = db.get(Pet, pet_id)
    if pet is None or pet.owner_id != current_user.id:
        # Güvenlik nedeniyle "bu hayvan başkasına ait" yerine 404 döndürülür;
        # böylece bir saldırgan var olan ama kendisine ait olmayan bir pet_id'yi
        # var olmayan bir pet_id'den ayırt edemez.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evcil hayvan bulunamadı.")
    return pet
