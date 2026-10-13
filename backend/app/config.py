"""Configuración compartida. Ningún secreto se envía al navegador."""

import os
from dataclasses import dataclass, field
from sqlalchemy import URL
from sqlalchemy.engine import make_url


def integer(name: str, default: int, minimum: int = 1) -> int:
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}")
    return value


def data_mode():
    mode = os.getenv("DATA_MODE", "demo")
    return ("api" if os.getenv("API_FOOTBALL_KEY", "").strip() else "demo") if mode == "auto" else mode


@dataclass(frozen=True)
class Settings:
    mode: str = field(default_factory=data_mode)
    api_key: str = field(default_factory=lambda: os.getenv("API_FOOTBALL_KEY", ""))
    profile: str = field(default_factory=lambda: os.getenv("SYNC_PROFILE", "free"))
    league_scope: str = field(default_factory=lambda: os.getenv("LEAGUE_SCOPE", "selected"))
    # Argentina, Conmebol, Europa y Brasil. Son IDs estables del proveedor.
    league_ids: tuple[int, ...] = field(
        default_factory=lambda: tuple(
            dict.fromkeys(
                int(v.strip())
                for v in os.getenv(
                    "LEAGUE_IDS", "128,129,130,13,11,2,39,140,135,78,61,71"
                ).split(",")
                if v.strip()
            )
        )
    )
    daily_budget: int = field(default_factory=lambda: integer("API_DAILY_BUDGET", 90))
    minimum_gap: int = field(default_factory=lambda: integer("API_MIN_GAP_SECONDS", 7))
    origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            v.strip()
            for v in os.getenv(
                "CORS_ORIGINS", "http://localhost:8080,http://localhost:5173"
            ).split(",")
            if v.strip()
        )
    )

    def __post_init__(self):
        if self.mode not in {"demo", "api"}:
            raise ValueError("DATA_MODE debe ser demo o api")
        if self.profile not in {"free", "live"}:
            raise ValueError("SYNC_PROFILE debe ser free o live")
        if self.league_scope not in {"selected", "all"}:
            raise ValueError("LEAGUE_SCOPE debe ser selected o all")
        if not self.league_ids or any(i <= 0 for i in self.league_ids):
            raise ValueError("LEAGUE_IDS requiere IDs positivos")

    @property
    def all_leagues(self):
        return self.league_scope == "all"

    @property
    def allowed_leagues(self):
        return None if self.all_leagues else self.league_ids

    def accepts_league(self, league_id):
        return self.all_leagues or league_id in self.league_ids

    @property
    def live_seconds(self):
        return integer(
            "LIVE_INTERVAL_SECONDS", 1800 if self.profile == "free" else 15, 5
        )

    @property
    def statistics_seconds(self):
        return integer("STATISTICS_INTERVAL_SECONDS", 1800 if self.profile == "free" else 60, 60)

    @property
    def fixtures_seconds(self):
        return integer(
            "FIXTURES_INTERVAL_SECONDS", 86400 if self.profile == "free" else 21600, 60
        )

    @property
    def tables_seconds(self):
        return integer(
            "TABLES_INTERVAL_SECONDS", 86400 if self.profile == "free" else 3600, 3600
        )

    @property
    def scorers_seconds(self):
        return integer(
            "SCORERS_INTERVAL_SECONDS", 86400 if self.profile == "free" else 21600, 3600
        )

    @property
    def worker_heartbeat_timeout(self):
        interval = integer("WORKER_EXPECTED_INTERVAL_SECONDS", 0, 0)
        return interval + 180 if interval else 90

    @property
    def database_url(self):
        supplied = os.getenv("DATABASE_URL")
        if supplied:
            url = make_url(supplied)
            if url.drivername in {"postgres", "postgresql"}:
                url = url.set(drivername="postgresql+psycopg")
            return url
        return URL.create(
            "postgresql+psycopg",
            username=os.getenv("POSTGRES_USER", "latente"),
            password=os.getenv("POSTGRES_PASSWORD", "latente_local_only"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "latente"),
        )


settings = Settings()
