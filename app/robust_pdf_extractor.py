import re
import pdfplumber
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser
from app.db.database import SessionLocal
from app.db.models import ExtractedData
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
        
        # Patrones para llamadas - formato exacto del PDF detectado
        self.call_pattern = re.compile(
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+'  # Fecha completa
            r'(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                        # Hora
            r'(IN|OUT)\s+'                                                         # Dirección
            r'(.*?)\s+'                                                            # Contacto/descripción
            r'([A-Z])\s+'                                                          # Tipo (F, etc.)
            r'(\d+)\s*'                                                            # Duración
            r'(-|\$[\d\.]+)?\s*.*?$',                                             # Costo + contenido adicional
            re.IGNORECASE
        )
        
        # Patrón para llamadas solo con hora (sin fecha - muy común en el PDF)
        self.call_no_date_pattern = re.compile(
            r'^\s*(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                   # Solo hora
            r'(IN|OUT)\s+'                                                         # Dirección  
            r'(.*?)\s+'                                                            # Contacto/descripción
            r'([A-Z])\s+'                                                          # Tipo
            r'(\d+)\s*'                                                            # Duración
            r'(-|\$[\d\.]+)?\s*.*?$',                                             # Costo + contenido adicional
            re.IGNORECASE
        )
        
        # Patrón alternativo para detectar hora en formato 24h
        self.time_24h_pattern = re.compile(r'(\d{1,2}):(\d{2})(?:\s*(AM|PM))?')
        
        # Patrón para detectar ubicaciones/ciudades
        self.location_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[,/]\s*([A-Z]{2})')  # Ciudad, Estado
        
        # Patrones para mensajes - formato exacto del PDF detectado
        self.message_pattern = re.compile(
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+'  # Fecha completa
            r'(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                        # Hora
            r'(IN|OUT)\s+'                                                         # Dirección
            r'(.+?)\s+'                                                            # Contacto/descripción
            r'(TXT|PIC|MMS)\s*'                                                    # Tipo
            r'(-|\$[\d\.]+)?\s*.*?$',                                             # Costo + contenido adicional
            re.IGNORECASE
        )
        
        # Patrón para mensajes solo con hora (muy común en el PDF)
        self.message_no_date_pattern = re.compile(
            r'^\s*(\d{1,2}:\d{2})\s*(AM|PM)\s+'                                   # Solo hora
            r'(IN|OUT)\s+'                                                         # Dirección
            r'(.+?)\s+'                                                            # Contacto/descripción  
            r'(TXT|PIC|MMS)\s*'                                                    # Tipo
            r'(-|\$[\d\.]+)?\s*.*?$',                                             # Costo + contenido adicional
            re.IGNORECASE
        )
        
        # Patrón para uso de datos - formato exacto del PDF detectado
        self.data_pattern = re.compile(
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+'  # Fecha
            r'(Mobile Internet|Web Access)\s+'                                    # Tipo de servicio
            r'(-)\s+'                                                              # Origen (siempre -)
            r'(-)\s+'                                                              # Tipo (siempre -)  
            r'([\d,\.]+)\s*'                                                       # MB (con comas)
            r'(-|\$[\d\.]+)?\s*.*?$',                                             # Costo + contenido adicional
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
        Maneja múltiples formatos: 'Mar 15 3:45 PM', '15:45', '3:45 AM'
        """
        try:
            month_num = self.month_map.get(month_str[:3].title())
            if not month_num:
                return None
            
            day = int(day_str)
            
            # Parsear hora con flexibilidad para 12h y 24h
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # Manejar formato 12 horas con AM/PM
            if am_pm:
                if am_pm.upper() == 'PM' and hour != 12:
                    hour += 12
                elif am_pm.upper() == 'AM' and hour == 12:
                    hour = 0
            # Si no hay AM/PM, asumir formato 24h (verificar rango válido)
            elif hour > 12:
                pass  # Ya está en formato 24h
            
            # Validar rango de hora
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                return None
                
            return datetime(year, month_num, day, hour, minute)
        
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing date/time: {month_str} {day_str} {time_str} {am_pm} - {e}")
            return None
    
    def extract_location(self, description_text):
        """Extrae ubicación/ciudad de la descripción si está presente"""
        if not description_text:
            return None
        
        location_match = self.location_pattern.search(description_text)
        if location_match:
            city = location_match.group(1)
            state = location_match.group(2)
            return f"{city}, {state}"
        
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
        """Procesa línea de llamada capturando todos los campos clave"""
        match = self.call_pattern.match(line.strip())
        if not match:
            return None
        
        month_str, day_str, time_str, am_pm, direction, contact_desc, call_type, duration, cost = match.groups()
        
        # 1. FECHA Y HORA - Parseo preciso con múltiples formatos
        event_datetime = self.parse_date_time(month_str, day_str, time_str, am_pm, bill_year)
        if not event_datetime:
            return None
        
        # 2. LÍNEA TELEFÓNICA - Ya viene del contexto
        phone_line = current_line if current_line != "Desconocida" else "N/A"
        
        # 3. EVENTO - Tipo fijo: Llamada
        event_type = "Llamada"
        
        # 4. TIPO - Entrante o Saliente
        event_direction = "ENTRANTE" if direction.upper() == "IN" else "SALIENTE"
        
        # 5. CONTACTO - Extraer número de teléfono limpio  
        contact_number = "N/A"
        if contact_desc:
            phone_match = self.phone_pattern.search(contact_desc)
            if phone_match:
                contact_number = self.clean_phone_number(phone_match.group(0))
            # También buscar números sin paréntesis
            elif re.search(r'\d{10,}', contact_desc):
                numbers = re.findall(r'\d{10,}', contact_desc)
                if numbers:
                    contact_number = self.clean_phone_number(numbers[0])
        
        # 6. LUGAR - Extraer ubicación de la descripción
        location = self.extract_location(contact_desc) if contact_desc else None
        
        # 7. DURACIÓN - En minutos
        call_duration = duration if duration and duration != "-" else "0"
        
        # Crear descripción estructurada con todos los campos
        description_parts = []
        if contact_desc and contact_desc.strip():
            description_parts.append(f"Descripción: {contact_desc.strip()}")
        if location:
            description_parts.append(f"Ubicación: {location}")
        if call_type and call_type != "-":
            description_parts.append(f"Tipo llamada: {call_type}")
        if cost and cost != "-":
            description_parts.append(f"Costo: {cost}")
        
        full_description = " | ".join(description_parts) if description_parts else "Llamada"
        
        return ExtractedData(
            source_file=filename,
            phone_line=phone_line,
            event_type=event_type,
            timestamp=event_datetime,
            direction=event_direction,
            contact=contact_number,
            description=full_description,
            value=call_duration
        )
    
    def process_message_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de mensaje capturando todos los campos clave"""
        match = self.message_pattern.match(line.strip())
        if not match:
            return None
        
        month_str, day_str, time_str, am_pm, direction, contact_desc, msg_type, cost = match.groups()
        
        # 1. FECHA Y HORA - Parseo preciso
        event_datetime = self.parse_date_time(month_str, day_str, time_str, am_pm, bill_year)
        if not event_datetime:
            return None
        
        # 2. LÍNEA TELEFÓNICA
        phone_line = current_line if current_line != "Desconocida" else "N/A"
        
        # 3. EVENTO - Tipo fijo: Mensaje
        event_type = "Mensaje"
        
        # 4. TIPO - Entrante o Saliente
        event_direction = "ENTRANTE" if direction.upper() == "IN" else "SALIENTE"
        
        # 5. CONTACTO - Extraer número telefónico
        contact_number = "N/A"
        description_clean = contact_desc
        
        # Buscar número telefónico en la descripción
        phone_in_desc = self.phone_pattern.search(contact_desc)
        if phone_in_desc:
            contact_number = self.clean_phone_number(phone_in_desc.group(0))
            # Limpiar descripción removiendo el número
            description_clean = contact_desc.replace(phone_in_desc.group(0), "").strip()
        
        # 6. LUGAR - Extraer ubicación si está presente
        location = self.extract_location(description_clean)
        
        # 7. CANTIDAD - Siempre 1 para mensajes
        message_count = "1"
        
        # Crear descripción estructurada
        description_parts = []
        if description_clean:
            description_parts.append(f"Descripción: {description_clean}")
        if location:
            description_parts.append(f"Ubicación: {location}")
        if msg_type:
            description_parts.append(f"Tipo: {msg_type}")
        if cost and cost != "-":
            description_parts.append(f"Costo: {cost}")
        
        full_description = " | ".join(description_parts) if description_parts else f"Mensaje {msg_type}"
        
        return ExtractedData(
            source_file=filename,
            phone_line=phone_line,
            event_type=event_type,
            timestamp=event_datetime,
            direction=event_direction,
            contact=contact_number,
            description=full_description,
            value=message_count
        )
    
    def process_data_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de uso de datos capturando todos los campos clave"""
        match = self.data_pattern.match(line.strip())
        if not match:
            return None
        
        month_str, day_str, time_str, am_pm, description, data_amount, cost = match.groups()
        
        # 1. FECHA Y HORA - Parseo preciso
        event_datetime = self.parse_date_time(month_str, day_str, time_str, am_pm, bill_year)
        if not event_datetime:
            return None
        
        # 2. LÍNEA TELEFÓNICA
        phone_line = current_line if current_line != "Desconocida" else "N/A"
        
        # 3. EVENTO - Tipo fijo: Datos
        event_type = "Datos"
        
        # 4. TIPO - Siempre consumo (saliente)
        event_direction = "CONSUMO"
        
        # 5. CONTACTO - No aplica para uso de datos
        contact_number = "N/A"
        
        # 6. LUGAR - Extraer ubicación si está presente
        location = self.extract_location(description)
        
        # 7. CANTIDAD - Cantidad de datos usados (MB, GB, KB)
        data_quantity = data_amount if data_amount else "0 MB"
        
        # Crear descripción estructurada
        description_parts = []
        if description and description.strip():
            description_parts.append(f"Actividad: {description.strip()}")
        if location:
            description_parts.append(f"Ubicación: {location}")
        description_parts.append(f"Cantidad: {data_quantity}")
        if cost and cost != "-":
            description_parts.append(f"Costo: {cost}")
        
        full_description = " | ".join(description_parts)
        
        return ExtractedData(
            source_file=filename,
            phone_line=phone_line,
            event_type=event_type,
            timestamp=event_datetime,
            direction=event_direction,
            contact=contact_number,
            description=full_description,
            value=data_quantity
        )
        
    def process_call_no_date_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de llamada sin fecha explícita usando fecha persistente"""
        match = self.call_no_date_pattern.match(line.strip())
        if not match or not current_date:
            return None
        
        time_str, am_pm, direction, contact_desc, call_type, duration, cost = match.groups()
        
        # Usar fecha persistente con hora específica
        time_parts = time_str.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if am_pm and am_pm.upper() == 'PM' and hour != 12:
            hour += 12
        elif am_pm and am_pm.upper() == 'AM' and hour == 12:
            hour = 0
            
        event_datetime = current_date.replace(hour=hour, minute=minute)
        
        # Procesar igual que llamada normal
        phone_line = current_line if current_line != "Desconocida" else "N/A"
        event_type = "Llamada"
        event_direction = "ENTRANTE" if direction.upper() == "IN" else "SALIENTE"
        
        # Extraer contacto
        contact_number = "N/A"
        if contact_desc:
            phone_match = self.phone_pattern.search(contact_desc)
            if phone_match:
                contact_number = self.clean_phone_number(phone_match.group(0))
        
        location = self.extract_location(contact_desc) if contact_desc else None
        call_duration = duration if duration != "-" else "0"
        
        # Descripción estructurada
        description_parts = []
        if contact_desc and contact_desc.strip():
            description_parts.append(f"Descripción: {contact_desc.strip()}")
        if location:
            description_parts.append(f"Ubicación: {location}")
        if call_type and call_type != "-":
            description_parts.append(f"Tipo llamada: {call_type}")
        if cost and cost != "-":
            description_parts.append(f"Costo: {cost}")
        
        full_description = " | ".join(description_parts) if description_parts else "Llamada"
        
        return ExtractedData(
            source_file=filename,
            phone_line=phone_line,
            event_type=event_type,
            timestamp=event_datetime,
            direction=event_direction,
            contact=contact_number,
            description=full_description,
            value=call_duration
        )
        
    def process_message_no_date_line(self, line, current_date, current_line, bill_year, filename):
        """Procesa línea de mensaje sin fecha explícita usando fecha persistente"""
        match = self.message_no_date_pattern.match(line.strip())
        if not match or not current_date:
            return None
        
        time_str, am_pm, direction, contact_desc, msg_type, cost = match.groups()
        
        # Usar fecha persistente con hora específica
        time_parts = time_str.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if am_pm and am_pm.upper() == 'PM' and hour != 12:
            hour += 12
        elif am_pm and am_pm.upper() == 'AM' and hour == 12:
            hour = 0
            
        event_datetime = current_date.replace(hour=hour, minute=minute)
        
        # Procesar igual que mensaje normal
        phone_line = current_line if current_line != "Desconocida" else "N/A"
        event_type = "Mensaje"
        event_direction = "ENTRANTE" if direction.upper() == "IN" else "SALIENTE"
        
        # Extraer contacto
        contact_number = "N/A"
        description_clean = contact_desc
        
        if contact_desc:
            phone_match = self.phone_pattern.search(contact_desc)
            if phone_match:
                contact_number = self.clean_phone_number(phone_match.group(0))
                description_clean = contact_desc.replace(phone_match.group(0), "").strip()
        
        location = self.extract_location(description_clean)
        
        # Descripción estructurada
        description_parts = []
        if description_clean:
            description_parts.append(f"Descripción: {description_clean}")
        if location:
            description_parts.append(f"Ubicación: {location}")
        if msg_type:
            description_parts.append(f"Tipo: {msg_type}")
        if cost and cost != "-":
            description_parts.append(f"Costo: {cost}")
        
        full_description = " | ".join(description_parts) if description_parts else f"Mensaje {msg_type}"
        
        return ExtractedData(
            source_file=filename,
            phone_line=phone_line,
            event_type=event_type,
            timestamp=event_datetime,
            direction=event_direction,
            contact=contact_number,
            description=full_description,
            value="1"
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
                            # Intentar patrón con fecha explícita
                            record = self.process_call_line(line, last_known_date, current_line, bill_year, filename)
                            
                            # Si falla, intentar patrón sin fecha explícita
                            if not record and last_known_date:
                                record = self.process_call_no_date_line(line, last_known_date, current_line, bill_year, filename)
                                
                        elif current_section == "Mensaje":
                            # Intentar patrón con fecha explícita
                            record = self.process_message_line(line, last_known_date, current_line, bill_year, filename)
                            
                            # Si falla, intentar patrón sin fecha explícita  
                            if not record and last_known_date:
                                record = self.process_message_no_date_line(line, last_known_date, current_line, bill_year, filename)
                                
                        elif current_section == "Datos":
                            record = self.process_data_line(line, last_known_date, current_line, bill_year, filename)
                        
                        # Si se extrajo un registro, agregarlo
                        if record:
                            extracted_records.append(record)
                            logger.debug(f"Registro extraído: {record.event_type} - {record.timestamp}")
            
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