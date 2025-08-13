#!/usr/bin/env python3
"""
Test del sistema de extracción 100% confiable
"""

import sys
import os
sys.path.append('.')

from app.bulletproof_extractor import bulletproof_extractor
from app.db.database import SessionLocal
from app.db.models import ExtractedData
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bulletproof_extraction():
    """Test del extractor 100% confiable"""
    
    pdf_path = "data/raw/1BillSummaryJn_1755046685947.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"Archivo PDF no encontrado: {pdf_path}")
        return
    
    logger.info("🎯 INICIANDO EXTRACCIÓN 100% CONFIABLE")
    logger.info("=" * 60)
    
    try:
        # Ejecutar extracción bulletproof
        result = bulletproof_extractor.extract_with_absolute_certainty(pdf_path, 'all')
        
        if result["success"]:
            records_processed = result['records_processed']
            logger.info(f"✅ EXTRACCIÓN COMPLETADA: {records_processed} registros procesados")
            
            # Verificar resultados en base de datos
            db = SessionLocal()
            try:
                records = db.query(ExtractedData).filter(
                    ExtractedData.source_file == "1BillSummaryJn_1755046685947.pdf"
                ).order_by(ExtractedData.timestamp).all()
                
                logger.info(f"\n📊 ANÁLISIS FINAL:")
                logger.info(f"Total registros en BD: {len(records)}")
                
                # Análisis por tipo
                event_counts = {}
                direction_counts = {}
                phone_lines = set()
                
                for record in records:
                    event_counts[record.event_type] = event_counts.get(record.event_type, 0) + 1
                    direction_counts[record.direction] = direction_counts.get(record.direction, 0) + 1
                    if record.phone_line and record.phone_line != "N/A":
                        phone_lines.add(record.phone_line)
                
                logger.info(f"\n🎯 RESULTADOS POR TIPO:")
                for event_type, count in event_counts.items():
                    logger.info(f"  {event_type}: {count} registros")
                
                logger.info(f"\n🔄 RESULTADOS POR DIRECCIÓN:")
                for direction, count in direction_counts.items():
                    logger.info(f"  {direction}: {count} registros")
                
                logger.info(f"\n📞 LÍNEAS TELEFÓNICAS:")
                for line in sorted(phone_lines):
                    logger.info(f"  {line}")
                
                # Mostrar ejemplos
                logger.info(f"\n📋 EJEMPLOS DE REGISTROS:")
                for i, record in enumerate(records[:5]):
                    logger.info(f"  [{i+1}] {record.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                              f"{record.event_type} | {record.direction} | "
                              f"Línea: {record.phone_line} | Contacto: {record.contact}")
                
                # Verificación de objetivo 372 registros
                expected_total = 372
                percentage = (len(records) / expected_total) * 100
                
                logger.info(f"\n🎯 VERIFICACIÓN DE OBJETIVO:")
                logger.info(f"  Esperado: {expected_total} registros")
                logger.info(f"  Extraído: {len(records)} registros")
                logger.info(f"  Precisión: {percentage:.1f}%")
                
                if percentage >= 100:
                    logger.info("🏆 ¡OBJETIVO 100% ALCANZADO!")
                elif percentage >= 95:
                    logger.info("✅ Excelente precisión (95%+)")
                else:
                    logger.warning(f"⚠️  Precisión por debajo del objetivo: {percentage:.1f}%")
                
            finally:
                db.close()
                
        else:
            logger.error("❌ FALLO EN LA EXTRACCIÓN")
            logger.error(f"Error: {result.get('error', 'Desconocido')}")
            
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()

def verify_database_integrity():
    """Verificar integridad de la base de datos"""
    
    logger.info("\n🔍 VERIFICANDO INTEGRIDAD DE BASE DE DATOS")
    
    db = SessionLocal()
    try:
        # Contar total de registros
        total_count = db.query(ExtractedData).count()
        logger.info(f"Total registros en sistema: {total_count}")
        
        # Contar por archivo fuente
        files = db.query(ExtractedData.source_file).distinct().all()
        for file_tuple in files:
            filename = file_tuple[0]
            count = db.query(ExtractedData).filter(ExtractedData.source_file == filename).count()
            logger.info(f"  {filename}: {count} registros")
        
        # Verificar campos nulos
        null_checks = {
            'phone_line': db.query(ExtractedData).filter(ExtractedData.phone_line.is_(None)).count(),
            'event_type': db.query(ExtractedData).filter(ExtractedData.event_type.is_(None)).count(),
            'timestamp': db.query(ExtractedData).filter(ExtractedData.timestamp.is_(None)).count(),
            'direction': db.query(ExtractedData).filter(ExtractedData.direction.is_(None)).count()
        }
        
        logger.info(f"\n🔍 VERIFICACIÓN DE CAMPOS NULOS:")
        for field, null_count in null_checks.items():
            status = "❌" if null_count > 0 else "✅"
            logger.info(f"  {status} {field}: {null_count} nulos")
        
        logger.info("✅ Verificación de integridad completada")
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 SISTEMA DE EXTRACCIÓN 100% CONFIABLE")
    logger.info("=" * 60)
    
    # Test principal
    test_bulletproof_extraction()
    
    # Verificación de integridad
    verify_database_integrity()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ PRUEBA COMPLETADA")