#!/usr/bin/env python3
"""
Test simple del extractor línea por línea
"""

import sys
import os
sys.path.append('.')

# Verificar que las dependencias estén disponibles
try:
    from app.line_by_line_extractor import line_by_line_extractor
    from app.db.database import SessionLocal
    from app.db.models import ExtractedData
    import logging
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    def simple_line_test():
        """Test simple del extractor línea por línea"""
        
        pdf_path = "data/raw/1BillSummaryJn_1755046685947.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF no encontrado: {pdf_path}")
            return
        
        logger.info("🎯 TEST SIMPLE LÍNEA POR LÍNEA")
        logger.info("Basado en la imagen de selección individual")
        
        try:
            result = line_by_line_extractor.extract_with_line_precision(pdf_path, 'all')
            
            if result["success"]:
                logger.info(f"✅ Éxito: {result['records_processed']} registros")
                
                # Verificar en BD
                db = SessionLocal()
                try:
                    count = db.query(ExtractedData).filter(
                        ExtractedData.source_file == "1BillSummaryJn_1755046685947.pdf"
                    ).count()
                    
                    logger.info(f"Registros en BD: {count}")
                    
                    if count >= 372:
                        logger.info("🏆 OBJETIVO ALCANZADO CON MÉTODO LÍNEA POR LÍNEA")
                    else:
                        logger.info(f"Progreso: {count}/372 registros")
                        
                finally:
                    db.close()
            else:
                logger.error(f"Error: {result.get('error', 'Desconocido')}")
                
        except Exception as e:
            logger.error(f"Error en test: {str(e)}")
    
    if __name__ == "__main__":
        simple_line_test()

except ImportError as e:
    print(f"Error de importación: {e}")
    print("Algunas dependencias no están disponibles")
except Exception as e:
    print(f"Error general: {e}")