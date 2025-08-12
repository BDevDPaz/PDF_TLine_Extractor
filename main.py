import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename
from app.db.database import init_db, SessionLocal
from app.db.models import ExtractedData
from app.data_extractor import process_pdf

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

    try:
        record_count = process_pdf(filepath, pages)
        if record_count > 0:
            return jsonify({'message': f'{record_count} registros extraídos y guardados con éxito.'})
        else:
            return jsonify({'message': 'Proceso completado, pero no se encontraron datos válidos con los patrones actuales. Revisa app/config.py'}), 200
    except Exception as e:
        return jsonify({'error': f'Error durante el procesamiento: {str(e)}'}), 500

@app.route('/api/get-data', methods=['GET'])
def get_data():
    db = SessionLocal()
    try:
        data = db.query(ExtractedData).all()
        results = [
            {
                "id": item.id, "source_file": item.source_file, "event_type": item.event_type,
                "timestamp": item.timestamp.isoformat(), "detail_1": item.detail_1, "detail_2": item.detail_2,
                "detail_3": item.detail_3, "numeric_value": item.numeric_value
            } for item in data
        ]
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