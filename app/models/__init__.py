"""
Tüm SQLAlchemy modellerini tek bir yerden içe aktarır.

`app.main` içindeki `Base.metadata.create_all(bind=engine)` çağrısının tüm
tabloları oluşturabilmesi için, ilgili modül import edilmeden önce her model
sınıfının Python tarafından "görülmüş" (import edilmiş) olması gerekir.
Bu dosya tam olarak bu amaca hizmet eder.
"""
from app.models.analysis import Analysis
from app.models.exercise_log import ExerciseLog
from app.models.food_log import FoodLog
from app.models.medicine import Medicine
from app.models.pet import Pet
from app.models.user import User
from app.models.vaccine import Vaccine
from app.models.vet_visit import VetVisit
from app.models.water_log import WaterLog
from app.models.weight_log import WeightLog

__all__ = [
    "Analysis",
    "ExerciseLog",
    "FoodLog",
    "Medicine",
    "Pet",
    "User",
    "Vaccine",
    "VetVisit",
    "WaterLog",
    "WeightLog",
]
