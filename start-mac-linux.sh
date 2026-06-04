#!/bin/bash
echo "==============================================="
echo "   TaQ Engine - Iniciando Servidor (Mac/Linux)"
echo "==============================================="
echo

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
    exit 1
fi

# Initialize database and start server
echo "Iniciando base de datos y servidor..."
echo
python -m taq.main --host 0.0.0.0 --port 8400 --reload

# If we get here, the server stopped (error or Ctrl+C)
echo
echo "El servidor se detuvo. Presione cualquier tecla para cerrar..."
read -n 1 -s