"""
Yapay zekâ analizi uç noktaları - Android PetMetaApiService.analyzePhoto/getAnalysisHistory ile eşleşir.

Groq API anahtarı YALNIZCA burada, backend tarafında kullanılır; Android
istemcisi yalnızca fotoğrafı ve pet_id'yi gönderir (bkz. ai_service.py).

NOT (hesapsız/girişsiz kullanım): Bu uç noktalar bilinçli olarak hesap/giriş
gerektirmez — analiz geçmişi zaten yalnızca Android'in kendi yerel Room
veritabanında tutulur (bkz. AnalysisRepository.kt), backend yalnızca tek
seferlik Groq çağrısı için kullanılır. Kötüye kullanımı/aşırı Groq maliyetini
önlemek için basit bir IP bazlı günlük istek limiti uygulanır
(bkz. services/rate_limiter.py, ayar: ANALYSIS_DAILY_LIMIT_PER_IP).
"""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.analysis import Analysis
from app.schemas.analysis import AiAnalysisResponse, AiFindingSchema
from app.services.ai_service import analyze_pet_photo
from app.services.rate_limiter import enforce_daily_limit

router = APIRouter(tags=["Yapay Zekâ Analizi"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


@router.post(
    "/analysis",
    response_model=AiAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_daily_limit)],
)
async def analyze_photo(
    photo: UploadFile = File(...),
    pet_id: str = Form(..., alias="petId"),
    db: Session = Depends(get_db),
) -> AiAnalysisResponse:
    if photo.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Yalnızca JPEG, PNG veya WEBP formatında fotoğraflar desteklenir.",
        )

    photo_bytes = await photo.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(photo_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fotoğraf boyutu {settings.max_upload_size_mb}MB sınırını aşıyor.",
        )

    result = await analyze_pet_photo(photo_bytes, photo.content_type)

    analysis = Analysis(
        id=str(uuid.uuid4()),
        pet_id=pet_id,
        findings=[finding.model_dump(by_alias=True) for finding in result.findings],
        vet_recommendation=result.vet_recommendation,
        preventive_care_recommendation=result.preventive_care_recommendation,
        nutrition_recommendation=result.nutrition_recommendation,
        hygiene_recommendation=result.hygiene_recommendation,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return _to_response(analysis)


@router.get("/history", response_model=list[AiAnalysisResponse])
def get_analysis_history(
    pet_id: str,
    db: Session = Depends(get_db),
) -> list[AiAnalysisResponse]:
    """
    NOT: Artık hesap/kullanıcı kavramı olmadığından bu uç nokta yalnızca
    `pet_id` ile filtreler (aksi halde herkesin analizleri karışırdı).
    Android istemcisi zaten geçmişi yerel veritabanından okuduğu için bu uç
    nokta pratikte kullanılmaz; geriye dönük uyumluluk için tutulur.
    """
    analyses = (
        db.query(Analysis)
        .filter(Analysis.pet_id == pet_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    return [_to_response(analysis) for analysis in analyses]


def _to_response(analysis: Analysis) -> AiAnalysisResponse:
    return AiAnalysisResponse(
        analysis_id=analysis.id,
        pet_id=analysis.pet_id,
        findings=[AiFindingSchema.model_validate(item) for item in analysis.findings],
        vet_recommendation=analysis.vet_recommendation,
        preventive_care_recommendation=analysis.preventive_care_recommendation,
        nutrition_recommendation=analysis.nutrition_recommendation,
        hygiene_recommendation=analysis.hygiene_recommendation,
        disclaimer=analysis.disclaimer,
        created_at=analysis.created_at,
    )
