"""
Basit, bellek içi (in-memory) IP bazlı günlük istek limiti.

Yapay zekâ analizi endpoint'i artık hesap/giriş gerektirmediği için
(bkz. routers/analysis.py), kötüye kullanımı ve buna bağlı Groq maliyetini
sınırlamak amacıyla her IP adresi için basit bir günlük sayaç tutulur.

NOT: Bu limiter yalnızca tek bir worker/process ile tutarlıdır (bkz.
render.yaml -> `--workers 1`). Birden fazla worker/instance kullanılırsa her
biri kendi sayacını tutar ve gerçek limit, tanımlanan değerin worker sayısı
katı kadar gevşemiş olur. Daha güçlü/kalıcı ve çok-instance'a duyarlı bir
limit gerekirse Redis gibi paylaşımlı bir depolama kullanılmalıdır.
"""
from collections import defaultdict
from datetime import date
from threading import Lock

from fastapi import HTTPException, Request, status

from app.config import settings

_lock = Lock()
_daily_counts: dict[str, tuple[date, int]] = defaultdict(lambda: (date.min, 0))


def _client_key(request: Request) -> str:
    """Render gibi ters proxy arkasında gerçek istemci IP'sini almaya çalışır."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_daily_limit(request: Request) -> None:
    """
    Aynı IP'den gelen istekleri günlük bir üst sınırla sınırlar.
    Limit aşıldığında 429 Too Many Requests döner.
    """
    limit = settings.analysis_daily_limit_per_ip
    if limit <= 0:
        return  # 0 veya negatif değer: limit devre dışı

    key = _client_key(request)
    today = date.today()

    with _lock:
        last_date, count = _daily_counts[key]
        if last_date != today:
            count = 0
        count += 1
        _daily_counts[key] = (today, count)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Bu IP adresi için günlük yapay zekâ analiz limiti ({limit}) "
                    "aşıldı. Lütfen yarın tekrar deneyin."
                ),
            )
