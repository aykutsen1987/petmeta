"""SQLAlchemy modeli: Evcil Hayvan (Pet) - Android PetEntity/PetDto ile alan bazında eşleşir."""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    species: Mapped[str] = mapped_column(String(50), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    color: Mapped[str | None] = mapped_column(String(60), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_neutered: Mapped[bool] = mapped_column(Boolean, default=False)
    microchip_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    owner_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User", back_populates="pets")
    vaccines = relationship("Vaccine", back_populates="pet", cascade="all, delete-orphan")
    medicines = relationship("Medicine", back_populates="pet", cascade="all, delete-orphan")
    vet_visits = relationship("VetVisit", back_populates="pet", cascade="all, delete-orphan")
    food_logs = relationship("FoodLog", back_populates="pet", cascade="all, delete-orphan")
    water_logs = relationship("WaterLog", back_populates="pet", cascade="all, delete-orphan")
    exercise_logs = relationship("ExerciseLog", back_populates="pet", cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="pet", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="pet", cascade="all, delete-orphan")
