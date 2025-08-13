#!/usr/bin/env python3
"""
Test del sistema híbrido ultra-agresivo
"""

import sys
import os
sys.path.append('.')

from app.hybrid_ultra_extractor import hybrid_ultra_extractor
from app.db.database import SessionLocal
from app.db.models import ExtractedData
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_hybrid_ultra():
    """Test del extractor híbrido ultra"""
    
    pdf_path = "../data/raw/1BillSummaryJn_1755046685947.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF no encontrado: {pdf_path}")
        return
    
    logger.info("🚀 INICIANDO EXTRACCIÓN HÍBRIDA ULTRA-AGRESIVA")
    logger.info("=" * 70)
    logger.info("OBJETIVO: 372 registros (100% precisión)")
    logger.info("ESTRATEGIAS: Regex + AI + Fuerza Bruta + Caracteres + Reconstrucción")
    logger.info("=" * 70)
    
    try:
        # Ejecutar extracción híbrida ultra
        result = hybrid_ultra_extractor.extract_with_hybrid_ultra(pdf_path, 'all')
        
        if result["success"]:
            records_count = result['records_processed']
            logger.info(f"✅ EXTRACCIÓN HÍBRIDA COMPLETADA: {records_count} registros")
            
            # Análisis detallado
            db = SessionLocal()
            try:
                records = db.query(ExtractedData).filter(
                    ExtractedData.source_file == "1BillSummaryJn_1755046685947.pdf"
                ).order_by(ExtractedData.timestamp).all()
                
                logger.info(f"\n📊 ANÁLISIS FINAL HÍBRIDO:")
                logger.info(f"Total en base de datos: {len(records)} registros")
                
                # Análisis por tipo
                type_counts = {}
                direction_counts = {}
                phone_lines = set()
                
                for record in records:
                    type_counts[record.event_type] = type_counts.get(record.event_type, 0) + 1
                    direction_counts[record.direction] = direction_counts.get(record.direction, 0) + 1
                    if record.phone_line and record.phone_line != "N/A":
                        phone_lines.add(record.phone_line)
                
                logger.info(f"\n🎯 RESULTADOS POR TIPO:")
                for event_type, count in sorted(type_counts.items()):
                    logger.info(f"  {event_type}: {count} registros")
                
                logger.info(f"\n🔄 RESULTADOS POR DIRECCIÓN:")
                for direction, count in sorted(direction_counts.items()):
                    logger.info(f"  {direction}: {count} registros")
                
                logger.info(f"\n📞 LÍNEAS TELEFÓNICAS DETECTADAS:")
                for line in sorted(phone_lines):
                    logger.info(f"  {line}")
                
                # Verificación final de precisión
                expected_total = 372
                percentage = (len(records) / expected_total) * 100
                
                logger.info(f"\n🎯 VERIFICACIÓN FINAL:")
                logger.info(f"  Meta: {expected_total} registros (100%)")
                logger.info(f"  Capturado: {len(records)} registros")
                logger.info(f"  Precisión: {percentage:.2f}%")
                
                if percentage >= 100:
                    logger.info("🏆 ¡MISIÓN CUMPLIDA! 100% DE PRECISIÓN ALCANZADA!")
                elif percentage >= 99:
                    logger.info("🥇 Excelente! Casi 100% de precisión")
                elif percentage >= 95:
                    logger.info("🥈 Muy bueno! Más del 95%")
                else:
                    missing = expected_total - len(records)
                    logger.warning(f"⚠️  Faltan {missing} registros para 100%")
                
                # Mostrar últimos registros extraídos
                logger.info(f"\n📋 ÚLTIMOS 10 REGISTROS EXTRAÍDOS:")
                for i, record in enumerate(records[-10:]):
                    logger.info(f"  [{len(records)-10+i+1}] {record.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                              f"{record.event_type} | {record.direction} | "
                              f"Línea: {record.phone_line}")
                
            finally:
                db.close()
                
        else:
            logger.error("❌ FALLO EN EXTRACCIÓN HÍBRIDA")
            logger.error(f"Error: {result.get('error', 'Desconocido')}")
            
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_ultra()