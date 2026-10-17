# Backup y recuperación — Latente PostgreSQL (Railway)

**Estado:** configuración preparada, **NO desplegada ni programada todavía**.
La base de producción es el servicio `Postgres`, volumen `postgres-volume` (500 MB)
con imagen `ghcr.io/railwayapp-templates/postgres-ssl:18`. Ningún backup
estaba disponible para inspección con las acciones de Railway conectadas;
no debemos suponer que existen o que están activados.

## Defensa 1 — Backups nativos (primera prioridad)

Ir a Railway → proyecto **Latente** → **Postgres** → **Backups** →
**Edit schedule** → seleccionar *Daily*, *Weekly* y *Monthly*.
Railway retiene: diarios 6 días, semanales 27 días, mensuales 89 días.
Hacer un snapshot manual inicial desde esa misma pantalla.
Si el usuario utiliza Railway CLI v5.9+ autenticada con OAuth:

```sh
railway postgres pitr schedule set --project 357c8d6b-9d28-43c6-a2e4-c812065ff1ea --environment production --service Postgres --daily --weekly --monthly
railway postgres pitr schedule list --project 357c8d6b-9d28-43c6-a2e4-c812065ff1ea --environment production --service Postgres
railway postgres pitr backup create --project 357c8d6b-9d28-43c6-a2e4-c812065ff1ea --environment production --service Postgres --name inicial-latente
```

**Precaución:** No restaurar nunca directamente sobre producción durante una
prueba. Restore de snapshot desde el dashboard crea un volumen nuevo y pasa
por cambios staged; comprobar antes de Deploy. La eliminación del volumen
elimina sus backups. El almacenamiento incremental se factura.

## Defensa 2 — PITR (opcional, luego de probar snapshots)

Desde Backups → Enable PITR. Railway crea un bucket para WAL archivados,
reinicia PostgreSQL y, después de una primera base completa, habilita la
recuperación a una marca temporal. PITR restaura en un servicio hermano, sin
alterar el origen, pero tiene costos de almacenamiento y egress.
No activarlo sin revisión de la ventana de mantenimiento y costos.

## Defensa 3 — Dump diario portable y almacenado fuera de DB

El subdirectorio incluye `Dockerfile` y `backup.sh` listos para un
servicio cron **separado**, que corre `pg_dump -Fc` y valida el catálogo
con `pg_restore --list`. Luego sube dump y checksum SHA-256 a S3/Railway
Bucket y confirma la presencia remota. No copia secretos a GitHub ni
altera la base productiva.

Al aprobar el nuevo servicio y bucket (tienen costo variable):
1. Crear bucket privado llamado `latente-pg-backups` en Railway.
2. Crear servicio `postgres-backup` desde repo `mboero9/latente`,
   root directory `ops/postgres-backup`, Dockerfile del mismo directorio.
3. Configurar referencias de variables desde el dashboard, **sin valores
   literales en GitHub**:
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
   - `BUCKET=${{latente-pg-backups.BUCKET}}` (revisar el nombre real en Credentials)
   - `ENDPOINT=${{latente-pg-backups.ENDPOINT}}`
   - `AWS_ACCESS_KEY_ID=${{latente-pg-backups.ACCESS_KEY_ID}}`
   - `AWS_SECRET_ACCESS_KEY=${{latente-pg-backups.SECRET_ACCESS_KEY}}`
   - `AWS_DEFAULT_REGION=${{latente-pg-backups.REGION}}`
4. Cron `0 6 * * *` = 06:00 UTC / 03:00 Argentina (UTC-3).
5. Lanzar una prueba y verificar **dump descargable y checksum correcto**;
   luego configurar lifecycle del bucket para 30–90 días si es compatible,
   revisando costos. El script **no elimina backups** por defecto.
6. Realizar restore mensual sobre base aislada mediante
   `restore-drill.sh` con `RESTORE_TARGET_URL`, `BACKUP_FILE` y
   `CONFIRM_ISOLATED_RESTORE=YES`. Nunca apuntar al URL productivo.

El entorno de Railway para Latinoamérica y medios varía: comprobar nombres
reales de variables disponibles en Credentials antes de activar el cron.
Cambiar/rotar claves desde Railway, no en el código.

## Qué validar después del primer backup

- Cron `SUCCESS`, objeto y SHA-256 realmente en bucket.
- `pg_restore --list` funciona, restore real en base temporal aislada.
- Comparar `COUNT(*)` de tablas importantes y una muestra de fechas recientes.
- Registrar tiempo total de restauración (RTO) y antigüedad del último
  backup válido (RPO); lanzar alertas cuando falten copias.
- Prohibir acceso público al bucket y limitar acceso a credenciales.

Documentación oficial:
- https://docs.railway.com/guides/postgres-backups-restores
- https://docs.railway.com/cli/postgres
- https://docs.railway.com/volumes/backups
- https://docs.railway.com/cli/agent
