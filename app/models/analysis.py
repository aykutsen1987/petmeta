"""SQLAlchemy modeli: Yapay Zekâ Analizi (Analysis) - Android AiAnalysisResponseDto ile eşleşir.

`findings` alanı JSON olarak tutulur (bkz. schemas/analysis.py -> AiFindingSchema listesi).
Bu sayede her analiz için değişken sayıda bulgu (condition/probability/risk) esnek şekilde saklanabilir.

NOT: Yapay zekâ analizi hesap/giriş gerektirmez (bkz. routers/analysis.py). Bu yüzden
`pet_id`, backend'deki `pets` tablosuna bir foreign key DEĞİLDİR — yalnızca istemcinin
(Android'in kendi yerel Room veritabanındaki) referans kimliğidir ve backend'de yalnızca
kayıt/loglama amacıyla saklanır. Aynı sebeple bu tabloda bir `user_id` alanı yoktur.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

DEFAULT_DISCLAIMER = (
    "Bu analiz yalnızca yapay zekâ tarafından oluşturulmuştur. "
    "Kesin teşhis değildir. Lütfen veteriner hekime danışınız."
)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # İstemcinin (Android) kendi yerel pet kimliği; backend'de bir foreign key değildir.
    pet_id: Mapped[str] = mapped_column(String(64), index=True)

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

