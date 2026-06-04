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

:: Function to kill process on a given port
:kill_port
setlocal
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8400"
echo Verificando si el puerto %PORT% está en uso...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    set "PID=%%a"
    echo Encontrado proceso PID !PID! en el puerto %PORT%
    :: Check if it's a Python process
    tasklist /FI "PID eq !PID!" | findstr /I "python.exe" >nul
    if !errorlevel! equ 0 (
        echo Terminando proceso de Python en el puerto %PORT%...
        taskkill /PID !PID! /F >nul
        if !errorlevel! equ 0 (
            echo Proceso terminado.
        ) else (
            echo Error al terminar el proceso. Continuando de todos modos...
        )
    ) else (
        echo El proceso en el puerto %PORT% no parece ser de Python. No se terminará.
    )
)
endlocal
goto :eof

:: Try to free ports 8400 through 8409
set "BASE_PORT=8400"
set "MAX_ATTEMPTS=10"
set "PORT="
for /L %%i in (0,1,9) do (
    set /a PORT=%BASE_PORT%+%%i
    echo Intentando liberar el puerto !PORT%...
    call :kill_port !PORT!
    timeout /t 2 >nul
)

:: Now try to start the server on each port until one works
set "STARTED=0"
for /L %%i in (0,1,9) do (
    set /a PORT=%BASE_PORT%+%%i
    if !STARTED! equ 0 (
        echo.
        echo Intentando iniciar el servidor en el puerto !PORT%...
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
        echo Iniciando base de datos y servidor en el puerto !PORT%...
        echo.
        python -m taq.main --host 0.0.0.0 --port !PORT% --reload
        set "ERRORLEVEL=%errorlevel%"
        if !ERRORLEVEL! equ 0 (
            echo Servidor detenido normalmente.
            set "STARTED=1"
        ) else if !ERRORLEVEL! equ 1 (
            echo Error al iniciar el servidor (posiblemente puerto en uso). Probando el siguiente puerto...
        ) else (
            echo Error inesperado (codigo de salida !ERRORLEVEL!). Deteniendo.
            pause
            exit /b !ERRORLEVEL!
        )
    )
)

if !STARTED! equ 0 (
    echo.
    echo Error: No se pudo iniciar el servidor en ninguno de los puertos %BASE_PORT% a %BASE_PORT%+9.
    echo Por favor, cierre cualquier otra instancia de TaQ Engine o cambie el puerto manualmente.
    pause
    exit /b 1
) else (
    echo.
    echo El servidor se detuvo. Presione cualquier tecla para cerrar...
    pause >nul
)