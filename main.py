import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from app.db.database import init_db
from app.extractors.main_extractor import process_pdf_files
from app.db.queries import get_all_data, get_summary_data, has_data, get_chronological_data, get_available_files
from app.services.ai_service import generate_ai_content
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.config['UPLOAD_FOLDER'] = 'data/raw'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/timeline_app')
def timeline_app():
    return render_template('timeline_app_upload.html')

@app.route('/notes')
def notes_app():
    return render_template('notes.html')

@app.route('/viewer')
def viewer_app():
    return render_template('viewer.html')

@app.route('/analyzer')
def analyzer_app():
    if not has_data():
        return render_template('analyzer_empty.html')
    return render_template('analyzer.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No se encontraron archivos'}), 400
    
    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No se seleccionaron archivos'}), 400
    
    filepaths = []
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            filepaths.append(filepath)
    
    try:
        counts = process_pdf_files(filepaths)
        total_records = sum(counts.values())
        
        if total_records == 0:
            message = f"{len(filepaths)} archivo(s) procesado(s), pero no se encontraron datos válidos. Revisa el formato."
            return jsonify({'message': message, 'status': 'warning'}), 200
        
        message = f'Éxito. {total_records} registros fueron actualizados desde {len(filepaths)} archivo(s).'
        return jsonify({'message': message, 'status': 'success'}), 200
        
    except Exception as e:
        app.logger.error(f"Error processing PDFs: {str(e)}")
        return jsonify({'error': f'Error crítico durante el procesamiento: {str(e)}'}), 500

@app.route('/api/data')
def get_data():
    return jsonify(get_all_data())

@app.route('/api/summary')
def get_summary():
    return jsonify(get_summary_data())

@app.route('/api/chronological')
def get_chronological():
    """New endpoint for chronological paginated data"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    file_filter = request.args.get('file_filter', 'all')  # 'all' or specific filename
    
    # Validate per_page values
    if per_page not in [25, 50, 100]:
        per_page = 25
    
    try:
        result = get_chronological_data(page=page, per_page=per_page, file_filter=file_filter)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting chronological data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files')
def get_files():
    """New endpoint to get available source files"""
    try:
        files = get_available_files()
        return jsonify({'files': files})
    except Exception as e:
        app.logger.error(f"Error getting files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/gemini', methods=['POST'])
def gemini_proxy():
    if not os.getenv("GOOGLE_API_KEY"):
        return jsonify({"error": "La API de IA no está configurada."}), 500
    
    data = request.json
    prompt = data.get('prompt') if data else None
    
    if not prompt:
        return jsonify({"error": "El prompt es requerido."}), 400
    
    success, content = generate_ai_content(prompt)
    
    if success:
        return jsonify({"text": content})
    else:
        return jsonify({"error": content}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
