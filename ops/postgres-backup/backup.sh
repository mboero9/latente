#!/bin/sh
# One-shot Railway cron job. Read-only pg_dump; never alters production.
set -eu
umask 077

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BUCKET:?BUCKET is required}"
: "${ENDPOINT:?ENDPOINT is required}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_DEFAULT_REGION:?AWS_DEFAULT_REGION is required}"

export AWS_EC2_METADATA_DISABLED=true
export PGCONNECT_TIMEOUT=20
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
KEY="latente/postgresql/${STAMP}.dump"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT HUP INT TERM

echo "Latente PostgreSQL dump starting at $STAMP (credentials redacted)"
pg_dump "$DATABASE_URL" --format=custom --compress=6 --no-owner \
  --no-privileges --file="$TEMP_DIR/backup.dump"
test -s "$TEMP_DIR/backup.dump"
pg_restore --list "$TEMP_DIR/backup.dump" > /dev/null
sha256sum "$TEMP_DIR/backup.dump" | awk '{print $1}' > "$TEMP_DIR/sha256.txt"
echo "Dump created and archive catalog verified"

aws --endpoint-url "$ENDPOINT" s3 cp "$TEMP_DIR/backup.dump" \
  "s3://$BUCKET/$KEY" --only-show-errors
aws --endpoint-url "$ENDPOINT" s3 cp "$TEMP_DIR/sha256.txt" \
  "s3://$BUCKET/$KEY.sha256" --only-show-errors
aws --endpoint-url "$ENDPOINT" s3api head-object \
  --bucket "$BUCKET" --key "$KEY" --query ContentLength --output text > "$TEMP_DIR/remote-length"
REMOTE_BYTES="$(cat "$TEMP_DIR/remote-length")"
[ "$REMOTE_BYTES" -gt 0 ] || { echo "ERROR: remote dump missing/empty" >&2; exit 1; }
echo "Latente backup successfully uploaded: $KEY ($REMOTE_BYTES bytes)"
# No automatic destructive deletion. Set object lifecycle in the bucket once
# retention is approved (recommended 30-90 days). Never share this bucket publicly.
