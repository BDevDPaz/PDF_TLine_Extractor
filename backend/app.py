import os
import threading
import json
from datetime import date, datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import SessionLocal, Line, CallEvent, TextEvent, DataEvent, init_db
from parser import PDFParser
import ai_enrichment

# Helper para convertir objetos SQLAlchemy a diccionarios
def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, (datetime, date)):
            d[column.name] = value.isoformat()
        else:
            d[column.name] = value
    return d

# --- Inicialización de la App ---
app = Flask(__name__)
CORS(app) # Permitir peticiones desde el frontend
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear las tablas de la base de datos si no existen
init_db()

# --- Endpoints de la API ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó archivo"}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    
    try:
        parser = PDFParser(filepath)
        parser.run_extraction()
        # Iniciar el enriquecimiento de IA en un hilo para no bloquear la respuesta
        ai_thread = threading.Thread(target=ai_enrichment.categorize_phone_numbers)
        ai_thread.start()
        return jsonify({"message": "Archivo procesado. El enriquecimiento con IA se está ejecutando."}), 200
    except Exception as e:
        # Imprimir el error en la consola del backend para depuración
        print(f"Error detallado al procesar el PDF: {e}")
        return jsonify({"error": f"Error al procesar el PDF: {str(e)}"}), 500

@app.route('/api/lines', methods=['GET'])
def get_lines():
    session = SessionLocal()
    lines_db = session.query(Line).all()
    lines = [{"id": l.id, "phone_number": l.phone_number} for l in lines_db]
    session.close()
    return jsonify(lines)

@app.route('/api/lines/<int:line_id>/details', methods=['GET'])
def get_line_details(line_id):
    session = SessionLocal()
    line = session.query(Line).get(line_id)
    if not line:
        session.close(); return jsonify({"error": "Línea no encontrada"}), 404
    
    # Usar el helper row2dict para una serialización segura a JSON
    details = {
        "calls": [row2dict(row) for row in line.call_events],
        "texts": [row2dict(row) for row in line.text_events],
        "data": [row2dict(row) for row in line.data_events],
    }
    session.close()
    return jsonify(details)

@app.route('/api/query', methods=['POST'])
def handle_query():
    if not ai_enrichment.model:
        return jsonify({"answer": "La IA no está configurada en el servidor."})

    data = request.get_json()
    user_question = data.get('question')
    line_id = data.get('line_id')

    if not user_question or not line_id:
        return jsonify({"error": "Faltan datos en la petición"}), 400
    
    session = SessionLocal()
    line = session.query(Line).get(line_id)
    if not line:
        session.close(); return jsonify({"error": "Línea no encontrada"}), 404
        
    calls = line.call_events[:20]
    data_context = f"Datos para la línea {line.phone_number}:\n"
    data_context += "Llamadas recientes:\n"
    data_context += "\n".join([f"- Llamada a {c.counterpart_number} ({c.ai_category}) el {c.timestamp.strftime('%d-%b')} duró {c.duration_minutes} min." for c in calls])
    
    prompt = f"""Eres un asistente experto en análisis de facturas. Sé conciso y amable.
    Basándote estrictamente en el siguiente contexto, responde la pregunta del usuario.
    Si la respuesta no se encuentra en los datos, di "No tengo suficiente información sobre eso en los datos recientes".

    Contexto:
    {data_context}

    Pregunta del usuario: "{user_question}"
    """
    
    try:
        response = ai_enrichment.model.generate_content(prompt)
        session.close()
        return jsonify({"answer": response.text})
    except Exception as e:
        session.close()
        return jsonify({"answer": f"Error al contactar la IA: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)