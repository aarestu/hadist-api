#!/usr/bin/env bash

set -e

echo "==================================================="
echo "  Hadith API Importer - Python Venv Setup (POSIX)"
echo "==================================================="

# Find Python binary
if command -v python &>/dev/null; then
    PYTHON_BIN="python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif [ -f "/c/Python311/python.exe" ]; then
    PYTHON_BIN="/c/Python311/python.exe"
else
    echo "[ERROR] Python tidak ditemukan. Harap install Python 3.9-3.12."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "[INFO] Membuat virtual environment '.venv'..."
    $PYTHON_BIN -m venv .venv
    echo "[INFO] Virtual environment '.venv' berhasil dibuat."
else
    echo "[INFO] Virtual environment '.venv' sudah ada."
fi

# Activate virtual environment
echo "[INFO] Mengaktifkan virtual environment..."
source .venv/bin/activate

# Upgrade pip & install requirements
echo "[INFO] Meng-upgrade pip..."
$PYTHON_BIN -m pip install --upgrade pip

echo "[INFO] Menginstal dependensi dari requirements.txt..."
$PYTHON_BIN -m pip install -r requirements.txt

echo ""
echo "==================================================="
echo "[SUCCESS] Isolated Workspace berhasil disiapkan!"
echo ""
echo "Untuk mengaktifkan environment kapan saja, jalankan:"
echo "  source .venv/bin/activate"
echo ""
echo "Untuk menjalankan importer:"
echo "  python -m app.cli.main"
echo "==================================================="
