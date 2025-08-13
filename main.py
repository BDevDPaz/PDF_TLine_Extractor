import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename
from datetime import datetime
from app.db.database import init_db, SessionLocal
from app.db.models import ExtractedData
from app.privacy_processor import process_with_privacy_mode, get_processing_stats
from app.advanced_filters import AdvancedDataFilter, PrivateCSVExporter
from app.ai_chat import get_chat_response
from app.chat_file_handler import process_chat_file_upload, export_chat_history

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

    # Verificar API Key (el sistema híbrido la usa cuando es posible)
    if not os.getenv("GOOGLE_API_KEY"): 
        print("Warning: No Google API Key found, using regex-only mode")
    
    try:
        # Usar procesador con modo privacidad
        session_id = request.headers.get('X-Session-ID') or None
        result = process_with_privacy_mode(filepath, pages, session_id)
        
        if result['success']:
            return jsonify({
                'message': f'Procesamiento completado: {result["record_count"]} registros extraídos',
                'method': result['method_used'],
                'session_id': result['session_id']
            })
        else:
            return jsonify({'error': f'Error en procesamiento: {result["error"]}'}), 500
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
    """Endpoint con filtros avanzados y modo privacidad"""
    try:
        with AdvancedDataFilter() as filter_engine:
            # Obtener parámetros de filtrado
            filters = {}
            if request.args.get('event_type'):
                filters['event_type'] = request.args.get('event_type').split(',')
            if request.args.get('direction'):
                filters['direction'] = request.args.get('direction').split(',')
            if request.args.get('phone_line'):
                filters['phone_line'] = request.args.get('phone_line').split(',')
            if request.args.get('date_from'):
                filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
            if request.args.get('date_to'):
                filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
            
            # Obtener datos filtrados
            data = filter_engine.get_filtered_data(filters)
            
            # Formatear respuesta sin exponer datos sensibles innecesariamente
            results = []
            for item in data:
                result = {
                    "id": item.id,
                    "source_file": item.source_file,
                    "phone_line": item.phone_line,
                    "event_type": item.event_type,
                    "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                    "direction": item.direction,
                    "contact": item.contact,
                    "description": item.description,
                    "value": item.value
                }
                results.append(result)
            
            return jsonify({
                'data': results,
                'total_records': len(results),
                'filters_applied': list(filters.keys())
            })
    except Exception as e:
        return jsonify({'error': f'Error obteniendo datos: {str(e)}'}), 500

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Export CSV con opciones de privacidad"""
    try:
        # Parámetros de privacidad
        anonymize = request.args.get('anonymize', 'false').lower() == 'true'
        
        with AdvancedDataFilter() as filter_engine:
            # Aplicar los mismos filtros que en get-data
            filters = {}
            if request.args.get('event_type'):
                filters['event_type'] = request.args.get('event_type').split(',')
            if request.args.get('direction'):
                filters['direction'] = request.args.get('direction').split(',')
            if request.args.get('phone_line'):
                filters['phone_line'] = request.args.get('phone_line').split(',')
            if request.args.get('date_from'):
                filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
            if request.args.get('date_to'):
                filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
            
            data = filter_engine.get_filtered_data(filters)
            
            # Generar CSV con opciones de privacidad
            csv_content = PrivateCSVExporter.generate_secure_csv(data, anonymize_contacts=anonymize)
            
            filename = f"datos_comunicacion_{'anonimo' if anonymize else 'completo'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                csv_content,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        return jsonify({'error': f'Error exportando CSV: {str(e)}'}), 500

@app.route('/api/chat-file', methods=['POST'])
def chat_file_handler():
    """Maneja archivos PDF subidos directamente al chat"""
    if 'file' not in request.files or 'question' not in request.form:
        return jsonify({'error': 'Falta archivo o pregunta'}), 400
    
    file = request.files['file']
    question = request.form['question']
    
    if file.filename == '' or not question.strip():
        return jsonify({'error': 'Archivo vacío o pregunta vacía'}), 400
    
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400
    
    try:
        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        
        # Procesar con IA
        response = process_chat_file_upload(temp_path, question)
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': f'Error procesando archivo: {str(e)}'}), 500

@app.route('/api/export-chat', methods=['POST'])
def export_chat_history_endpoint():
    """Exporta el historial de chat"""
    data = request.get_json()
    if not data or 'history' not in data:
        return jsonify({'error': 'No se proporcionó historial'}), 400
    
    try:
        chat_text = export_chat_history(data['history'])
        
        # Crear respuesta como archivo descargable
        response = Response(
            chat_text,
            mimetype='text/plain',
            headers={'Content-Disposition': 'attachment; filename=historial_chat.txt'}
        )
        return response
    except Exception as e:
        return jsonify({'error': f'Error exportando chat: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)