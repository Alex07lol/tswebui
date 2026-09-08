#!/usr/bin/env bash
# Start the OCR Platform development stack
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"

echo "=== Starting OCR Platform (Development) ==="

cleanup() {
    echo
    echo "Stopping development servers..."
    kill "$BACKEND_PID" 2>/dev/null || true
    wait 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# Start backend
echo "[INFO] Starting backend on http://localhost:8000"
cd "$ROOT_DIR/backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo
echo "[READY] OCR Platform backend running:"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop."
wait
