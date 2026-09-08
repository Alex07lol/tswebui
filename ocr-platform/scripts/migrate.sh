#!/usr/bin/env bash
# Run Alembic database migrations
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"

cd "$ROOT_DIR/backend"

ACTION="${1:-upgrade}"
REV="${2:-head}"

echo "[INFO] Running Alembic: $ACTION $REV"
alembic "$ACTION" "$REV"
echo "[OK] Migration complete."
