import pdfplumber
import json
import pandas as pd

def procesar(ruta_archivo):
    eventos = []
    try:
        with pdfplumber.open(ruta_archivo) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                texto = page.extract_text()
                if texto and texto.strip():
                    timestamp = None
                    try:
                        timestamp = pd.to_datetime(texto, infer_datetime_format=True, errors='coerce').to_pydatetime()
                    except Exception: pass

                    if timestamp:
                        eventos.append({
                            'timestamp': timestamp,
                            'tipo_evento': f'PDF Página {i}',
                            'datos_json': json.dumps({"contenido": texto.strip()}, indent=2, ensure_ascii=False)
                        })
    except Exception as e:
        print(f"Error en procesador PDF: {e}")
    return eventos
