"""
Yapay zekâ analizi uç noktası - Android PetMetaApiService.analyzePhoto ile eşleşir.

Groq API anahtarı YALNIZCA burada, backend tarafında kullanılır; Android istemcisi
yalnızca fotoğrafı, pet_id'yi ve (isteğe bağlı) türü gönderir.

Gizlilik (bilinçli tasarım): Bu uç nokta hesap/giriş gerektirmez ve analiz sonuçları
veya fotoğraflar backend'de SAKLANMAZ. Geçmiş yalnızca cihazın yerel (şifreli) Room
veritabanında tutulur. (Eski `/history` uç noktası kaldırıldı: istemci pet_id'leri
tahmin edilebilir sayılar olduğundan başkalarının sonuçlarının okunmasına yol açıyordu.)
Kötüye kullanım/maliyet, IP bazlı günlük limitle sınırlanır (bkz. services/rate_limiter.py).
"""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.config import settings
from app.schemas.analysis import AiAnalysisResponse
from app.services.ai_service import AiUnavailableError, analyze_pet_photo
from app.services.rate_limiter import check_daily_limit, record_successful_use

logger = logging.getLogger("petmeta.analysis")

router = APIRouter(tags=["Yapay Zekâ Analizi"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
_CHUNK = 64 * 1024


def _sniff_image_type(data: bytes) -> str | None:
    """İstemcinin beyan ettiği Content-Type'a güvenmeden dosya imzasından (magic bytes) tür bulur."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def _read_limited(photo: UploadFile, max_bytes: int) -> bytes:
    """Dosyayı parça parça okur; sınır aşılırsa belleği doldurmadan 413 döner."""
    buffer = bytearray()
    while chunk := await photo.read(_CHUNK):
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fotoğraf boyutu {settings.max_upload_size_mb}MB sınırını aşıyor.",
            )
    return bytes(buffer)


@router.post(
    "/analysis",
    response_model=AiAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_daily_limit)],
)
async def analyze_photo(
    request: Request,
    photo: UploadFile = File(...),
    pet_id: str = Form(..., alias="petId", max_length=64),
    species: str | None = Form(None, max_length=32),
) -> AiAnalysisResponse:
    if photo.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Yalnızca JPEG, PNG veya WEBP formatında fotoğraflar desteklenir.",
        )

    photo_bytes = await _read_limited(photo, settings.max_upload_size_mb * 1024 * 1024)
    real_type = _sniff_image_type(photo_bytes)
    if real_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Dosya geçerli bir JPEG, PNG veya WEBP görseli değil.",
        )

    try:
        result = await analyze_pet_photo(photo_bytes, real_type, species)
    except AiUnavailableError as exc:
        logger.error("AI analizi başarısız: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Yapay zekâ analizi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
        ) from exc

    record_successful_use(request)

    return AiAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        pet_id=pet_id,
        findings=result.findings,
        vet_recommendation=result.vet_recommendation,
        preventive_care_recommendation=result.preventive_care_recommendation,
        nutrition_recommendation=result.nutrition_recommendation,
        hygiene_recommendation=result.hygiene_recommendation,
        created_at=datetime.now(timezone.utc),
    )
