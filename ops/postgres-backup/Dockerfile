# Match Latente's production Postgres major version (18) to avoid pg_dump
# compatibility failures. Updates should pin a tested image digest at release.
FROM postgres:18-alpine
RUN apk add --no-cache aws-cli coreutils
COPY backup.sh /usr/local/bin/latente-backup
RUN chmod 0700 /usr/local/bin/latente-backup
USER postgres
ENTRYPOINT ["/usr/local/bin/latente-backup"]
