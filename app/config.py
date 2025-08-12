# app/config.py
# ¡ESTE ES EL ARCHIVO MÁS IMPORTANTE PARA LA EXTRACCIÓN DE DATOS!
# Modifica los patrones de REGEX a continuación para que coincidan con el formato de TUS facturas PDF.

import re

# --- Patrones de Expresiones Regulares (REGEX) ---
# He incluido patrones de ejemplo. Es muy probable que necesites ajustarlos.
# Herramienta recomendada para probar tus patrones: https://regex101.com/

# Ejemplo de línea a buscar: "Jul 15  10:30 PM  IN  (123) 456-7890  New York, NY  G  15"
CALL_PATTERN = re.compile(
    r"(\w{3})\s+(\d{1,2})\s+"          # Grupo 1 y 2: Mes y Día ("Jul 15")
    r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s+"  # Grupo 3: Hora ("10:30 PM")
    r"(IN|OUT)\s+"                     # Grupo 4: Tipo de llamada ("IN")
    r"\((.+?)\)\s+"                    # Grupo 5: Número de teléfono ("(123) 456-7890")
    r"(.+?)\s+"                        # Grupo 6: Descripción/Lugar ("New York, NY")
    r"([A-Z])?\s+"                     # Grupo 7: Código opcional ("G")
    r"(\d+)\n",                        # Grupo 8: Minutos ("15")
    re.MULTILINE
)

# Ejemplo: "Aug 02  08:15 AM  OUT  (987) 654-3210  Some Place  TXT"
MESSAGE_PATTERN = re.compile(
    r"(\w{3})\s+(\d{1,2})\s+"          # Mes y Día
    r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s+"  # Hora
    r"(IN|OUT)\s+"                     # Tipo de mensaje
    r"(.+?)\s+"                        # Contacto/Número
    r"(.+?)\s+"                        # Destino/Descripción
    r"(TXT|PIC|MSG)\n",                # Formato
    re.MULTILINE
)

# Ejemplo: "Jun 05 Mobile Internet 1,234.56"
DATA_USAGE_PATTERN = re.compile(
    r"(\w{3})\s+(\d{1,2})\s+"          # Mes y Día
    r"Mobile Internet\s+"              # Texto literal
    r"([\d,]+\.\d+)\n",                # MB Usados (con comas)
    re.MULTILINE
)