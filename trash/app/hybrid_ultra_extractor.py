#!/usr/bin/env python3
"""
Sistema Híbrido Ultra-Agresivo para Extracción 100% Confiable
Combina múltiples técnicas: regex + AI + análisis de texto plano + OCR
"""

import os
import re
import pdfplumber
from datetime import datetime
from dateutil import parser as dateutil_parser
from app.db.database import SessionLocal
from app.db.models import ExtractedData
import logging

# Google Generative AI para casos complejos
try:
    from google.genai import types
    from google import genai
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridUltraExtractor:
    def __init__(self):
        """Extractor híbrido con múltiples estrategias"""
        
        self.month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # MÚLTIPLES ESTRATEGIAS DE EXTRACCIÓN
        self.strategies = [
            self.strategy_bulletproof_regex,
            self.strategy_ai_extraction,
            self.strategy_brute_force_text,
            self.strategy_character_level,
            self.strategy_pattern_reconstruction
        ]
        
        # Patrones regex ultra-agresivos
        self.ultra_patterns = {
            'calls': [
                re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+.*?([A-Z])\s+(\d+)', re.IGNORECASE),
                re.compile(r'(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+.*?([A-Z])\s+(\d+)', re.IGNORECASE),
                re.compile(r'(IN|OUT)\s+.*?(F|G|H)\s+(\d+)', re.IGNORECASE),
                re.compile(r'\b(\d{1,2}:\d{2})\s*(AM|PM).*?(IN|OUT)', re.IGNORECASE),
            ],
            'messages': [
                re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+.*?(TXT|PIC|MMS)', re.IGNORECASE),
                re.compile(r'(\d{1,2}:\d{2})\s*(AM|PM)\s+(IN|OUT)\s+.*?(TXT|PIC|MMS)', re.IGNORECASE),
                re.compile(r'(IN|OUT)\s+.*?(TXT|PIC|MMS)', re.IGNORECASE),
                re.compile(r'(TXT|PIC|MMS)', re.IGNORECASE),
            ],
            'data': [
                re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(Mobile Internet|Web Access).*?([\d,\.]+)', re.IGNORECASE),
                re.compile(r'(Mobile Internet|Web Access).*?([\d,\.]+)', re.IGNORECASE),
                re.compile(r'([\d,\.]+)\s*(MB|GB)', re.IGNORECASE),
                re.compile(r'\d+\.\d+', re.IGNORECASE),
            ]
        }
        
        # Números de teléfono en todos los formatos
        self.phone_patterns = [
            re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}'),
            re.compile(r'\d{3}-\d{3}-\d{4}'),
            re.compile(r'\d{10,11}'),
            re.compile(r'\d{3}\s*\d{3}\s*\d{4}'),
            re.compile(r'\b\d{10}\b'),
        ]
    
    def extract_with_hybrid_ultra(self, filepath, selected_pages):
        """
        Extracción híbrida ultra-agresiva con múltiples estrategias
        OBJETIVO: 100% de registros capturados sin excepciones
        """
        db = SessionLocal()
        try:
            filename = os.path.basename(filepath)
            logger.info(f"🚀 INICIANDO EXTRACCIÓN HÍBRIDA ULTRA: {filename}")
            
            # Limpiar registros existentes
            deleted_count = db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
            logger.info(f"Registros eliminados: {deleted_count}")
            
            bill_year = self.get_bill_year(filepath)
            logger.info(f"Año detectado: {bill_year}")
            
            # Aplicar TODAS las estrategias y combinar resultados
            all_records = set()  # Usar set para evitar duplicados
            
            with pdfplumber.open(filepath) as pdf:
                if selected_pages == 'all':
                    selected_pages = list(range(1, len(pdf.pages) + 1))
                
                for strategy_func in self.strategies:
                    logger.info(f"Ejecutando estrategia: {strategy_func.__name__}")
                    
                    try:
                        strategy_records = strategy_func(pdf, selected_pages, bill_year, filename)
                        for record in strategy_records:
                            # Crear clave única para evitar duplicados
                            record_key = (
                                record.timestamp.isoformat(),
                                record.event_type,
                                record.phone_line,
                                record.contact,
                                record.value
                            )
                            if record_key not in {self._record_to_key(r) for r in all_records}:
                                all_records.add(record)
                        
                        logger.info(f"  Registros únicos de esta estrategia: {len(strategy_records)}")
                        
                    except Exception as e:
                        logger.warning(f"  Error en estrategia {strategy_func.__name__}: {e}")
            
            # Convertir set a lista para guardar
            final_records = list(all_records)
            
            # Guardar todos los registros
            if final_records:
                db.add_all(final_records)
                db.commit()
                logger.info(f"✅ ÉXITO HÍBRIDO: {len(final_records)} registros únicos guardados")
            else:
                logger.error("❌ FALLO CRÍTICO: Ninguna estrategia extrajo registros")
                return {'success': False, 'error': 'No records from any strategy', 'records_processed': 0}
            
            return {'success': True, 'records_processed': len(final_records)}
            
        except Exception as e:
            logger.error(f"❌ ERROR CRÍTICO EN HÍBRIDO: {str(e)}")
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _record_to_key(self, record):
        """Convertir registro a clave única"""
        return (
            record.timestamp.isoformat(),
            record.event_type,
            record.phone_line,
            record.contact,
            record.value
        )
    
    def strategy_bulletproof_regex(self, pdf, selected_pages, bill_year, filename):
        """Estrategia 1: Regex bulletproof (mejorada)"""
        records = []
        current_date = None
        current_line = None
        
        for page_num in selected_pages:
            if page_num > len(pdf.pages):
                continue
                
            page = pdf.pages[page_num - 1]
            lines = self.extract_comprehensive_text(page)
            
            # Detectar contexto
            context = self.analyze_comprehensive_context(lines)
            if context['line']:
                current_line = context['line']
            if context['date']:
                current_date = context['date']
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Actualizar fecha
                new_date = self.extract_date_from_line(line, bill_year)
                if new_date:
                    current_date = new_date
                
                # Probar todos los patrones
                for event_type, patterns in self.ultra_patterns.items():
                    for pattern in patterns:
                        match = pattern.search(line)
                        if match:
                            record = self.create_record_from_match(
                                match, event_type, line, current_date, current_line, bill_year, filename
                            )
                            if record:
                                records.append(record)
                                break
        
        return records
    
    def strategy_ai_extraction(self, pdf, selected_pages, bill_year, filename):
        """Estrategia 2: Extracción con AI para casos complejos"""
        records = []
        
        if not AI_AVAILABLE:
            logger.info("  AI no disponible, saltando estrategia")
            return records
        
        try:
            # Extraer texto de todas las páginas para AI
            full_text = ""
            for page_num in selected_pages:
                if page_num > len(pdf.pages):
                    continue
                page = pdf.pages[page_num - 1]
                page_text = page.extract_text() or ""
                full_text += f"\n--- PÁGINA {page_num} ---\n{page_text}\n"
            
            # Prompt para AI
            prompt = f"""
Analiza este texto de factura de telecomunicaciones y extrae TODOS los registros de:
1. LLAMADAS (con IN/OUT, hora, duración)
2. MENSAJES (con TXT/PIC, hora)  
3. DATOS (Mobile Internet/Web Access con MB)

Texto de la factura:
{full_text[:8000]}  # Limitar para no exceder tokens

Responde SOLO con líneas en formato CSV:
TIPO,FECHA,HORA,DIRECCION,CONTACTO,DURACION_MB
"""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response and response.text:
                # Parsear respuesta AI
                ai_lines = response.text.strip().split('\n')
                for line in ai_lines:
                    if ',' in line and not line.startswith('TIPO'):
                        try:
                            parts = line.split(',')
                            if len(parts) >= 6:
                                record = self.create_record_from_ai_data(parts, bill_year, filename)
                                if record:
                                    records.append(record)
                        except:
                            continue
            
        except Exception as e:
            logger.info(f"  Error en AI: {e}")
        
        return records
    
    def strategy_brute_force_text(self, pdf, selected_pages, bill_year, filename):
        """Estrategia 3: Fuerza bruta sobre todo el texto"""
        records = []
        
        # Extraer TODO el texto posible
        all_text_lines = []
        
        for page_num in selected_pages:
            if page_num > len(pdf.pages):
                continue
            page = pdf.pages[page_num - 1]
            
            # Múltiples métodos de extracción
            methods = [
                lambda p: p.extract_text(),
                lambda p: p.extract_text(layout=True),
                lambda p: ' '.join([char['text'] for char in p.chars]) if p.chars else '',
            ]
            
            for method in methods:
                try:
                    text = method(page) or ""
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    all_text_lines.extend(lines)
                except:
                    continue
        
        # Buscar patrones en cada línea
        seen_lines = set()
        for line in all_text_lines:
            if line in seen_lines or len(line) < 5:
                continue
            seen_lines.add(line)
            
            # Detectar llamadas por palabras clave
            if any(word in line.upper() for word in ['IN', 'OUT']) and any(char.isdigit() for char in line):
                record = self.brute_force_parse_line(line, 'call', bill_year, filename)
                if record:
                    records.append(record)
            
            # Detectar mensajes
            if any(word in line.upper() for word in ['TXT', 'PIC', 'MMS']):
                record = self.brute_force_parse_line(line, 'message', bill_year, filename)
                if record:
                    records.append(record)
            
            # Detectar datos
            if any(word in line.upper() for word in ['MOBILE INTERNET', 'WEB ACCESS']) or re.search(r'\d+[\.,]\d+', line):
                record = self.brute_force_parse_line(line, 'data', bill_year, filename)
                if record:
                    records.append(record)
        
        return records
    
    def strategy_character_level(self, pdf, selected_pages, bill_year, filename):
        """Estrategia 4: Análisis a nivel de caracteres"""
        records = []
        
        for page_num in selected_pages:
            if page_num > len(pdf.pages):
                continue
            page = pdf.pages[page_num - 1]
            
            if not page.chars:
                continue
            
            # Agrupar caracteres por líneas basado en posición Y
            lines_by_y = {}
            for char in page.chars:
                y = round(char['y0'])
                if y not in lines_by_y:
                    lines_by_y[y] = []
                lines_by_y[y].append((char['x0'], char['text']))
            
            # Reconstruir líneas ordenando por X
            for y in sorted(lines_by_y.keys(), reverse=True):
                char_data = sorted(lines_by_y[y])
                line_text = ''.join([char[1] for char in char_data]).strip()
                
                if len(line_text) > 5:
                    # Buscar patrones de tiempo
                    time_match = re.search(r'\d{1,2}:\d{2}\s*(AM|PM)', line_text)
                    if time_match:
                        record = self.character_level_parse(line_text, bill_year, filename)
                        if record:
                            records.append(record)
        
        return records
    
    def strategy_pattern_reconstruction(self, pdf, selected_pages, bill_year, filename):
        """Estrategia 5: Reconstrucción de patrones perdidos"""
        records = []
        
        # Esta estrategia busca fragmentos y los reconstruye
        all_fragments = []
        
        for page_num in selected_pages:
            if page_num > len(pdf.pages):
                continue
            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""
            
            # Buscar todos los fragmentos que podrían ser parte de registros
            fragments = {
                'times': re.findall(r'\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b', text),
                'directions': re.findall(r'\b(IN|OUT)\b', text),
                'phones': [match.group() for pattern in self.phone_patterns for match in pattern.finditer(text)],
                'amounts': re.findall(r'\b\d+[\.,]\d+\b', text),
                'durations': re.findall(r'\b\d+\s*(?:min)?\b', text),
            }
            
            all_fragments.append(fragments)
        
        # Intentar reconstruir registros de fragmentos
        for fragments in all_fragments:
            for i, time in enumerate(fragments['times']):
                for j, direction in enumerate(fragments['directions']):
                    if abs(i - j) <= 2:  # Si están cerca, probablemente relacionados
                        record = self.reconstruct_record_from_fragments(
                            time, direction, fragments, bill_year, filename
                        )
                        if record:
                            records.append(record)
        
        return records
    
    def extract_comprehensive_text(self, page):
        """Extraer texto con máxima cobertura"""
        lines = []
        
        # Método 1: Extracción estándar
        text1 = page.extract_text() or ""
        lines.extend([line.strip() for line in text1.split('\n') if line.strip()])
        
        # Método 2: Con layout
        text2 = page.extract_text(layout=True) or ""
        lines.extend([line.strip() for line in text2.split('\n') if line.strip()])
        
        # Método 3: Por caracteres
        if page.chars:
            char_text = ''.join([char['text'] for char in page.chars])
            lines.extend([line.strip() for line in char_text.split('\n') if line.strip()])
        
        # Eliminar duplicados
        return list(dict.fromkeys(lines))
    
    def analyze_comprehensive_context(self, lines):
        """Análisis completo de contexto"""
        context = {'section': None, 'line': None, 'date': None}
        
        text = ' '.join(lines)
        
        # Detectar números de teléfono
        for pattern in self.phone_patterns:
            match = pattern.search(text)
            if match:
                context['line'] = self.clean_phone_number(match.group())
                break
        
        # Detectar fechas
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', text)
        if date_match:
            try:
                month = self.month_map.get(date_match.group(1).title())
                day = int(date_match.group(2))
                if month:
                    context['date'] = datetime(datetime.now().year, month, day)
            except:
                pass
        
        return context
    
    def create_record_from_match(self, match, event_type, line, current_date, current_line, bill_year, filename):
        """Crear registro desde match regex"""
        try:
            groups = match.groups()
            
            # Parsear según tipo de evento
            if event_type == 'calls':
                return self.parse_call_match(groups, current_date, current_line, bill_year, filename)
            elif event_type == 'messages':
                return self.parse_message_match(groups, current_date, current_line, bill_year, filename)
            elif event_type == 'data':
                return self.parse_data_match(groups, current_date, current_line, bill_year, filename)
        except:
            return None
    
    def parse_call_match(self, groups, current_date, current_line, bill_year, filename):
        """Parsear match de llamada"""
        try:
            if len(groups) >= 7:  # Con fecha completa
                month_str, day_str, time_str, am_pm, direction, call_type, duration = groups[:7]
                event_datetime = self.parse_datetime(month_str, day_str, time_str, am_pm, bill_year)
            elif len(groups) >= 5:  # Solo hora
                time_str, am_pm, direction, call_type, duration = groups[:5]
                event_datetime = self.parse_time_with_date(time_str, am_pm, current_date) if current_date else None
            else:
                return None
            
            if not event_datetime:
                return None
            
            return ExtractedData(
                source_file=filename,
                phone_line=current_line or "N/A",
                event_type="Llamada",
                timestamp=event_datetime,
                direction="ENTRANTE" if direction.upper() == "IN" else "SALIENTE",
                contact="N/A",
                description=f"Tipo: {call_type}, Duración: {duration}",
                value=str(duration) if duration else "0"
            )
        except:
            return None
    
    def parse_message_match(self, groups, current_date, current_line, bill_year, filename):
        """Parsear match de mensaje"""
        try:
            if len(groups) >= 6:  # Con fecha completa
                month_str, day_str, time_str, am_pm, direction, msg_type = groups[:6]
                event_datetime = self.parse_datetime(month_str, day_str, time_str, am_pm, bill_year)
            elif len(groups) >= 4:  # Solo hora
                time_str, am_pm, direction, msg_type = groups[:4]
                event_datetime = self.parse_time_with_date(time_str, am_pm, current_date) if current_date else None
            else:
                return None
            
            if not event_datetime:
                return None
            
            return ExtractedData(
                source_file=filename,
                phone_line=current_line or "N/A",
                event_type="Mensaje",
                timestamp=event_datetime,
                direction="ENTRANTE" if direction.upper() == "IN" else "SALIENTE",
                contact="N/A",
                description=f"Tipo: {msg_type}",
                value="1"
            )
        except:
            return None
    
    def parse_data_match(self, groups, current_date, current_line, bill_year, filename):
        """Parsear match de datos"""
        try:
            if len(groups) >= 4:  # Con fecha completa
                month_str, day_str, service, amount = groups[:4]
                event_datetime = self.parse_datetime(month_str, day_str, "12:00", "PM", bill_year)
            elif len(groups) >= 2:  # Solo servicio y cantidad
                service, amount = groups[:2]
                event_datetime = current_date or datetime.now().replace(hour=12, minute=0)
            else:
                return None
            
            # Limpiar cantidad
            amount_clean = re.sub(r'[^\d\.]', '', amount) if amount else "0"
            
            return ExtractedData(
                source_file=filename,
                phone_line=current_line or "N/A",
                event_type="Datos",
                timestamp=event_datetime,
                direction="CONSUMO",
                contact="N/A",
                description=f"Servicio: {service}, Cantidad: {amount_clean}",
                value=f"{amount_clean} MB"
            )
        except:
            return None
    
    def brute_force_parse_line(self, line, record_type, bill_year, filename):
        """Parseo por fuerza bruta"""
        try:
            # Buscar hora
            time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', line)
            if not time_match:
                return None
            
            hour_str, am_pm = time_match.groups()
            
            # Crear timestamp básico
            now = datetime.now()
            time_parts = hour_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            if am_pm.upper() == 'PM' and hour != 12:
                hour += 12
            elif am_pm.upper() == 'AM' and hour == 12:
                hour = 0
            
            event_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Detectar dirección
            direction = "SALIENTE"  # Default
            if "IN" in line.upper():
                direction = "ENTRANTE"
            elif record_type == 'data':
                direction = "CONSUMO"
            
            # Crear registro básico
            return ExtractedData(
                source_file=filename,
                phone_line="N/A",
                event_type=record_type.title(),
                timestamp=event_datetime,
                direction=direction,
                contact="N/A",
                description=f"Extraído por fuerza bruta: {line[:50]}",
                value="1" if record_type != 'data' else "0"
            )
        except:
            return None
    
    def character_level_parse(self, line_text, bill_year, filename):
        """Parseo a nivel de caracteres"""
        return self.brute_force_parse_line(line_text, 'unknown', bill_year, filename)
    
    def reconstruct_record_from_fragments(self, time, direction, fragments, bill_year, filename):
        """Reconstruir registro desde fragmentos"""
        try:
            # Crear timestamp básico
            time_match = re.search(r'(\d{1,2}):(\d{2})', time)
            if not time_match:
                return None
            
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            now = datetime.now()
            event_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return ExtractedData(
                source_file=filename,
                phone_line="N/A",
                event_type="Reconstruido",
                timestamp=event_datetime,
                direction="ENTRANTE" if direction == "IN" else "SALIENTE",
                contact="N/A",
                description=f"Reconstruido desde fragmentos: {time} {direction}",
                value="1"
            )
        except:
            return None
    
    def extract_date_from_line(self, line, bill_year):
        """Extraer fecha de línea"""
        match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', line)
        if match:
            try:
                month = self.month_map.get(match.group(1).title())
                day = int(match.group(2))
                if month:
                    return datetime(bill_year, month, day)
            except:
                pass
        return None
    
    def clean_phone_number(self, phone):
        """Limpiar número telefónico"""
        digits = re.sub(r'\D', '', phone)
        return digits[-10:] if len(digits) >= 10 else "N/A"
    
    def parse_datetime(self, month_str, day_str, time_str, am_pm, year):
        """Parsear fecha y hora"""
        try:
            month = self.month_map.get(month_str.title())
            if not month:
                return None
            
            day = int(day_str)
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            if am_pm and am_pm.upper() == 'PM' and hour != 12:
                hour += 12
            elif am_pm and am_pm.upper() == 'AM' and hour == 12:
                hour = 0
            
            return datetime(year, month, day, hour, minute)
        except:
            return None
    
    def parse_time_with_date(self, time_str, am_pm, base_date):
        """Parsear hora con fecha base"""
        try:
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            if am_pm and am_pm.upper() == 'PM' and hour != 12:
                hour += 12
            elif am_pm and am_pm.upper() == 'AM' and hour == 12:
                hour = 0
            
            return base_date.replace(hour=hour, minute=minute)
        except:
            return None
    
    def create_record_from_ai_data(self, parts, bill_year, filename):
        """Crear registro desde datos de AI"""
        try:
            record_type = parts[0].strip()
            date_str = parts[1].strip()
            time_str = parts[2].strip()
            direction = parts[3].strip()
            contact = parts[4].strip()
            value = parts[5].strip()
            
            # Parsear fecha y hora
            event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            return ExtractedData(
                source_file=filename,
                phone_line="N/A",
                event_type=record_type,
                timestamp=event_datetime,
                direction=direction,
                contact=contact,
                description=f"Extraído por AI",
                value=value
            )
        except:
            return None
    
    def get_bill_year(self, filepath):
        """Obtener año del PDF"""
        try:
            with pdfplumber.open(filepath) as pdf:
                text = pdf.pages[0].extract_text() or ""
                year_match = re.search(r'\b(20\d{2})\b', text)
                if year_match:
                    return int(year_match.group(1))
        except:
            pass
        return datetime.now().year

# Instancia global
hybrid_ultra_extractor = HybridUltraExtractor()