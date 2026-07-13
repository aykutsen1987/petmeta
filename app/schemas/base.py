"""
PetMeta Backend - Ortak Pydantic Taban Sınıfı

Android istemcisi (bkz. data/remote/dto/Dtos.kt), kotlinx.serialization ile
JSON alan adlarını AYNEN Kotlin property adları (camelCase) olarak bekler ve
üretir (herhangi bir snake_case dönüştürücü kullanılmaz - bkz. NetworkModule.kt).

Bu yüzden backend tarafında da Python'un doğal snake_case yazım kuralına
(PEP 8) sadık kalabilmek için, tüm şemalar bu `CamelModel` sınıfından türetilir:
- Python tarafında alanlar snake_case yazılır (ör. `full_name`).
- JSON serileştirme/parse sırasında bu alanlar otomatik olarak camelCase'e
  çevrilir (ör. `fullName`), böylece Android DTO'larıyla birebir uyumlu olur.
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Tüm request/response şemalarının miras aldığı temel sınıf."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
