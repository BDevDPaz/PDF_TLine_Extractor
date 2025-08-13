"""
Parser optimizado para T-Mobile PDF con formato multi-línea
Basado en análisis real del contenido del PDF
"""

import fitz
import re
import logging
from datetime import datetime
from models import Line, CallEvent, TextEvent, DataEvent

class TMobileParser:
    def __init__(self, session):
        self.session = session
        self.total_extracted = 0
        self.extraction_stats = {'calls': 0, 'texts': 0, 'data': 0}
        
    def parse_pdf(self, pdf_path):
        """Parse PDF T-Mobile con formato multi-línea identificado"""
        try:
            logging.info("🔥 Iniciando parser T-Mobile optimizado para formato multi-línea")
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Seguir especificaciones: omitir 3 primeras y 2 últimas páginas
            start_page = 3  # Página 4 (índice 3)
            end_page = total_pages - 2
            
            if start_page >= end_page:
                logging.warning("⚠️ Muy pocas páginas para procesar")
                return self.extraction_stats
                
            # Extraer año de página 4
            base_year = 2024
            if total_pages > 3:
                page_4_text = doc[3].get_text()
                year_match = re.search(r'\b(20\d{2})\b', page_4_text)
                if year_match:
                    base_year = int(year_match.group(1))
                    logging.info(f"📅 Año base detectado: {base_year}")
            
            # Combinar texto de páginas relevantes
            combined_text = ""
            for page_num in range(start_page, min(start_page + 8, end_page)):
                try:
                    page_text = doc[page_num].get_text()
                    if "USAGE DETAILS" in page_text or any(kw in page_text for kw in ["TALK", "IN (", "OUT ("]):
                        combined_text += page_text + "\n"
                        logging.info(f"📄 Procesando página {page_num + 1}")
                except Exception as e:
                    logging.warning(f"⚠️ Error en página {page_num + 1}: {e}")
            
            if not combined_text:
                logging.warning("⚠️ No se encontró contenido válido")
                return self.extraction_stats
                
            # Detectar líneas telefónicas
            self._detect_phone_lines(combined_text)
            
            # Procesar eventos en formato multi-línea
            self._process_multiline_events(combined_text, base_year)
            
            logging.info(f"✅ EXTRACCIÓN COMPLETADA: {self.total_extracted} eventos")
            logging.info(f"📊 Llamadas: {self.extraction_stats['calls']}, Textos: {self.extraction_stats['texts']}, Datos: {self.extraction_stats['data']}")
            
            return self.extraction_stats
            
        except Exception as e:
            logging.error(f"❌ Error en parser T-Mobile: {e}")
            return self.extraction_stats
    
    def _detect_phone_lines(self, text):
        """Detectar líneas telefónicas en encabezados de sección"""
        lines = text.split('\n')
        detected_lines = {}
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            phone_match = re.match(r'^\((\d{3})\)\s*(\d{3})-(\d{4})(?:\s|$)', line_clean)
            
            if phone_match and i + 1 < len(lines):
                phone_number = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                next_line = lines[i + 1].strip()
                
                # Verificar si es encabezado válido
                if "TALK" in next_line or re.search(r'(Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', next_line):
                    existing_line = self.session.query(Line).filter_by(phone_number=phone_number).first()
                    if not existing_line:
                        new_line = Line(phone_number=phone_number)
                        self.session.add(new_line)
                        self.session.flush()
                        detected_lines[phone_number] = new_line
                    else:
                        detected_lines[phone_number] = existing_line
                    logging.info(f"📱 LÍNEA DETECTADA: {phone_number}")
        
        self.detected_lines = detected_lines
        return detected_lines
    
    def _process_multiline_events(self, text, base_year):
        """Procesar eventos en formato multi-línea basado en análisis real"""
        lines = text.split('\n')
        current_line_obj = None
        current_date = None
        
        # Mapeo de meses
        MONTH_MAP = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Detectar cambio de línea actual
            for phone_number, line_obj in self.detected_lines.items():
                if line_clean.startswith(phone_number):
                    current_line_obj = line_obj
                    logging.info(f"📱 Procesando eventos para: {phone_number}")
                    break
            
            # Detectar nueva fecha
            date_match = re.match(r'(Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun)\s+(\d{1,2})', line_clean)
            if date_match:
                month_str = date_match.group(1)
                day = int(date_match.group(2))
                month = MONTH_MAP.get(month_str, 7)
                current_date = datetime(base_year, month, day)
                logging.info(f"📅 Nueva fecha: {current_date.strftime('%Y-%m-%d')}")
                continue
            
            # Detectar línea telefónica para todos los eventos siguientes
            if not current_line_obj and self.detected_lines:
                # Si no tenemos línea actual, usar la primera disponible
                current_line_obj = list(self.detected_lines.values())[0]
                logging.info(f"📱 Usando línea por defecto: {current_line_obj.phone_number}")
            
            # Detectar eventos por hora (formato multi-línea)
            time_match = re.match(r'^(\d{1,2}:\d{2}\s+[AP]M)$', line_clean)
            if time_match and current_line_obj and current_date and i + 4 < len(lines):
                time_str = time_match.group(1)
                logging.info(f"🕐 HORA DETECTADA: {time_str} (línea {i})")
                
                # Buscar patrón multi-línea en siguientes líneas
                for j in range(1, min(6, len(lines) - i)):
                    next_line = lines[i + j].strip()
                    direction_match = re.match(r'^(IN|OUT)\s+\((\d{3})\)\s*(\d{3}-\d{4})$', next_line)
                    
                    if direction_match:
                        logging.info(f"📞 DIRECCIÓN DETECTADA: {next_line} (línea {i+j})")
                        direction = direction_match.group(1)
                        area_code = direction_match.group(2)
                        phone_number = direction_match.group(3)
                        contact_number = f"({area_code}) {phone_number}"
                        
                        if i + j + 3 < len(lines):
                            description = lines[i + j + 1].strip()
                            event_type = lines[i + j + 2].strip()
                            logging.info(f"📝 DESC/TIPO: '{description}' / '{event_type}'")
                            
                            # Procesar llamada si tiene duración
                            try:
                                duration_line = lines[i + j + 3].strip()
                                if duration_line.isdigit():
                                    duration = int(duration_line)
                                    logging.info(f"⏱️  DURACIÓN: {duration} min")
                                    self._create_call_event(time_str, direction, contact_number, description, duration, current_line_obj, current_date)
                                    break
                            except Exception as e:
                                logging.debug(f"Error en duración: {e}")
                            
                            # Procesar texto si es TXT
                            if 'TXT' in description or event_type == 'TXT':
                                logging.info(f"💬 TEXTO DETECTADO")
                                self._create_text_event(time_str, direction, contact_number, description, current_line_obj, current_date)
                                break
    
    def _create_call_event(self, time_str, direction, contact_number, description, duration, line_obj, date):
        """Crear evento de llamada"""
        try:
            # Crear timestamp
            hour, minute_period = time_str.split(':')
            minute, period = minute_period.split()
            hour = int(hour)
            minute = int(minute)
            if period.upper() == 'PM' and hour != 12:
                hour += 12
            elif period.upper() == 'AM' and hour == 12:
                hour = 0
            
            timestamp = date.replace(hour=hour, minute=minute)
            
            # Crear evento
            call_event = CallEvent(
                line_id=line_obj.id,
                timestamp=timestamp,
                counterpart_number=contact_number,
                description=f"{direction} - {description}",
                call_type=direction,
                duration_minutes=duration
            )
            self.session.add(call_event)
            self.total_extracted += 1
            self.extraction_stats['calls'] += 1
            logging.info(f"📞 LLAMADA: {direction} {contact_number} - {duration}min")
            
        except Exception as e:
            logging.debug(f"⚠️ Error en llamada: {e}")
    
    def _create_text_event(self, time_str, direction, contact_number, description, line_obj, date):
        """Crear evento de texto"""
        try:
            # Crear timestamp
            hour, minute_period = time_str.split(':')
            minute, period = minute_period.split()
            hour = int(hour)
            minute = int(minute)
            if period.upper() == 'PM' and hour != 12:
                hour += 12
            elif period.upper() == 'AM' and hour == 12:
                hour = 0
            
            timestamp = date.replace(hour=hour, minute=minute)
            
            # Crear evento
            text_event = TextEvent(
                line_id=line_obj.id,
                timestamp=timestamp,
                counterpart_number=contact_number,
                destination=description,
                message_type=direction
            )
            self.session.add(text_event)
            self.total_extracted += 1
            self.extraction_stats['texts'] += 1
            logging.info(f"💬 TEXTO: {direction} {contact_number} - {description}")
            
        except Exception as e:
            logging.debug(f"⚠️ Error en texto: {e}")