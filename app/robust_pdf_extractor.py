import re
import pdfplumber
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser
from app.database import SessionLocal, ExtractedData
import logging

# Configurar logging para debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustPDFExtractor:
    """
    Extractor extremadamente robusto para facturas de telecomunicaciones
    Diseñado para manejar formato de dos columnas con información secuencial
    """
    
    def __init__(self):
        # Mapeo de meses en inglés a número
        self.month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Patrones regex optimizados para formato específico
        self.phone_pattern = re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}')
        self.date_pattern = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?!\d)', re.IGNORECASE)
        
        # Patrones para llamadas con máxima precisión
        self.call_pattern = re.compile(
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+'  # Fecha
            r'(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                        # Hora
            r'(IN|OUT)\s+'                                                         # Dirección
            r'((?:\(\d{3}\)\s*\d{3}-\d{4})|(?:\d{10,15})|(?:[\w\s\./\(\)\-\:]+?))\s+'  # Contacto
            r'(.*?)\s+'                                                            # Descripción
            r'([A-ZCHFWG]|-)\s+'                                                   # Tipo
            r'(\d+|-)\s*'                                                          # Duración/cantidad
            r'(-|\$[\d\.]+)?\s*$',                                                # Costo
            re.IGNORECASE
        )
        
        # Patrones para mensajes con máxima precisión
        self.message_pattern = re.compile(
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+'  # Fecha
            r'(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                        # Hora
            r'(IN|OUT)\s+'                                                         # Dirección
            r'(.+?)\s+'                                                            # Contacto/descripción
            r'(TXT|PIC|MMS)\s*'                                                    # Tipo
            r'(-|\$[\d\.]+)?\s*$',                                                # Costo
            re.IGNORECASE
        )
        
        # Patrones para uso de datos
        self.data_pattern = re.compile(
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+'  # Fecha
            r'(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                        # Hora
            r'(.+?)\s+'                                                            # Descripción
            r'([\d\.]+\s*(?:KB|MB|GB))\s*'                                         # Cantidad
            r'(-|\$[\d\.]+)?\s*$',                                                # Costo
            re.IGNORECASE
        )
    
    def clean_phone_number(self, phone_str):
        """Limpia y normaliza números telefónicos"""
        if not phone_str:
            return None
        # Mantener solo dígitos
        cleaned = re.sub(r'\D', '', phone_str)
        return cleaned if len(cleaned) >= 7 else None
    
    def parse_date_time(self, month_str, day_str, time_str, am_pm, year):
        """
        Convierte fecha en formato específico a datetime
        Maneja formato: 'Mar 15 3:45 PM' con año de facturación
        """
        try:
            month_num = self.month_map.get(month_str[:3].title())
            if not month_num:
                return None
            
            day = int(day_str)
            
            # Parsear hora
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Convertir a formato 24 horas
            if am_pm.upper() == 'PM' and hour != 12:
                hour += 12
            elif am_pm.upper() == 'AM' and hour == 12:
                hour = 0
            
            return datetime(year, month_num, day, hour, minute)
        
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing date/time: {month_str} {day_str} {time_str} {am_pm} - {e}")
            return None
    
    def extract_two_column_text(self, page):
        """
        Extrae texto respetando el formato de dos columnas
        Lee secuencialmente: columna izquierda, luego columna derecha
        """
        try:
            # Obtener dimensiones de la página
            page_width = page.width
            page_height = page.height
            
            # Definir áreas de columnas (ajustar según necesidad)
            left_column = page.crop((0, 0, page_width/2, page_height))
            right_column = page.crop((page_width/2, 0, page_width, page_height))
            
            # Extraer texto de cada columna
            left_text = left_column.extract_text(x_tolerance=2, layout=True) or ""
            right_text = right_column.extract_text(x_tolerance=2, layout=True) or ""
            
            # Combinar texto respetando orden de lectura
            combined_lines = []
            left_lines = [line.strip() for line in left_text.split('\n') if line.strip()]
            right_lines = [line.strip() for line in right_text.split('\n') if line.strip()]
            
            # Agregar líneas de columna izquierda
            combined_lines.extend(left_lines)
            # Agregar líneas de columna derecha
            combined_lines.extend(right_lines)
            
            return combined_lines
            
        except Exception as e:
            logger.error(f"Error extracting two-column text: {e}")
            # Fallback a extracción normal
            text = page.extract_text(x_tolerance=2, layout=True) or ""
            return [line.strip() for line in text.split('\n') if line.strip()]
    
    def detect_section_and_line(self, lines):
        """
        Detecta sección actual y línea telefónica del contenido
        """
        current_section = "Desconocida"
        current_line = "Desconocida"
        
        # Buscar en todas las líneas
        text_combined = ' '.join(lines)
        
        # Detectar sección
        if "TALK" in text_combined:
            current_section = "Llamada"
        elif "TEXT" in text_combined:
            current_section = "Mensaje"
        elif "DATA" in text_combined:
            current_section = "Datos"
        
        # Detectar línea telefónica
        phone_match = self.phone_pattern.search(text_combined)
        if phone_match:
            current_line = self.clean_phone_number(phone_match.group(0))
        
        return current_section, current_line
    
    def process_call_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de llamada con máxima precisión"""
        match = self.call_pattern.match(line.strip())
        if not match:
            return None
        
        month_str, day_str, time_str, am_pm, direction, contact_raw, description, call_type, duration, cost = match.groups()
        
        # Parsear fecha y hora
        event_datetime = self.parse_date_time(month_str, day_str, time_str, am_pm, bill_year)
        if not event_datetime:
            return None
        
        # Limpiar contacto
        contact = self.clean_phone_number(contact_raw) if contact_raw else "N/A"
        
        # Crear descripción completa
        full_description = f"{description.strip()} - Tipo: {call_type} - Duración: {duration} min"
        if cost and cost != "-":
            full_description += f" - Costo: {cost}"
        
        return ExtractedData(
            source_file=filename,
            phone_line=current_line,
            event_type="Llamada",
            timestamp=event_datetime,
            direction=direction.upper(),
            contact=contact,
            description=full_description.strip(),
            value=duration if duration != "-" else "0"
        )
    
    def process_message_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de mensaje con máxima precisión"""
        match = self.message_pattern.match(line.strip())
        if not match:
            return None
        
        month_str, day_str, time_str, am_pm, direction, contact_desc, msg_type, cost = match.groups()
        
        # Parsear fecha y hora
        event_datetime = self.parse_date_time(month_str, day_str, time_str, am_pm, bill_year)
        if not event_datetime:
            return None
        
        # Extraer contacto de la descripción
        contact = "N/A"
        description = contact_desc
        
        # Buscar número telefónico en la descripción
        phone_in_desc = self.phone_pattern.search(contact_desc)
        if phone_in_desc:
            contact = self.clean_phone_number(phone_in_desc.group(0))
        
        # Crear descripción completa
        full_description = f"{description.strip()} - Tipo: {msg_type}"
        if cost and cost != "-":
            full_description += f" - Costo: {cost}"
        
        return ExtractedData(
            source_file=filename,
            phone_line=current_line,
            event_type="Mensaje",
            timestamp=event_datetime,
            direction=direction.upper(),
            contact=contact,
            description=full_description.strip(),
            value="1"
        )
    
    def process_data_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de uso de datos con máxima precisión"""
        match = self.data_pattern.match(line.strip())
        if not match:
            return None
        
        month_str, day_str, time_str, am_pm, description, data_amount, cost = match.groups()
        
        # Parsear fecha y hora
        event_datetime = self.parse_date_time(month_str, day_str, time_str, am_pm, bill_year)
        if not event_datetime:
            return None
        
        # Crear descripción completa
        full_description = f"{description.strip()} - Cantidad: {data_amount}"
        if cost and cost != "-":
            full_description += f" - Costo: {cost}"
        
        return ExtractedData(
            source_file=filename,
            phone_line=current_line,
            event_type="Datos",
            timestamp=event_datetime,
            direction="OUT",  # Asumimos que el uso de datos es saliente
            contact="N/A",
            description=full_description.strip(),
            value=data_amount
        )
    
    def extract_bill_year(self, first_page_text):
        """Extrae el año de facturación del PDF"""
        # Buscar patrones de fecha en la primera página
        year_patterns = [
            r'Bill issue date.*?(\b20\d{2}\b)',
            r'Statement date.*?(\b20\d{2}\b)',
            r'Date.*?(\b20\d{2}\b)',
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, first_page_text, re.DOTALL | re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Fallback al año actual
        return datetime.now().year
    
    def extract_data_robust(self, filepath, selected_pages):
        """
        Método principal de extracción extremadamente robusto
        """
        db = SessionLocal()
        try:
            filename = filepath.split('/')[-1]
            logger.info(f"Procesando archivo: {filename}")
            
            # Limpiar datos existentes
            deleted_count = db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
            logger.info(f"Eliminados {deleted_count} registros existentes")
            
            extracted_records = []
            
            with pdfplumber.open(filepath) as pdf:
                # Extraer año de facturación
                first_page_text = pdf.pages[0].extract_text() or ""
                bill_year = self.extract_bill_year(first_page_text)
                logger.info(f"Año de facturación detectado: {bill_year}")
                
                # Estado persistente para fechas sin fecha explícita
                last_known_date = None
                
                # Procesar páginas seleccionadas
                if selected_pages == 'all':
                    selected_pages = list(range(1, len(pdf.pages) + 1))
                
                for page_num in selected_pages:
                    if page_num > len(pdf.pages):
                        continue
                    
                    page = pdf.pages[page_num - 1]
                    logger.info(f"Procesando página {page_num}")
                    
                    # Extraer texto respetando formato de dos columnas
                    lines = self.extract_two_column_text(page)
                    
                    # Detectar sección y línea actual
                    current_section, current_line = self.detect_section_and_line(lines)
                    logger.info(f"Página {page_num}: Sección={current_section}, Línea={current_line}")
                    
                    # Procesar cada línea
                    for line in lines:
                        if not line or len(line.strip()) < 5:
                            continue
                        
                        # Detectar si la línea tiene fecha explícita
                        date_match = self.date_pattern.match(line.strip())
                        if date_match:
                            # Actualizar fecha conocida
                            try:
                                month_num = self.month_map.get(date_match.group(1)[:3].title())
                                if month_num:  # Verificar que month_num no sea None
                                    day = int(date_match.group(2))
                                    last_known_date = datetime(bill_year, month_num, day)
                                    logger.debug(f"Fecha actualizada: {last_known_date.strftime('%Y-%m-%d')}")
                            except (ValueError, TypeError):
                                pass
                        
                        # Procesar línea según tipo de sección
                        record = None
                        
                        if current_section == "Llamada":
                            record = self.process_call_line(line, last_known_date, current_line, bill_year, filename)
                        elif current_section == "Mensaje":
                            record = self.process_message_line(line, last_known_date, current_line, bill_year, filename)
                        elif current_section == "Datos":
                            record = self.process_data_line(line, last_known_date, current_line, bill_year, filename)
                        
                        # Si se extrajo un registro, agregarlo
                        if record:
                            extracted_records.append(record)
                            logger.debug(f"Registro extraído: {record.event_type} - {record.timestamp}")
                        
                        # Para eventos sin fecha explícita, usar última fecha conocida
                        elif last_known_date and (":" in line and ("AM" in line or "PM" in line)):
                            # Intentar procesar como evento sin fecha explícita
                            # (Implementar lógica adicional si es necesario)
                            pass
            
            # Ordenar registros cronológicamente
            extracted_records.sort(key=lambda x: x.timestamp if x.timestamp else datetime.min)
            
            # Guardar en base de datos
            for record in extracted_records:
                db.add(record)
            
            db.commit()
            
            logger.info(f"Extracción completada: {len(extracted_records)} registros procesados")
            return {"success": True, "records_processed": len(extracted_records)}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error durante extracción: {str(e)}")
            raise e
        finally:
            db.close()

# Instancia global del extractor
robust_extractor = RobustPDFExtractor()