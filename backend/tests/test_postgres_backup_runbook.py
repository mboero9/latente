"""Postgres DR scripts are safe to introduce without mutating production."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ops/postgres-backup"


def test_dump_job_reuses_pg18_and_is_readonly():
    image = (BASE/"Dockerfile").read_text(encoding="utf-8")
    script = (BASE/"backup.sh").read_text(encoding="utf-8")
    assert "FROM postgres:18-alpine" in image
    assert "apk add --no-cache aws-cli" in image
    assert "pg_dump" in script and "--format=custom" in script
    assert "pg_restore --list" in script
    assert "sha256sum" in script
    assert "s3api head-object" in script
    assert "BUCKET" in script and "ENDPOINT" in script
    assert "rm -rf" in script and 'TEMP_DIR="$(mktemp -d)"' in script
    for forbidden in ("DROP DATABASE", "pg_restore --dbname", "psql -c", "aws s3 rm"):
        assert forbidden not in script


def test_restore_only_with_explicit_isolated_target_approval():
    script = (BASE/"restore-drill.sh").read_text(encoding="utf-8")
    assert 'RESTORE_TARGET_URL' in script
    assert 'CONFIRM_ISOLATED_RESTORE' in script
    assert 'Refusing to restore into production' in script
    assert '--exit-on-error' in script
    assert '--no-owner' in script


def test_runbook_requires_human_approval_and_real_backup_verification():
    readme = (BASE/"README.md").read_text(encoding="utf-8")
    assert "NO desplegada ni programada todavía" in readme
    assert "railway postgres pitr schedule set" in readme
    assert "latente-pg-backups" in readme
    assert "0 6 * * *" in readme
    assert "SHA-256" in readme
    assert "RESTORE_TARGET_URL" in readme
    agent = (ROOT/"docs/RAILWAY-AGENT-LATENTE.md").read_text(encoding="utf-8")
    assert "no habilites" in agent
    assert "no hagas merge automático" in agent
    assert "PR" in agent
