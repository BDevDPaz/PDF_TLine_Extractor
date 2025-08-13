#!/usr/bin/env python3
"""
Script para probar y comparar la extracción de datos del PDF
con el sistema robusto implementado
"""

import sys
import os
sys.path.append('.')

from app.robust_pdf_extractor import robust_extractor
from app.db.database import SessionLocal
from app.db.models import ExtractedData
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_extraction():
    """Procesa el PDF de prueba y muestra resultados detallados"""
    
    pdf_path = "data/raw/1BillSummaryJn_1755046685947.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"Archivo PDF no encontrado: {pdf_path}")
        return
    
    logger.info(f"Iniciando procesamiento del PDF: {pdf_path}")
    
    try:
        # Procesar todo el PDF
        result = robust_extractor.extract_data_robust(pdf_path, 'all')
        
        logger.info(f"Resultado del procesamiento: {result}")
        
        if result["success"]:
            logger.info(f"✅ Extracción exitosa: {result['records_processed']} registros procesados")
            
            # Consultar datos extraídos
            db = SessionLocal()
            try:
                records = db.query(ExtractedData).filter(
                    ExtractedData.source_file == "1BillSummaryJn_1755046685947.pdf"
                ).order_by(ExtractedData.timestamp).all()
                
                logger.info(f"\n📊 ANÁLISIS DE DATOS EXTRAÍDOS:")
                logger.info(f"Total de registros: {len(records)}")
                
                # Análisis por tipo de evento
                event_counts = {}
                direction_counts = {}
                phone_lines = set()
                
                for record in records:
                    # Contar tipos de eventos
                    event_counts[record.event_type] = event_counts.get(record.event_type, 0) + 1
                    
                    # Contar direcciones
                    direction_counts[record.direction] = direction_counts.get(record.direction, 0) + 1
                    
                    # Recopilar líneas telefónicas
                    if record.phone_line and record.phone_line != "N/A":
                        phone_lines.add(record.phone_line)
                
                logger.info(f"\n🔢 ESTADÍSTICAS POR TIPO:")
                for event_type, count in event_counts.items():
                    logger.info(f"  {event_type}: {count} registros")
                
                logger.info(f"\n🔄 ESTADÍSTICAS POR DIRECCIÓN:")
                for direction, count in direction_counts.items():
                    logger.info(f"  {direction}: {count} registros")
                
                logger.info(f"\n📞 LÍNEAS TELEFÓNICAS DETECTADAS:")
                for line in sorted(phone_lines):
                    logger.info(f"  {line}")
                
                # Mostrar algunos ejemplos de registros
                logger.info(f"\n📋 EJEMPLOS DE REGISTROS EXTRAÍDOS:")
                for i, record in enumerate(records[:10]):  # Primeros 10 registros
                    logger.info(f"  [{i+1}] {record.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                              f"{record.event_type} | {record.direction} | "
                              f"Línea: {record.phone_line} | Contacto: {record.contact} | "
                              f"Valor: {record.value}")
                
                if len(records) > 10:
                    logger.info(f"  ... y {len(records) - 10} registros más")
                
            finally:
                db.close()
        else:
            logger.error("❌ Fallo en la extracción")
            
    except Exception as e:
        logger.error(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_pdf_content():
    """Analiza el contenido del PDF para validar campos detectados"""
    
    logger.info("\n🔍 ANÁLISIS MANUAL DEL PDF PARA COMPARACIÓN:")
    
    # Información esperada basada en la revisión manual del PDF
    expected_data = {
        "bill_date": "Jun 16, 2024",
        "account": "999019933",
        "phone_lines": [
            "(747) 240-1916",  # Línea principal con actividad
            "(818) 301-8406",  # Línea con actividad
            "(747) 230-1993",  # Línea con actividad 
            "(818) 466-1106",  # Línea con actividad mínima
            "(818) 466-3424",  # Línea nueva
            "(818) 466-3504",  # Línea nueva
            "(818) 466-3558"   # Dispositivo conectado (watch)
        ],
        "expected_activities": {
            "calls": {
                "(747) 240-1916": 2,  # Jun 16: 6:16 PM OUT, 6:26 PM IN
                "(818) 301-8406": 4,  # Jun 16: múltiples llamadas
                "(747) 230-1993": 1,  # Jun 16: 10:00 PM IN
                "(818) 466-3558": 7   # Jun 16: múltiples llamadas
            },
            "messages": {
                "(747) 240-1916": 25,  # Múltiples mensajes TXT
                "(818) 301-8406": 50,  # Múltiples mensajes PIC
                "(747) 230-1993": 3,   # Pocos mensajes
                "(818) 466-1106": 1,   # 1 mensaje
                "(818) 466-3558": 25   # Múltiples mensajes
            },
            "data": {
                "(818) 301-8406": "7,525.7945 MB",
                "(747) 230-1993": "111.7145 MB",
                "(818) 466-1106": "21.3396 MB"
            }
        }
    }
    
    logger.info(f"📅 Fecha de factura esperada: {expected_data['bill_date']}")
    logger.info(f"📱 Líneas telefónicas esperadas: {len(expected_data['phone_lines'])}")
    
    for line in expected_data['phone_lines']:
        logger.info(f"  - {line}")
    
    logger.info(f"\n📊 ACTIVIDADES ESPERADAS:")
    logger.info(f"  Llamadas: {sum(expected_data['expected_activities']['calls'].values())} total")
    logger.info(f"  Mensajes: {sum(expected_data['expected_activities']['messages'].values())} total")
    logger.info(f"  Uso de datos: {len(expected_data['expected_activities']['data'])} líneas con datos")
    
    return expected_data

if __name__ == "__main__":
    logger.info("🔬 INICIANDO COMPARACIÓN EXHAUSTIVA DE EXTRACCIÓN")
    logger.info("=" * 60)
    
    # Paso 1: Analizar contenido esperado
    expected = analyze_pdf_content()
    
    logger.info("\n" + "=" * 60)
    
    # Paso 2: Procesar PDF con sistema robusto
    test_pdf_extraction()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ COMPARACIÓN COMPLETADA")