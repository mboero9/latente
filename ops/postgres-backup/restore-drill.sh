#!/bin/sh
# Restores only into an isolated target database; explicitly refuse production.
set -eu
umask 077
: "${RESTORE_TARGET_URL:?RESTORE_TARGET_URL must point to an isolated database}"
: "${BACKUP_FILE:?BACKUP_FILE must be an existing custom format dump}"
test -f "$BACKUP_FILE"
test -s "$BACKUP_FILE"
[ "${DATABASE_URL:-}" != "$RESTORE_TARGET_URL" ] || {
  echo "Refusing to restore into production DATABASE_URL" >&2; exit 1;
}
[ "${CONFIRM_ISOLATED_RESTORE:-}" = "YES" ] || {
  echo "Set CONFIRM_ISOLATED_RESTORE=YES only after checking the target" >&2; exit 1;
}
pg_restore --list "$BACKUP_FILE" > /dev/null
echo "Restoring to specifically authorized isolated target..."
pg_restore --dbname "$RESTORE_TARGET_URL" --no-owner --no-privileges \
  --exit-on-error --verbose "$BACKUP_FILE"
echo "Restore completed; validate counts and queries before signing off"
