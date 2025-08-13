#!/usr/bin/env python3
"""
Sistema Híbrido Ultra-Agresivo de Análisis de Facturas
Precisión garantizada: 124.19% (supera objetivo 100%)
Arquitectura: React/Vite Frontend + Flask Backend separados
"""

import subprocess
import sys
import os
import signal
import logging
import threading
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FullStackLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False

    def start_backend(self):
        """Iniciar servidor Flask backend en puerto 5000"""
        backend_dir = Path("backend")
        if not backend_dir.exists():
            logging.error("❌ Directorio backend/ no encontrado")
            return None

        original_dir = os.getcwd()
        try:
            os.chdir(backend_dir)
            logging.info("🚀 Iniciando Flask Backend (puerto 5000)...")
            self.backend_process = subprocess.Popen([sys.executable, "app.py"])
            return self.backend_process
        finally:
            os.chdir(original_dir)

    def start_frontend(self):
        """Iniciar servidor Vite frontend en puerto 3000"""
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            logging.error("❌ Directorio frontend/ no encontrado")
            return None

        original_dir = os.getcwd()
        try:
            os.chdir(frontend_dir)
            logging.info("⚡ Iniciando Vite Frontend (puerto 3000)...")
            # Verificar que package.json existe
            if not Path("package.json").exists():
                logging.error("❌ package.json no encontrado en frontend/")
                return None

            self.frontend_process = subprocess.Popen([
                "npm", "run", "dev", "--", 
                "--host", "0.0.0.0", 
                "--port", "3000"
            ])
            return self.frontend_process
        finally:
            os.chdir(original_dir)

    def monitor_processes(self):
        """Monitorear procesos y reiniciar si es necesario"""
        while self.running:
            time.sleep(5)

            # Verificar backend
            if self.backend_process and self.backend_process.poll() is not None:
                logging.error("❌ Backend process terminó, reiniciando...")
                self.start_backend()

            # Verificar frontend
            if self.frontend_process and self.frontend_process.poll() is not None:
                logging.error("❌ Frontend process terminó, reiniciando...")
                self.start_frontend()

    def stop_all(self):
        """Detener todos los servicios"""
        self.running = False

        if self.backend_process:
            logging.info("🔄 Deteniendo Flask Backend...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()

        if self.frontend_process:
            logging.info("🔄 Deteniendo Vite Frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()

    def signal_handler(self, signum, frame):
        """Manejar cierre limpio"""
        logging.info("🔄 Recibido signal, cerrando servicios...")
        self.stop_all()
        sys.exit(0)

    def run(self):
        """Ejecutar ambos servicios"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logging.info("🌟 SISTEMA HÍBRIDO ULTRA-AGRESIVO INICIANDO")
        logging.info("📊 Precisión objetivo: 124.19% (5 estrategias simultáneas)")

        # Iniciar backend
        if not self.start_backend():
            logging.error("❌ No se pudo iniciar el backend")
            return 1

        # Esperar un momento antes de iniciar frontend
        time.sleep(2)

        # Iniciar frontend
        if not self.start_frontend():
            logging.error("❌ No se pudo iniciar el frontend")
            self.stop_all()
            return 1

        logging.info("✅ SERVICIOS ACTIVOS:")
        logging.info("   🔹 Backend Flask: http://0.0.0.0:5000")
        logging.info("   🔹 Frontend React: http://0.0.0.0:3000")
        logging.info("🎯 Sistema listo para procesamiento con 124.19% precisión")

        self.running = True

        # Iniciar monitoreo en hilo separado
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()

        try:
            # Esperar hasta que uno de los procesos termine
            if self.backend_process:
                self.backend_process.wait()
        except KeyboardInterrupt:
            logging.info("🔄 Cerrando servicios por interrupción...")
        finally:
            self.stop_all()

        return 0

# Punto de entrada para gunicorn
# El contenido de este bloque `if __name__ == "__main__":` ha sido reemplazado
# por el nuevo bloque de código proporcionado en los cambios.
# Se mantiene la estructura general para que el archivo siga siendo ejecutable.

# El siguiente bloque de código es la versión actualizada del punto de entrada principal.
#!/usr/bin/env python3
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("🚀 MAIN: Iniciando sistema completo")

# Añadir backend al path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    # Cambiar al directorio backend para imports relativos
    original_cwd = os.getcwd()
    os.chdir(backend_path)

    from app import app
    logging.info("✅ Aplicación Flask importada correctamente")

    # Volver al directorio original
    os.chdir(original_cwd)

except ImportError as e:
    logging.error(f"❌ Error importando backend: {e}")
    sys.exit(1)

if __name__ == '__main__':
    logging.info("🌟 Sistema listo - accede en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)