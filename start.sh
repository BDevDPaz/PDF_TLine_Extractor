#!/bin/bash
set -e # Detener el script si un comando falla

echo "--- Iniciando Entorno Full-Stack ---"

# --- Configuración del Backend ---
echo " "
echo ">>> Configurando el Backend con Poetry..."
cd backend
# Instala las dependencias definidas en pyproject.toml
poetry install
# Lanza la aplicación con Gunicorn usando poetry en segundo plano
echo ">>> Lanzando servidor Gunicorn en puerto 5000..."
(poetry run gunicorn -c gunicorn.conf.py) &


# --- Configuración del Frontend ---
echo " "
echo ">>> Configurando el Frontend con NPM..."
cd ../frontend
# Instala las dependencias de Node.js
npm install
# Lanza el servidor de desarrollo de Vite en primer plano
echo ">>> Lanzando servidor de Vite en puerto 3000..."
npm run dev -- --host 0.0.0.0