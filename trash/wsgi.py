#!/usr/bin/env python3
"""
WSGI Entry Point para el Sistema Híbrido Ultra-Agresivo
Punto de entrada compatible con gunicorn para el backend Flask
"""

import sys
import os
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from app import app
    
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=5000, debug=False)
        
except ImportError as e:
    print(f"Error importando la aplicación Flask: {e}")
    print("Verificando estructura del proyecto...")
    
    # Fallback: ejecutar el launcher principal
    from main import FullStackLauncher
    launcher = FullStackLauncher()
    launcher.run()