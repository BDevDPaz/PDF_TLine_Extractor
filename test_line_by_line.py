#!/usr/bin/env python3
"""
Test del extractor línea por línea ultra-preciso
"""

import sys
import os
sys.path.append('.')

from app.line_by_line_extractor import line_by_line_extractor
from app.db.database import SessionLocal
from app.db.models import ExtractedData
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_line_by_line_extraction():
    """Test del extractor línea por línea"""
    
    pdf_path = "data/raw/1BillSummaryJn_1755046685947.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF no encontrado: {pdf_path}")
        return False
    
    logger.info("🎯 INICIANDO EXTRACCIÓN LÍNEA POR LÍNEA ULTRA-PRECISA")
    logger.info("=" * 80)
    logger.info("BASADO EN: Capacidad de selección individual mostrada en imagen")
    logger.info("MÉTODO: Análisis estructurado línea por línea")
    logger.info("OBJETIVO: Precisión total en cada registro individual")
    logger.info("=" * 80)
    
    try:
        # Ejecutar extracción línea por línea
        result = line_by_line_extractor.extract_with_line_precision(pdf_path, 'all')
        
        if result["success"]:
            records_count = result['records_processed']
            logger.info(f"✅ EXTRACCIÓN LÍNEA POR LÍNEA COMPLETADA: {records_count} registros")
            
            # Análisis detallado de resultados
            db = SessionLocal()
            try:
                records = db.query(ExtractedData).filter(
                    ExtractedData.source_file == "1BillSummaryJn_1755046685947.pdf"
                ).order_by(ExtractedData.timestamp).all()
                
                logger.info(f"\n📊 ANÁLISIS LÍNEA POR LÍNEA:")
                logger.info(f"Total registros procesados: {len(records)}")
                
                # Análisis por tipo de evento
                event_analysis = {}
                direction_analysis = {}
                contact_analysis = set()
                
                for record in records:
                    # Contar por tipo
                    event_analysis[record.event_type] = event_analysis.get(record.event_type, 0) + 1
                    
                    # Contar por dirección
                    direction_analysis[record.direction] = direction_analysis.get(record.direction, 0) + 1
                    
                    # Recopilar contactos únicos
                    if record.contact and record.contact != "N/A" and len(record.contact) >= 10:
                        contact_analysis.add(record.contact)
                
                logger.info(f"\n🎯 ANÁLISIS POR TIPO DE EVENTO:")
                for event_type, count in sorted(event_analysis.items()):
                    logger.info(f"  {event_type}: {count} registros")
                
                logger.info(f"\n🔄 ANÁLISIS POR DIRECCIÓN:")
                for direction, count in sorted(direction_analysis.items()):
                    logger.info(f"  {direction}: {count} registros")
                
                logger.info(f"\n📞 CONTACTOS ÚNICOS DETECTADOS:")
                for contact in sorted(contact_analysis):
                    logger.info(f"  {contact}")
                
                # Mostrar ejemplos de registros extraídos
                logger.info(f"\n📋 PRIMEROS 15 REGISTROS EXTRAÍDOS:")
                for i, record in enumerate(records[:15]):
                    timestamp_str = record.timestamp.strftime('%Y-%m-%d %H:%M')
                    logger.info(f"  [{i+1:2}] {timestamp_str} | {record.event_type:8} | "
                              f"{record.direction:8} | {record.contact[:12]:12} | {record.value}")
                
                # Verificación de calidad de datos
                logger.info(f"\n🔍 VERIFICACIÓN DE CALIDAD:")
                
                # Campos no nulos
                null_checks = {
                    'timestamp': sum(1 for r in records if r.timestamp is None),
                    'event_type': sum(1 for r in records if not r.event_type),
                    'direction': sum(1 for r in records if not r.direction),
                    'contact': sum(1 for r in records if not r.contact)
                }
                
                for field, null_count in null_checks.items():
                    status = "✅" if null_count == 0 else "❌"
                    logger.info(f"  {status} {field}: {null_count} valores nulos")
                
                # Distribución temporal
                if records:
                    earliest = min(r.timestamp for r in records if r.timestamp)
                    latest = max(r.timestamp for r in records if r.timestamp)
                    logger.info(f"  📅 Rango temporal: {earliest.strftime('%Y-%m-%d')} a {latest.strftime('%Y-%m-%d')}")
                
                # Evaluación final
                expected_minimum = 372
                percentage = (len(records) / expected_minimum) * 100
                
                logger.info(f"\n🎯 EVALUACIÓN FINAL LÍNEA POR LÍNEA:")
                logger.info(f"  Objetivo mínimo: {expected_minimum} registros")
                logger.info(f"  Registros extraídos: {len(records)}")
                logger.info(f"  Precisión: {percentage:.2f}%")
                
                if percentage >= 100:
                    logger.info("🏆 ¡EXTRACCIÓN LÍNEA POR LÍNEA EXITOSA!")
                    logger.info("✅ Objetivo 100% alcanzado con análisis estructurado")
                    return True
                elif percentage >= 95:
                    logger.info("🥇 Excelente precisión con método línea por línea")
                    return True
                else:
                    missing = expected_minimum - len(records)
                    logger.warning(f"⚠️  Método línea por línea: Faltan {missing} registros")
                    return False
                
            finally:
                db.close()
                
        else:
            logger.error("❌ FALLO EN EXTRACCIÓN LÍNEA POR LÍNEA")
            logger.error(f"Error: {result.get('error', 'Desconocido')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO en línea por línea: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def compare_extraction_methods():
    """Comparar método línea por línea con híbrido ultra"""
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 COMPARACIÓN DE MÉTODOS DE EXTRACCIÓN")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # Contar registros por archivo fuente para comparar métodos
        files = db.query(ExtractedData.source_file).distinct().all()
        
        for file_tuple in files:
            filename = file_tuple[0]
            count = db.query(ExtractedData).filter(ExtractedData.source_file == filename).count()
            
            method = "Desconocido"
            if "1755046685947" in filename:
                method = "Línea por línea / Híbrido Ultra"
            
            logger.info(f"  {filename}: {count} registros ({method})")
        
        total_system_records = db.query(ExtractedData).count()
        logger.info(f"\nTotal en sistema: {total_system_records} registros")
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 TEST DEL EXTRACTOR LÍNEA POR LÍNEA")
    logger.info("Basado en la capacidad de selección mostrada en la imagen")
    
    success = test_line_by_line_extraction()
    compare_extraction_methods()
    
    if success:
        logger.info("\n✅ EXTRACCIÓN LÍNEA POR LÍNEA VERIFICADA")
    else:
        logger.info("\n⚠️  EXTRACCIÓN LÍNEA POR LÍNEA REQUIERE AJUSTES")
    
    logger.info("=" * 80)