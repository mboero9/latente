#!/usr/bin/env bash
set -euo pipefail
base="${1:-http://localhost:8080}"
curl --fail --silent --show-error "$base/api/health"
curl --fail --silent --show-error "$base/api/leagues" > /dev/null
curl --fail --silent --show-error "$base/" > /dev/null
echo " Prueba básica completada."
