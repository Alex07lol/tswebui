#!/usr/bin/env bash
# OCR Platform — Installation Script
# Checks prerequisites and sets up the development environment
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"

echo "=== OCR Platform Installer ==="
echo "Root: $ROOT_DIR"
echo

# --- Prerequisite checks ---
check_command() {
    if command -v "$1" &>/dev/null; then
        echo "[OK] $1 found: $("$1" --version 2>&1 | head -1)"
    else
        echo "[MISSING] $1 not found"
        return 1
    fi
}

echo "--- Checking prerequisites ---"
check_command python3 || true
check_command node || true
check_command npm || true
check_command tesseract || echo "  (Tesseract optional for Phase 0; run scripts/setup-tesseract.sh)"
echo

# --- Backend setup ---
echo "--- Setting up backend ---"
cd "$ROOT_DIR/backend"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "[INFO] Created .env from .env.example"
fi

if command -v pip3 &>/dev/null; then
    pip3 install -e ".[dev]" --quiet || echo "[NOTICE] pip install skipped or requires system packages"
fi
echo

# --- Storage directories ---
mkdir -p "$ROOT_DIR/backend/storage"
echo "[OK] Storage directory created."
echo

echo "=== Installation complete ==="
echo "Run: scripts/dev.sh to start the development stack."
