@echo off
echo ===============================================
echo   TaQ Engine - Iniciando Servidor (Windows)
echo ===============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no encontrado. Por favor instale Python 3.12+ desde https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo Error: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate

:: Upgrade pip
echo Actualizando pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Fallo al instalar dependencias
    pause
    exit /b 1
)

:: Initialize database and start server
echo Iniciando base de datos y servidor...
echo.
python -m taq.main --host 0.0.0.0 --port 8400 --reload

:: Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo El servidor se detubo. Presione cualquier tecla para cerrar...
    pause >nul
)