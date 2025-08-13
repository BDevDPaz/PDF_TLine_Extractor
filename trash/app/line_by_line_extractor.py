#!/usr/bin/env python3
"""
Extractor Línea por Línea Ultra-Preciso
Basado en la capacidad de selección individual mostrada en la imagen
"""

import os
import re
import pdfplumber
from datetime import datetime
from dateutil import parser as dateutil_parser
from app.db.database import SessionLocal
from app.db.models import ExtractedData
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LineByLineExtractor:
    def __init__(self):
        """Extractor basado en análisis línea por línea preciso"""
        
        self.month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Patrones ultra-específicos basados en el formato observado
        self.line_patterns = {
            # Patrón principal para registros de comunicación
            'main_record': re.compile(
                r'^(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+\((\d{3})\)\s*(\d{3})-(\d{4})\s+(.*?)\s+([FP])\s+(\d+)\s*(.*)$',
                re.IGNORECASE
            ),
            
            # Patrón para llamadas con duración específica
            'call_with_duration': re.compile(
                r'^(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+\((\d{3})\)\s*(\d{3})-(\d{4})\s+(.*?)\s+F\s+(\d+)\s*$',
                re.IGNORECASE
            ),
            
            # Patrón para mensajes (TXT/PIC)
            'message_record': re.compile(
                r'^(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+\((\d{3})\)\s*(\d{3})-(\d{4})\s+(.*?)\s+P\s+(\d+)\s*$',
                re.IGNORECASE
            ),
            
            # Patrón para entrada "Incoming" sin número
            'incoming_record': re.compile(
                r'^(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN)\s+\((\d{3})\)\s*(\d{3})-(\d{4})\s+Incoming\s*-\s*(\d+)\s*$',
                re.IGNORECASE
            ),
            
            # Patrón para fechas de encabezado
            'date_header': re.compile(
                r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$',
                re.IGNORECASE
            ),
            
            # Patrón para datos de internet móvil
            'mobile_data': re.compile(
                r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(Mobile Internet|Web Access)\s*-\s*-\s*([\d,\.]+)\s*$',
                re.IGNORECASE
            )
        }
        
        # Patrones para limpiar números telefónicos
        self.phone_cleanup = re.compile(r'[^\d]')
    
    def extract_with_line_precision(self, filepath, selected_pages):
        """
        Extracción línea por línea con precisión total
        Basado en la estructura exacta mostrada en la imagen
        """
        db = SessionLocal()
        try:
            filename = os.path.basename(filepath)
            logger.info(f"🎯 EXTRACCIÓN LÍNEA POR LÍNEA: {filename}")
            
            # Limpiar registros existentes
            deleted_count = db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
            logger.info(f"Registros anteriores eliminados: {deleted_count}")
            
            bill_year = self.get_bill_year(filepath)
            logger.info(f"Año de facturación: {bill_year}")
            
            all_records = []
            current_date = None
            
            with pdfplumber.open(filepath) as pdf:
                if selected_pages == 'all':
                    selected_pages = list(range(1, len(pdf.pages) + 1))
                
                for page_num in selected_pages:
                    if page_num > len(pdf.pages):
                        continue
                    
                    page = pdf.pages[page_num - 1]
                    logger.info(f"Procesando página {page_num}")
                    
                    # Extraer líneas con máxima precisión
                    lines = self.extract_structured_lines(page)
                    
                    for line_num, line in enumerate(lines, 1):
                        if not line.strip():
                            continue
                        
                        # Detectar fecha de encabezado
                        date_match = self.line_patterns['date_header'].match(line.strip())
                        if date_match:
                            month_str, day_str = date_match.groups()
                            current_date = self.parse_date_header(month_str, day_str, bill_year)
                            if current_date:
                                logger.debug(f"Nueva fecha detectada: {current_date.strftime('%Y-%m-%d')}")
                            continue
                        
                        # Procesar registros de comunicación
                        record = self.process_communication_line(line, current_date, bill_year, filename)
                        if record:
                            all_records.append(record)
                            logger.debug(f"Registro extraído línea {line_num}: {record.event_type}")
                            continue
                        
                        # Procesar datos móviles
                        record = self.process_mobile_data_line(line, bill_year, filename)
                        if record:
                            all_records.append(record)
                            logger.debug(f"Datos móviles línea {line_num}: {record.value}")
                            continue
            
            # Guardar todos los registros
            if all_records:
                db.add_all(all_records)
                db.commit()
                logger.info(f"✅ LÍNEA POR LÍNEA COMPLETADO: {len(all_records)} registros guardados")
            else:
                logger.error("❌ No se extrajeron registros")
                return {'success': False, 'error': 'No records extracted', 'records_processed': 0}
            
            return {'success': True, 'records_processed': len(all_records)}
            
        except Exception as e:
            logger.error(f"❌ ERROR en extracción línea por línea: {str(e)}")
            db.rollback()
            raise e
        finally:
            db.close()
    
    def extract_structured_lines(self, page):
        """Extraer líneas respetando la estructura del PDF"""
        
        lines = []
        
        # Método 1: Extracción por texto con layout preservado
        text_layout = page.extract_text(layout=True)
        if text_layout:
            lines.extend([line.rstrip() for line in text_layout.split('\n')])
        
        # Método 2: Extracción por coordenadas Y para mantener orden
        if page.chars:
            lines_by_y = {}
            for char in page.chars:
                y_pos = round(char['y0'], 1)
                if y_pos not in lines_by_y:
                    lines_by_y[y_pos] = []
                lines_by_y[y_pos].append((char['x0'], char['text']))
            
            # Reconstruir líneas ordenadas por posición Y (de arriba hacia abajo)
            for y_pos in sorted(lines_by_y.keys(), reverse=True):
                char_line = sorted(lines_by_y[y_pos])  # Ordenar por X
                line_text = ''.join([char[1] for char in char_line]).strip()
                if line_text and line_text not in lines:
                    lines.append(line_text)
        
        # Método 3: Extracción estándar como respaldo
        standard_text = page.extract_text()
        if standard_text:
            standard_lines = [line.strip() for line in standard_text.split('\n') if line.strip()]
            for line in standard_lines:
                if line not in lines:
                    lines.append(line)
        
        # Filtrar líneas vacías o muy cortas
        filtered_lines = []
        for line in lines:
            clean_line = line.strip()
            if len(clean_line) > 3 and clean_line not in filtered_lines:
                filtered_lines.append(clean_line)
        
        logger.debug(f"Líneas estructuradas extraídas: {len(filtered_lines)}")
        return filtered_lines
    
    def process_communication_line(self, line, current_date, bill_year, filename):
        """Procesar línea de comunicación específica"""
        
        # Intentar con todos los patrones de registros de comunicación
        for pattern_name, pattern in self.line_patterns.items():
            if pattern_name in ['main_record', 'call_with_duration', 'message_record', 'incoming_record']:
                match = pattern.match(line.strip())
                if match:
                    return self.create_record_from_match(match, pattern_name, current_date, bill_year, filename, line)
        
        return None
    
    def process_mobile_data_line(self, line, bill_year, filename):
        """Procesar línea de datos móviles"""
        
        match = self.line_patterns['mobile_data'].match(line.strip())
        if match:
            month_str, day_str, service_type, data_amount = match.groups()
            
            # Crear fecha
            month = self.month_map.get(month_str.title())
            if not month:
                return None
            
            try:
                day = int(day_str)
                event_datetime = datetime(bill_year, month, day, 12, 0)  # Mediodía por defecto
                
                # Limpiar cantidad de datos
                clean_amount = data_amount.replace(',', '') if data_amount else "0"
                
                return ExtractedData(
                    source_file=filename,
                    phone_line="N/A",
                    event_type="Datos",
                    timestamp=event_datetime,
                    direction="CONSUMO",
                    contact="N/A",
                    description=f"Servicio: {service_type}, Cantidad: {clean_amount} MB",
                    value=f"{clean_amount} MB"
                )
            except ValueError:
                return None
        
        return None
    
    def create_record_from_match(self, match, pattern_name, current_date, bill_year, filename, original_line):
        """Crear registro desde match específico"""
        
        try:
            groups = match.groups()
            
            if pattern_name == 'main_record':
                time_str, am_pm, direction, area_code, exchange, number, description, record_type, duration, extra = groups
                contact_number = f"{area_code}{exchange}{number}"
                
            elif pattern_name == 'call_with_duration':
                time_str, am_pm, direction, area_code, exchange, number, description, duration = groups
                contact_number = f"{area_code}{exchange}{number}"
                record_type = 'F'  # Call
                
            elif pattern_name == 'message_record':
                time_str, am_pm, direction, area_code, exchange, number, description, count = groups
                contact_number = f"{area_code}{exchange}{number}"
                record_type = 'P'  # Picture/Message
                duration = count
                
            elif pattern_name == 'incoming_record':
                time_str, am_pm, direction, area_code, exchange, number, duration = groups
                contact_number = f"{area_code}{exchange}{number}"
                description = "Incoming"
                record_type = '-'
                
            else:
                return None
            
            # Crear timestamp
            if current_date:
                event_datetime = self.parse_time_with_date(time_str, am_pm, current_date)
            else:
                # Usar fecha actual como fallback
                today = datetime.now()
                event_datetime = self.parse_time_with_date(time_str, am_pm, today)
            
            if not event_datetime:
                return None
            
            # Determinar tipo de evento
            if record_type == 'F' or 'call' in description.lower():
                event_type = "Llamada"
            elif record_type == 'P' or 'pic' in description.lower() or 'txt' in description.lower():
                event_type = "Mensaje"
            else:
                event_type = "Comunicación"
            
            # Crear descripción detallada
            desc_parts = []
            if description and description != "-":
                desc_parts.append(f"Descripción: {description}")
            if record_type and record_type != "-":
                desc_parts.append(f"Tipo: {record_type}")
            desc_parts.append(f"Línea original: {original_line[:50]}...")
            
            full_description = " | ".join(desc_parts)
            
            return ExtractedData(
                source_file=filename,
                phone_line=contact_number,
                event_type=event_type,
                timestamp=event_datetime,
                direction="ENTRANTE" if direction.upper() == "IN" else "SALIENTE",
                contact=contact_number,
                description=full_description,
                value=str(duration) if duration else "1"
            )
            
        except Exception as e:
            logger.debug(f"Error creando registro desde match: {e}")
            return None
    
    def parse_date_header(self, month_str, day_str, year):
        """Parsear encabezado de fecha"""
        try:
            month = self.month_map.get(month_str.title())
            if month:
                day = int(day_str)
                return datetime(year, month, day)
        except ValueError:
            pass
        return None
    
    def parse_time_with_date(self, time_str, am_pm, base_date):
        """Parsear hora con fecha base"""
        try:
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # Convertir AM/PM a formato 24h
            if am_pm and am_pm.upper() == 'PM' and hour != 12:
                hour += 12
            elif am_pm and am_pm.upper() == 'AM' and hour == 12:
                hour = 0
            
            return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
        except (ValueError, AttributeError):
            return None
    
    def get_bill_year(self, filepath):
        """Obtener año de la factura"""
        try:
            with pdfplumber.open(filepath) as pdf:
                first_page_text = pdf.pages[0].extract_text() or ""
                year_match = re.search(r'\b(20\d{2})\b', first_page_text)
                if year_match:
                    return int(year_match.group(1))
        except Exception:
            pass
        return datetime.now().year

# Instancia global
line_by_line_extractor = LineByLineExtractor()