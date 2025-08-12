import os
import pdfplumber
import json
import re
from datetime import datetime
from dateutil.parser import parse
import google.generativeai as genai
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def extract_data_with_ai(filepath: str, pages_to_process: list[int]):
    # Configurar la API de Google
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')

    filename = os.path.basename(filepath)
    full_text = ""
    
    # Extraer texto del PDF
    with pdfplumber.open(filepath) as pdf:
        for page_num in pages_to_process:
            if page_num > len(pdf.pages): 
                continue
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            if text: 
                full_text += f"\n--- Página {page_num} ---\n{text}"

    if not full_text: 
        return 0

    # Prompt para la IA
    prompt = f"""
Analiza el siguiente texto de una factura de telecomunicaciones y extrae TODOS los registros de:

1. LLAMADAS (TALK): busca líneas con fechas, horas, direcciones (IN/OUT), números de teléfono y duración en minutos
2. MENSAJES (TEXT): busca líneas con fechas, horas, direcciones (IN/OUT), contactos y formato (TXT/PIC)
3. DATOS (DATA): busca registros de uso de datos con fechas y megabytes usados

Responde SOLO con un JSON válido en este formato exacto:
{{
  "calls": [
    {{
      "phone_line": "(555) 123-4567",
      "date": "Jun 16", 
      "time": "6:16 PM",
      "direction": "OUT",
      "contact": "(818) 466-3558", 
      "description": "to Canogapark/CA",
      "minutes": 15
    }}
  ],
  "messages": [
    {{
      "phone_line": "(555) 123-4567",
      "date": "Jun 16",
      "time": "4:27 PM", 
      "direction": "OUT",
      "contact": "96831",
      "format": "TXT"
    }}
  ],
  "data_usage": [
    {{
      "phone_line": "(555) 123-4567",
      "date": "Jun 16",
      "megabytes": 2517.55
    }}
  ]
}}

Texto de la factura:
{full_text}
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Limpiar el texto de respuesta para obtener solo el JSON
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].strip()
        
        # Parsear JSON
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Si no es JSON válido, intentar extraer con regex básico
            return extract_with_fallback_regex(full_text, filename)
        
        # Procesar los datos extraídos
        all_records = []
        current_year = "2024"
        
        # Procesar llamadas
        for call in extracted_data.get('calls', []):
            try:
                date_str = f"{call['date']} {call['time']}, {current_year}"
                timestamp = parse(date_str)
                all_records.append(ExtractedData(
                    source_file=filename,
                    phone_line=call.get('phone_line', 'N/A'),
                    event_type='Llamada',
                    timestamp=timestamp,
                    direction=call.get('direction'),
                    contact=call.get('contact'),
                    description=call.get('description', ''),
                    value=f"{call.get('minutes', 0)} min"
                ))
            except Exception:
                continue
        
        # Procesar mensajes
        for msg in extracted_data.get('messages', []):
            try:
                date_str = f"{msg['date']} {msg['time']}, {current_year}"
                timestamp = parse(date_str)
                all_records.append(ExtractedData(
                    source_file=filename,
                    phone_line=msg.get('phone_line', 'N/A'),
                    event_type='Mensaje',
                    timestamp=timestamp,
                    direction=msg.get('direction'),
                    contact=msg.get('contact'),
                    description='',
                    value=msg.get('format', 'TXT')
                ))
            except Exception:
                continue
        
        # Procesar uso de datos
        for data in extracted_data.get('data_usage', []):
            try:
                date_str = f"{data['date']}, {current_year}"
                timestamp = parse(date_str)
                all_records.append(ExtractedData(
                    source_file=filename,
                    phone_line=data.get('phone_line', 'N/A'),
                    event_type='Datos',
                    timestamp=timestamp,
                    direction=None,
                    contact=None,
                    description='Uso de datos',
                    value=f"{data.get('megabytes', 0):.2f} MB"
                ))
            except Exception:
                continue
        
        # Guardar en la base de datos
        db = SessionLocal()
        try:
            # Eliminar registros anteriores de este archivo
            db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
            
            # Insertar nuevos registros
            for record in all_records:
                db.add(record)
            
            db.commit()
            return len(all_records)
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error in AI processing: {e}")
        return extract_with_fallback_regex(full_text, filename)

def extract_with_fallback_regex(text: str, filename: str):
    """Extracción de respaldo usando regex básico"""
    all_records = []
    current_year = "2024"
    
    # Patrones regex básicos
    call_pattern = re.compile(
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s+([^\\n\\r]+?)\s+(\d+)",
        re.MULTILINE
    )
    
    for match in call_pattern.finditer(text):
        try:
            month, day, time, direction, contact_desc, minutes = match.groups()
            date_str = f"{month} {day}, {current_year} {time}"
            timestamp = parse(date_str)
            
            record = ExtractedData(
                source_file=filename,
                phone_line="N/A",
                event_type='Llamada',
                timestamp=timestamp,
                direction=direction,
                contact=contact_desc.split()[0] if contact_desc else 'Unknown',
                description=contact_desc,
                value=f"{minutes} min"
            )
            all_records.append(record)
        except Exception:
            continue
    
    # Guardar registros de respaldo
    if all_records:
        db = SessionLocal()
        try:
            db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
            for record in all_records:
                db.add(record)
            db.commit()
            return len(all_records)
        finally:
            db.close()
    
    return 0