import os
import pdfplumber
import json
import re
from datetime import datetime
from dateutil.parser import parse
import google.generativeai as genai
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def extract_data_with_optimized_processing(filepath: str, pages_to_process: list[int]):
    """
    Procesador optimizado que maneja TODAS las páginas seleccionadas en una operación:
    1. Extrae texto completo de todas las páginas
    2. Optimiza el contenido manteniendo información clave
    3. Usa AI con configuración optimizada para PDFs grandes
    4. Fallback robusto a regex si AI falla
    """
    filename = os.path.basename(filepath)
    
    # Extraer texto de TODAS las páginas seleccionadas
    full_text = ""
    page_summaries = []
    
    with pdfplumber.open(filepath) as pdf:
        for page_num in pages_to_process:
            if page_num > len(pdf.pages): 
                continue
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            if text:
                # Para AI: resumir cada página manteniendo datos estructurados
                page_summary = extract_key_data_from_page(text, page_num)
                page_summaries.append(page_summary)
                # Para regex fallback: texto completo
                full_text += f"\n--- Página {page_num} ---\n{text}"
    
    if not page_summaries and not full_text:
        return 0
    
    # Intentar con AI primero (usando páginas resumidas pero completas)
    ai_records = process_with_optimized_ai(page_summaries, filename)
    
    if len(ai_records) >= 3:  # Si AI encuentra registros suficientes
        return save_records_to_db(ai_records, filename)
    else:
        # Fallback a regex con texto completo
        print("AI no encontró suficientes registros, usando regex con texto completo...")
        regex_records = process_with_comprehensive_regex(full_text, filename)
        return save_records_to_db(regex_records, filename)

def extract_key_data_from_page(page_text: str, page_num: int) -> dict:
    """
    Extrae y resume la información clave de cada página manteniendo datos estructurados
    """
    # Buscar líneas que contengan fechas, horas, direcciones, números
    key_lines = []
    lines = page_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Líneas que contienen patrones de datos relevantes
        if (re.search(r'\b\w{3}\s+\d{1,2}\b', line) or  # fechas como "Jun 16"
            re.search(r'\d{1,2}:\d{2}\s*[AP]M', line) or  # horas como "6:16 PM"
            re.search(r'\b(IN|OUT)\b', line) or  # direcciones
            re.search(r'\(\d{3}\)\s*\d{3}-\d{4}', line) or  # teléfonos
            re.search(r'\d+\s*(?:MB|GB|min)', line) or  # datos/minutos
            'TEXT' in line.upper() or 'CALL' in line.upper() or 'DATA' in line.upper()):
            key_lines.append(line)
    
    return {
        'page_num': page_num,
        'key_content': '\n'.join(key_lines[:50]),  # Máximo 50 líneas relevantes por página
        'total_lines': len(lines),
        'relevant_lines': len(key_lines)
    }

def process_with_optimized_ai(page_summaries: list, filename: str) -> list:
    """
    Procesa con AI usando contenido optimizado de todas las páginas
    """
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configurando Google AI: {e}")
        return []
    
    # Combinar contenido clave de todas las páginas
    combined_content = ""
    for page_data in page_summaries:
        if page_data['relevant_lines'] > 0:
            combined_content += f"\n=== PÁGINA {page_data['page_num']} ===\n{page_data['key_content']}\n"
    
    if not combined_content:
        return []
    
    # Limitar contenido total pero mantener representatividad
    if len(combined_content) > 15000:
        combined_content = combined_content[:15000] + "\n[... contenido truncado para optimización ...]"
    
    prompt = f"""
Analiza este contenido de factura de telecomunicaciones de TODAS las páginas y extrae todos los registros de llamadas, mensajes y datos.

IMPORTANTE: Este es el contenido completo del documento, no solo una muestra.

Formato de respuesta JSON exacto:
{{
  "calls": [
    {{"date": "Jun 16", "time": "6:16 PM", "direction": "OUT", "contact": "(818)466-3558", "minutes": 15}}
  ],
  "messages": [
    {{"date": "Jun 16", "time": "4:27 PM", "direction": "OUT", "contact": "96831", "format": "TXT"}}
  ],
  "data_usage": [
    {{"date": "Jun 16", "megabytes": 2517.55}}
  ]
}}

Contenido completo de la factura:
{combined_content}
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Limpiar respuesta de forma más robusta
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].strip()
        
        # Limpiar caracteres no JSON
        response_text = response_text.strip()
        if not response_text.startswith('{'):
            # Buscar el primer { que marque el inicio del JSON
            start = response_text.find('{')
            if start != -1:
                response_text = response_text[start:]
        
        if not response_text.endswith('}'):
            # Buscar el último } que marque el final del JSON
            end = response_text.rfind('}')
            if end != -1:
                response_text = response_text[:end+1]
        
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error de JSON: {e}")
            print(f"Texto recibido: {response_text[:200]}...")
            # Si no es JSON válido, devolver estructura vacía para que use fallback
            extracted_data = {"calls": [], "messages": [], "data_usage": []}
        
        # Convertir a objetos de base de datos
        records = []
        current_year = "2024"
        
        # Procesar llamadas
        for call in extracted_data.get('calls', []):
            try:
                date_str = f"{call['date']} {call['time']}, {current_year}"
                timestamp = parse(date_str)
                records.append(ExtractedData(
                    source_file=filename,
                    phone_line="N/A",
                    event_type='Llamada',
                    timestamp=timestamp,
                    direction=call.get('direction'),
                    contact=call.get('contact'),
                    description=f"Llamada {call.get('direction', '').lower()}",
                    value=f"{call.get('minutes', 0)} min"
                ))
            except Exception:
                continue
        
        # Procesar mensajes
        for msg in extracted_data.get('messages', []):
            try:
                date_str = f"{msg['date']} {msg['time']}, {current_year}"
                timestamp = parse(date_str)
                records.append(ExtractedData(
                    source_file=filename,
                    phone_line="N/A",
                    event_type='Mensaje',
                    timestamp=timestamp,
                    direction=msg.get('direction'),
                    contact=msg.get('contact'),
                    description=f"Mensaje {msg.get('direction', '').lower()}",
                    value=msg.get('format', 'TXT')
                ))
            except Exception:
                continue
        
        # Procesar datos
        for data in extracted_data.get('data_usage', []):
            try:
                date_str = f"{data['date']}, {current_year}"
                timestamp = parse(date_str)
                records.append(ExtractedData(
                    source_file=filename,
                    phone_line="N/A",
                    event_type='Datos',
                    timestamp=timestamp,
                    direction=None,
                    contact=None,
                    description="Uso de datos",
                    value=f"{data.get('megabytes', 0):.2f} MB"
                ))
            except Exception:
                continue
        
        print(f"AI extrajo {len(records)} registros de {len(page_summaries)} páginas")
        return records
        
    except Exception as e:
        print(f"Error en AI: {e}")
        return []

def process_with_comprehensive_regex(full_text: str, filename: str) -> list:
    """
    Procesamiento regex completo y robusto para todas las páginas
    """
    records = []
    current_year = "2024"
    
    # Patrones múltiples para máxima cobertura
    call_patterns = [
        # Patrón principal: fecha hora dirección contacto duración
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s+([^\n]+?)\s+(\d+)\s*(?:min)?",
        # Patrón con paréntesis: Jun 16 6:16 PM OUT (818) 466-3558 to somewhere 15
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s+\(?([^)]+)\)?\s*(?:to|from)?\s*([^\d]*?)\s*(\d+)",
        # Patrón flexible
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s*([AP]M)?\s+(IN|OUT)\s+([^\n]+?)\s+(\d+)"
    ]
    
    for pattern in call_patterns:
        matches = re.finditer(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) >= 6:
                    month, day = groups[0], groups[1]
                    time = groups[2] if 'M' in groups[2] else f"{groups[2]} {groups[3]}" if len(groups) > 3 and groups[3] else f"{groups[2]} PM"
                    
                    direction = contact = minutes = None
                    for group in groups[2:]:
                        if group and group.upper() in ['IN', 'OUT']:
                            direction = group.upper()
                        elif group and group.isdigit() and not minutes:
                            minutes = int(group)
                        elif group and not contact and not group.upper() in ['IN', 'OUT', 'AM', 'PM']:
                            contact = group.strip()
                    
                    if direction and minutes:
                        date_str = f"{month} {day}, {current_year} {time}"
                        timestamp = parse(date_str)
                        
                        records.append(ExtractedData(
                            source_file=filename,
                            phone_line="N/A",
                            event_type='Llamada',
                            timestamp=timestamp,
                            direction=direction,
                            contact=contact or 'Unknown',
                            description=f"Llamada {direction.lower()}",
                            value=f"{minutes} min"
                        ))
            except Exception:
                continue
    
    # Patrones para mensajes
    message_patterns = [
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s+(\w+)\s*(?:TEXT|TXT|PIC)",
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s*(?:TEXT|TXT|PIC)\s+(\w+)"
    ]
    
    for pattern in message_patterns:
        matches = re.finditer(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) >= 5:
                    month, day, time, direction, contact = groups[:5]
                    date_str = f"{month} {day}, {current_year} {time}"
                    timestamp = parse(date_str)
                    
                    records.append(ExtractedData(
                        source_file=filename,
                        phone_line="N/A",
                        event_type='Mensaje',
                        timestamp=timestamp,
                        direction=direction.upper(),
                        contact=contact,
                        description=f"Mensaje {direction.lower()}",
                        value="TXT"
                    ))
            except Exception:
                continue
    
    # Patrones para datos
    data_patterns = [
        r"(\w{3})\s+(\d{1,2})\s+.*?(\d+(?:\.\d+)?)\s*(?:MB|GB)",
        r"Data\s+usage.*?(\w{3})\s+(\d{1,2}).*?(\d+(?:\.\d+)?)\s*(?:MB|GB)"
    ]
    
    for pattern in data_patterns:
        matches = re.finditer(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) >= 3:
                    month, day, usage = groups[0], groups[1], groups[2]
                    date_str = f"{month} {day}, {current_year}"
                    timestamp = parse(date_str)
                    
                    records.append(ExtractedData(
                        source_file=filename,
                        phone_line="N/A",
                        event_type='Datos',
                        timestamp=timestamp,
                        direction=None,
                        contact=None,
                        description="Uso de datos",
                        value=f"{usage} MB"
                    ))
            except Exception:
                continue
    
    print(f"Regex extrajo {len(records)} registros del texto completo")
    return records

def save_records_to_db(records: list, filename: str) -> int:
    """Guarda los registros en la base de datos"""
    if not records:
        return 0
        
    db = SessionLocal()
    try:
        # Eliminar registros anteriores de este archivo
        db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
        
        # Insertar nuevos registros
        for record in records:
            db.add(record)
        
        db.commit()
        return len(records)
    finally:
        db.close()