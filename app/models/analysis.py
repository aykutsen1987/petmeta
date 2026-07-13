"""SQLAlchemy modeli: Yapay Zekâ Analizi (Analysis) - Android AiAnalysisResponseDto ile eşleşir.

`findings` alanı JSON olarak tutulur (bkz. schemas/analysis.py -> AiFindingSchema listesi).
Bu sayede her analiz için değişken sayıda bulgu (condition/probability/risk) esnek şekilde saklanabilir.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

DEFAULT_DISCLAIMER = (
    "Bu analiz yalnızca yapay zekâ tarafından oluşturulmuştur. "
    "Kesin teşhis değildir. Lütfen veteriner hekime danışınız."
)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pet_id: Mapped[str] = mapped_column(String(36), ForeignKey("pets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    vet_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    preventive_care_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    nutrition_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    hygiene_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, default=DEFAULT_DISCLAIMER)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    pet = relationship("Pet", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
