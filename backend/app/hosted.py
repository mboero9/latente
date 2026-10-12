"""Arranque en PaaS: esperar PostgreSQL, migrar con un lock y ejecutar el servicio."""

import os
import sys
import time
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from .db import engine


def migrate():
    deadline = time.monotonic() + 120
    while True:
        try:
            with engine.connect() as connection:
                if connection.scalar(text("SELECT pg_try_advisory_lock(67120835)")):
                    try:
                        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
                        command.upgrade(config, "head")
                        return
                    finally:
                        connection.execute(text("SELECT pg_advisory_unlock(67120835)"))
        except OperationalError:
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("PostgreSQL no estuvo disponible para aplicar migraciones")
        time.sleep(2)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"api", "ingest", "worker"}:
        raise SystemExit("Uso: python -m app.hosted api|ingest|worker")
    mode = sys.argv[1]
    try:
        migrate()
    except Exception as exc:
        # No imprimir URLs de conexión ni excepciones que puedan incluir credenciales.
        print(f"No se pudo inicializar la base ({type(exc).__name__})", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        engine.dispose()
    if mode == "api":
        port = int(os.getenv("PORT", "8000"))
        if not 1 <= port <= 65535:
            raise SystemExit("PORT debe estar entre 1 y 65535")
        argv = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", os.getenv("API_BIND_HOST", "0.0.0.0"),
                "--port", str(port), "--no-proxy-headers"]
    elif mode == "ingest":
        argv = [sys.executable, "-m", "app.worker", "--once", "--max-seconds", "120"]
    else:
        argv = [sys.executable, "-m", "app.worker"]
    os.execv(sys.executable, argv)


if __name__ == "__main__":
    main()
