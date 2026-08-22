@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   Hadith API Importer - Python Venv Setup (Windows)
echo ===================================================

REM Check Python installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python tidak ditemukan di PATH. Harap install Python 3.9+ terlebih dahulu.
    exit /b 1
)

REM Create virtual environment if not exists
IF NOT EXIST ".venv" (
    echo [INFO] Membuat virtual environment '.venv'...
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Gagal membuat virtual environment.
        exit /b 1
    )
    echo [INFO] Virtual environment '.venv' berhasil dibuat.
) ELSE (
    echo [INFO] Virtual environment '.venv' sudah ada.
)

REM Activate virtual environment
echo [INFO] Mengaktifkan virtual environment...
CALL .venv\Scripts\activate.bat

REM Upgrade pip & install requirements
echo [INFO] Meng-upgrade pip...
python -m pip install --upgrade pip

echo [INFO] Menginstal dependensi dari requirements.txt...
pip install -r requirements.txt

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================================
    echo [SUCCESS] Isolated Workspace berhasil disiapkan!
    echo.
    echo Untuk mengaktifkan environment kapan saja, jalankan:
    echo   .venv\Scripts\activate
    echo.
    echo Untuk menjalankan importer:
    echo   python -m app.cli.main
    echo ===================================================
) ELSE (
    echo [ERROR] Gagal menginstal dependensi.
)

ENDLOCAL
