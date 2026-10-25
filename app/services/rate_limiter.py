"""
Basit, bellek içi (in-memory) IP bazlı günlük istek limiti.

Analiz endpoint'i hesap gerektirmediğinden, kötüye kullanımı ve Groq maliyetini
sınırlamak için her IP'ye günlük bir kota uygulanır.

- `check_daily_limit` (FastAPI dependency): kotayı TÜKETMEDEN yalnızca kontrol eder.
- `record_successful_use`: yalnızca analiz BAŞARILI olduğunda çağrılır; böylece
  Groq hatası veren istekler kullanıcının hakkından düşmez.

NOT: Tek worker ile tutarlıdır (render.yaml / Procfile `--workers 1`). Çok instance
gerekirse Redis gibi paylaşımlı bir depolama kullanın.
"""
from datetime import date
from threading import Lock

from fastapi import HTTPException, Request, status

from app.config import settings

_lock = Lock()
_daily_counts: dict[str, tuple[date, int]] = {}


def client_key(request: Request) -> str:
    """
    Gerçek istemci IP'si. Render gibi bir ters proxy kendi gördüğü adresi
    X-Forwarded-For'a EN SONA ekler; ilk değer istemci tarafından sahte yazılabilir,
    bu yüzden SON değer kullanılır.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        parts = [p.strip() for p in forwarded_for.split(",") if p.strip()]
        if parts:
            return parts[-1]
    return request.client.host if request.client else "unknown"


def _prune(today: date) -> None:
    stale = [k for k, (d, _) in _daily_counts.items() if d != today]
    for key in stale:
        del _daily_counts[key]


def check_daily_limit(request: Request) -> None:
    """Günlük kota dolmuşsa 429 döner; kotayı tüketmez."""
    limit = settings.analysis_daily_limit_per_ip
    if limit <= 0:
        return

    key = client_key(request)
    today = date.today()
    with _lock:
        last_date, count = _daily_counts.get(key, (today, 0))
        if last_date == today and count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Bu IP adresi için günlük yapay zekâ analiz limiti ({limit}) "
                    "aşıldı. Lütfen yarın tekrar deneyin."
                ),
            )


def record_successful_use(request: Request) -> None:
    """Başarılı bir analizden sonra IP'nin günlük sayacını 1 artırır."""
    if settings.analysis_daily_limit_per_ip <= 0:
        return

    key = client_key(request)
    today = date.today()
    with _lock:
        if len(_daily_counts) > 10_000:
            _prune(today)
        last_date, count = _daily_counts.get(key, (today, 0))
        if last_date != today:
            count = 0
        _daily_counts[key] = (today, count + 1)
