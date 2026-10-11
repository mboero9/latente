#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
owner="${1:-TU_USUARIO_GITHUB}"
repo="${2:-latente}"
visibility="${3:---private}"
if [[ "$owner" == "TU_USUARIO_GITHUB" || ! "$owner" =~ ^[A-Za-z0-9-]+$ || ! "$repo" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "Uso: bash scripts/publish-github.sh TU_USUARIO_GITHUB latente [--private|--public]" >&2
  exit 1
fi
if [[ "$visibility" != "--private" && "$visibility" != "--public" ]]; then
  echo "Visibilidad inválida" >&2; exit 1
fi
command -v gh >/dev/null || { echo "Instalá GitHub CLI: https://cli.github.com" >&2; exit 1; }
gh auth status
if [[ ! -d .git ]]; then git init -b main; fi
if git remote get-url origin >/dev/null 2>&1; then
  echo "Ya existe origin. Revisalo con git remote -v; este script no lo modifica." >&2
  exit 1
fi
if [[ -n "$(git ls-files .env '*.pem' '*.key')" ]]; then
  echo "Hay archivos sensibles versionados. Quitalos del índice antes de continuar." >&2; exit 1
fi
git add .
if ! git diff --cached --quiet; then git commit -m "feat: aplicación Latente con datos automáticos y despliegue Docker"; fi
# Crea un repositorio NUEVO; si el nombre existe, gh se detiene sin sobrescribirlo.
gh repo create "$owner/$repo" "$visibility" --description "Resultados de fútbol, ingesta automática y PostgreSQL" --source . --remote origin --push
