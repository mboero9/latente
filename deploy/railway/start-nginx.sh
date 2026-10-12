#!/bin/sh
set -eu
export PORT="${PORT:-8080}"
export API_PORT="${API_PORT:-8000}"
export API_HOST="${API_HOST:-api.railway.internal}"
case "$PORT:$API_PORT" in *[!0-9:]*|:*|*:) echo 'Puertos inválidos' >&2; exit 1;; esac
case "$API_HOST" in ''|*[!a-zA-Z0-9.-]*) echo 'API_HOST debe ser un hostname' >&2; exit 1;; esac
test "$PORT" -ge 1 && test "$PORT" -le 65535
test "$API_PORT" -ge 1 && test "$API_PORT" -le 65535
NGINX_RESOLVER=$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf)
test -n "$NGINX_RESOLVER"
case "$NGINX_RESOLVER" in *:*) NGINX_RESOLVER="[$NGINX_RESOLVER]";; esac
export NGINX_RESOLVER
envsubst '${PORT} ${API_HOST} ${API_PORT} ${NGINX_RESOLVER}' \
  < /etc/nginx/latente.conf.template > /etc/nginx/nginx.conf
nginx -t
exec nginx -g 'daemon off;'
