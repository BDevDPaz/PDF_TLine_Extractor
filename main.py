import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename
from app.db.database import init_db, SessionLocal
from app.db.models import ExtractedData
from app.regex_processor import extract_data_with_regex
from app.ai_chat import get_chat_response

# --- Configuración de la App ---
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['UPLOAD_FOLDER'] = 'data/raw'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_db()

# --- Rutas del Frontend ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Rutas de la API (Backend) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'pdfFile' not in request.files:
        return jsonify({'error': 'No se encontró el archivo PDF'}), 400
    file = request.files['pdfFile']
    if not file or file.filename == '' or file.filename is None:
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'message': 'Archivo subido con éxito', 'filename': filename})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/process', methods=['POST'])
def process_file():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se proporcionaron datos JSON'}), 400
    
    filename = data.get('filename')
    pages = data.get('pages')
    if not filename or pages is None:
        return jsonify({'error': 'Falta el nombre de archivo o las páginas'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'El archivo no existe en el servidor'}), 404

    # Comentamos la verificación de Google API Key ya que usamos regex ahora
    # if not os.getenv("GOOGLE_API_KEY"): 
    #     return jsonify({"error": "La API Key de Google no está configurada en los Secrets."}), 500
    
    try:
        record_count = extract_data_with_regex(filepath, pages)
        if record_count > 0:
            return jsonify({'message': f'Éxito: Se extrajeron {record_count} registros usando patrones avanzados.'})
        else:
            return jsonify({'message': 'El procesamiento completó pero no se encontraron datos estructurados que extraer.'}), 200
    except Exception as e:
        return jsonify({'error': f'Error en la IA: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    if not os.getenv("GOOGLE_API_KEY"): 
        return jsonify({"error": "La API Key de Google no está configurada en los Secrets."}), 500
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se proporcionaron datos JSON'}), 400
    
    user_prompt = data.get('prompt')
    history = data.get('history', [])
    if not user_prompt:
        return jsonify({'error': 'El prompt está vacío'}), 400
    try:
        response_text = get_chat_response(user_prompt, history)
        return jsonify({'response': response_text})
    except Exception as e:
        return jsonify({'error': f'Error en la IA: {str(e)}'}), 500

@app.route('/api/get-data', methods=['GET'])
def get_data():
    db = SessionLocal()
    try:
        data = db.query(ExtractedData).all()
        results = []
        for item in data:
            result = {
                "id": item.id, 
                "source_file": item.source_file,
                "phone_line": item.phone_line if hasattr(item, 'phone_line') else None,
                "event_type": item.event_type,
                "timestamp": item.timestamp.isoformat() if item.timestamp is not None else None,
                "direction": item.direction if hasattr(item, 'direction') else None,
                "contact": item.contact if hasattr(item, 'contact') else None,
                "description": item.description if hasattr(item, 'description') else None,
                "value": item.value if hasattr(item, 'value') else None
            }
            results.append(result)
        return jsonify(results)
    finally:
        db.close()

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    db = SessionLocal()
    try:
        query = db.query(ExtractedData)
        df = pd.read_sql(query.statement, query.session.bind)
        
        # Formatear el timestamp para legibilidad en CSV
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        return Response(
            df.to_csv(index=False),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=reporte_de_datos.csv"}
        )
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)