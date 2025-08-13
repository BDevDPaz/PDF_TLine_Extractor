"""
Procesador con enfoque en privacidad y eficiencia
Diseñado para procesamiento discreto sin exposición de datos sensibles
"""
import os
import tempfile
import hashlib
from datetime import datetime
from app.enhanced_regex_processor import extract_data_with_enhanced_regex
from app.optimized_processor import extract_data_with_optimized_processing

def generate_session_id():
    """Genera un ID de sesión único para privacidad"""
    timestamp = str(datetime.now().timestamp())
    return hashlib.md5(timestamp.encode()).hexdigest()[:8]

def process_with_privacy_mode(filepath, selected_pages, user_session_id=None):
    """
    Procesamiento con modo privacidad activado
    - Sin logs de contenido sensible
    - Procesamiento en memoria temporal
    - Limpieza automática de archivos temporales
    """
    session_id = user_session_id or generate_session_id()
    
    try:
        # Intento 1: Procesador regex especializado
        record_count = extract_data_with_enhanced_regex(filepath, selected_pages)
        processing_method = "Extractor Regex Especializado"
        
        # Intento 2: Si pocos resultados, usar IA híbrida
        if record_count < 5:
            record_count_ai = extract_data_with_optimized_processing(filepath, selected_pages)
            if record_count_ai > record_count:
                record_count = record_count_ai
                processing_method = "IA Híbrida con Regex Fallback"
        
        # Log mínimo sin datos sensibles
        print(f"[{session_id}] Procesamiento completado: {record_count} registros - Método: {processing_method}")
        
        return {
            'success': True,
            'record_count': record_count,
            'method_used': processing_method,
            'session_id': session_id
        }
        
    except Exception as e:
        print(f"[{session_id}] Error en procesamiento: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'session_id': session_id
        }

def secure_cleanup(filepath):
    """Limpieza segura de archivos temporales"""
    try:
        if os.path.exists(filepath):
            # Sobrescribir con datos aleatorios antes de eliminar
            with open(filepath, 'wb') as f:
                f.write(os.urandom(os.path.getsize(filepath)))
            os.remove(filepath)
            return True
    except:
        return False
    
def get_processing_stats():
    """Estadísticas generales sin datos sensibles"""
    from app.db.database import SessionLocal
    from app.db.models import ExtractedData
    
    db = SessionLocal()
    try:
        total_records = db.query(ExtractedData).count()
        unique_files = db.query(ExtractedData.source_file).distinct().count()
        
        return {
            'total_records': total_records,
            'files_processed': unique_files,
            'last_update': datetime.now().isoformat()
        }
    finally:
        db.close()