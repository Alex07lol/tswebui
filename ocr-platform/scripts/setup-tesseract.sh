#!/usr/bin/env bash
# Install and verify Tesseract OCR
set -euo pipefail

echo "=== Tesseract Setup ==="

if command -v tesseract &>/dev/null; then
    echo "[OK] Tesseract already installed: $(tesseract --version 2>&1 | head -1)"
else
    echo "[INFO] Installing Tesseract..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -q
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    elif command -v brew &>/dev/null; then
        brew install tesseract
    elif command -v pkg &>/dev/null; then
        pkg install tesseract
    else
        echo "[ERROR] Cannot determine package manager. Install Tesseract manually."
        exit 1
    fi
fi

echo "--- Verifying Tesseract ---"
tesseract --version
echo
echo "--- Available language packs ---"
tesseract --list-langs
echo
echo "=== Tesseract setup complete ==="
