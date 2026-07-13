"""Yapay zekâ analizi şemaları - Android AiAnalysisResponseDto/AiFindingDto ile birebir eşleşir."""
from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel

DEFAULT_DISCLAIMER = (
    "Bu analiz yalnızca yapay zekâ tarafından oluşturulmuştur. "
    "Kesin teşhis değildir. Lütfen veteriner hekime danışınız."
)

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class AiFindingSchema(CamelModel):
    """Örn: Mantar, Alerji, Parazit, Egzama, Kuruluk, Kaşıntı, Enfeksiyon vb."""

    condition: str
    probability_percent: int = Field(ge=0, le=100)
    risk_level: RiskLevel


class AiAnalysisResponse(CamelModel):
    analysis_id: str
    pet_id: str
    findings: list[AiFindingSchema]
    vet_recommendation: str
    preventive_care_recommendation: str
    nutrition_recommendation: str
    hygiene_recommendation: str
    disclaimer: str = DEFAULT_DISCLAIMER
    created_at: datetime
