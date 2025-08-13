#!/bin/bash
set -e # Detener el script si un comando falla

echo "--- Iniciando Entorno Full-Stack ---"

# --- Configuración del Backend ---
echo " "
echo ">>> Lanzando servidor Flask en puerto 5000..."
cd backend
python3 app.py &

# --- Configuración del Frontend ---
echo " "
echo ">>> Lanzando servidor de Vite en puerto 3000..."
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 3000