# gunicorn.conf.py
# Este archivo le dice a Gunicorn cómo encontrar y ejecutar tu aplicación Flask.

# La sintaxis es "nombre_del_archivo_sin_.py:nombre_de_la_variable_flask"
wsgi_app = "app:app"

# Configuración del servidor
bind = "0.0.0.0:5000"
workers = 1 # Para un entorno simple como Replit, 1 es suficiente