#!/bin/bash
echo "==============================================="
echo "   TaQ Engine - Iniciando Servidor (Mac/Linux)"
echo "==============================================="
echo

# Function to kill process on a given port
kill_port() {
    local PORT=${1:-8400}
    echo "Verificando si el puerto $PORT está en uso..."

    # Find PID of process listening on the port
    if command -v lsof > /dev/null; then
        PID=$(lsof -ti:$PORT)
    elif command -v netstat > /dev/null; then
        PID=$(netstat -tlnp | grep :$PORT | awk '{print $7}' | cut -d'/' -f1)
    else
        # Fallback: use ss if available
        PID=$(ss -tlnp | grep :$PORT | awk '{print $NF}' | cut -d'=' -f2 | cut -d',' -f1)
    fi

    if [ ! -z "$PID" ]; then
        # Check if it's a Python process
        if ps -p $PID | grep -i python > /dev/null; then
            echo "Encontrado proceso de Python PID $PID en el puerto $PORT"
            echo "Terminando proceso..."
            kill $PID
            # Wait a bit for process to terminate
            sleep 2
            # Force kill if still running
            if ps -p $PID > /dev/null; then
                echo "Proceso no respondió, forzando termination..."
                kill -9 $PID
            fi
            echo "Proceso terminado."
        else
            echo "El proceso en el puerto $PORT no parece ser de Python. No se terminará."
        fi
    else
        echo "Puerto $PORT está libre."
    fi
}

# Try ports 8400 through 8409
BASE_PORT=8400
MAX_ATTEMPTS=10
STARTED=0

for ((i=0; i<MAX_ATTEMPTS; i++)); do
    PORT=$((BASE_PORT + i))
    echo "Intentando liberar el puerto $PORT..."
    kill_port $PORT
    sleep 2
done

# Now try to start the server on each port until one works
for ((i=0; i<MAX_ATTEMPTS; i++)); do
    PORT=$((BASE_PORT + i))
    if [ $STARTED -eq 0 ]; then
        echo
        echo "Intentando iniciar el servidor en el puerto $PORT..."

        # Check if Python is available
        if ! command -v python3 &> /dev/null; then
            echo "Error: Python no encontrado. Por favor instale Python 3.12+ desde https://python.org"
            exit 1
        fi

        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            echo "Creando entorno virtual..."
            python3 -m venv venv
            if [ $? -ne 0 ]; then
                echo "Error: No se pudo crear el entorno virtual"
                exit 1
            fi
        fi

        # Activate virtual environment
        source venv/bin/activate

        # Upgrade pip
        echo "Actualizando pip..."
        python -m pip install --upgrade pip

        # Install dependencies
        echo "Instalando dependencias..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "Error: Fallo al instalar dependencias"
            deactivate
            exit 1
        fi

        # Initialize database and start server
        echo "Iniciando base de datos y servidor en el puerto $PORT..."
        echo
        python -m taq.main --host 0.0.0.0 --port $PORT --reload

        # Check exit code
        if [ $? -eq 0 ]; then
            echo "Servidor detenido normalmente."
            STARTED=1
        else
            echo "Error al iniciar el servidor (posiblemente puerto en uso). Probando el siguiente puerto..."
        fi
    fi
done

if [ $STARTED -eq 0 ]; then
    echo
    echo "Error: No se pudo iniciar el servidor en ninguno de los puertos $BASE_PORT a $((BASE_PORT + MAX_ATTEMPTS - 1))."
    echo "Por favor, cierre cualquier otra instancia de TaQ Engine o cambie el puerto manualmente."
    echo "Presione cualquier tecla para cerrar..."
    read -n 1 -s
    exit 1
else
    echo
    echo "El servidor se detuvo. Presione cualquier tecla para cerrar..."
    read -n 1 -s
fi