"""Cliente de API-SPORTS directo, con presupuesto persistente y pausas globales."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import httpx
from sqlalchemy import select
from .config import settings
from .db import session_scope
from .models import ApiUsage, utcnow
from .ingest import upsert


def aware(value):
    return (
        value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value
    )


def tomorrow(now):
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=10, microsecond=0)


class Deferred(Exception):
    def __init__(self, until, message):
        self.until, self.message = until, message
        super().__init__(message)


class ProviderError(Exception):
    pass


def retry_time(value, now):
    try:
        return now + timedelta(seconds=max(60, min(int(value), 86400)))
    except (ValueError, TypeError):
        try:
            return max(now + timedelta(seconds=60), parsedate_to_datetime(value))
        except (ValueError, TypeError, OverflowError):
            return now + timedelta(seconds=60)


def reserve():
    now = utcnow()
    with session_scope() as s:
        # INSERT DO NOTHING impide reiniciar contadores tras reinicios/concurrencia.
        from sqlalchemy.dialects.postgresql import insert

        s.execute(
            insert(ApiUsage).values(day=now.date(), requests=0).on_conflict_do_nothing()
        )
        u = s.scalar(
            select(ApiUsage).where(ApiUsage.day == now.date()).with_for_update()
        )
        if u.requests >= settings.daily_budget or u.provider_remaining == 0:
            raise Deferred(
                tomorrow(now), "Cuota diaria agotada; se conserva la última copia"
            )
        if u.blocked_until and aware(u.blocked_until) > now:
            raise Deferred(aware(u.blocked_until), "Pausa solicitada por el proveedor")
        if (
            u.last_request
            and aware(u.last_request) + timedelta(seconds=settings.minimum_gap) > now
        ):
            raise Deferred(
                aware(u.last_request) + timedelta(seconds=settings.minimum_gap),
                "Esperando intervalo de consultas",
            )
        u.requests += 1  # También cuentan los intentos fallidos.
        u.last_request = now
    return now.date()


def record_headers(day, headers, status):
    now = utcnow()
    with session_scope() as s:
        u = s.get(ApiUsage, day, with_for_update=True)
        remaining = headers.get("x-ratelimit-requests-remaining")
        if remaining is not None:
            try:
                u.provider_remaining = max(0, int(remaining))
            except ValueError:
                pass
        if u.provider_remaining == 0:
            u.blocked_until = tomorrow(now)
        elif status == 429 or headers.get("x-ratelimit-remaining") == "0":
            u.blocked_until = retry_time(headers.get("retry-after"), now)
        if status in (401, 403):
            u.blocked_until = now + timedelta(hours=1)


def validate_payload(data):
    if not isinstance(data, dict) or data.get("errors"):
        # Los mensajes del proveedor podrían repetir la clave. Se registra solo la categoría.
        known = {
            "token",
            "requests",
            "rateLimit",
            "plan",
            "endpoint",
            "league",
            "season",
            "page",
            "ids",
            "access",
        }
        keys = (
            sorted(known.intersection(data.get("errors", {}).keys()))
            if isinstance(data, dict) and isinstance(data.get("errors"), dict)
            else []
        )
        raise ProviderError(
            "API rechazó la consulta" + (": " + ", ".join(keys)[:80] if keys else "")
        )
    if not isinstance(data.get("response"), list):
        raise ProviderError("Respuesta de proveedor inválida")
    return data["response"]


class FootballClient:
    def __init__(self, transport=None):
        self.client = httpx.Client(
            base_url="https://v3.football.api-sports.io",
            headers={"x-apisports-key": settings.api_key},
            timeout=httpx.Timeout(25, connect=10),
            transport=transport,
            trust_env=False,
        )

    def get(self, endpoint, params):
        if not settings.api_key:
            raise Deferred(
                utcnow() + timedelta(minutes=5), "Falta configurar API_FOOTBALL_KEY"
            )
        all_rows = []
        page = 1
        while True:
            day = reserve()
            query = {**params, **({"page": page} if page > 1 else {})}
            try:
                response = self.client.get(endpoint, params=query)
            except httpx.HTTPError as exc:
                raise ProviderError("Error de red con el proveedor") from exc
            record_headers(day, response.headers, response.status_code)
            if response.status_code == 429:
                raise Deferred(
                    retry_time(response.headers.get("retry-after"), utcnow()),
                    "Límite temporal del proveedor",
                )
            if response.is_error:
                raise ProviderError(f"Proveedor HTTP {response.status_code}")
            try:
                data = response.json()
            except ValueError as exc:
                raise ProviderError("Proveedor devolvió un JSON inválido") from exc
            all_rows.extend(validate_payload(data))
            total = int(data.get("paging", {}).get("total") or 1)
            if page >= total:
                return all_rows
            if total > 100:
                raise ProviderError("Paginación inesperada; revisar consulta")
            # Una llamada paginada reprogramada conserva atomicidad: nunca se publica media tabla.
            import time

            time.sleep(settings.minimum_gap)
            page += 1

    def close(self):
        self.client.close()
