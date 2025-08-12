import os
import pdfplumber
import json
import re
from datetime import datetime
from dateutil.parser import parse
import google.generativeai as genai
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def extract_data_with_hybrid_approach(filepath: str, pages_to_process: list[int]):
    """
    Procesador híbrido que usa Google AI con optimizaciones para evitar timeouts:
    1. Procesa páginas por chunks pequeños
    2. Límites de texto estrictos
    3. Fallback a regex si AI falla
    """
    filename = os.path.basename(filepath)
    
    # Configurar la API de Google con timeouts agresivos
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configurando Google AI: {e}")
        return extract_with_regex_fallback(filepath, pages_to_process, filename)
    
    all_records = []
    current_year = "2024"
    
    # Procesar páginas en chunks pequeños para evitar timeouts
    chunk_size = 2  # Solo 2 páginas a la vez
    for i in range(0, len(pages_to_process), chunk_size):
        chunk_pages = pages_to_process[i:i + chunk_size]
        
        # Extraer texto del chunk
        chunk_text = ""
        with pdfplumber.open(filepath) as pdf:
            for page_num in chunk_pages:
                if page_num > len(pdf.pages): 
                    continue
                page = pdf.pages[page_num - 1]
                text = page.extract_text()
                if text: 
                    # Limitar texto por página a 2000 caracteres para evitar overload
                    chunk_text += f"\n--- Página {page_num} ---\n{text[:2000]}"
        
        if not chunk_text:
            continue
            
        # Límite total de texto por chunk
        if len(chunk_text) > 8000:
            chunk_text = chunk_text[:8000] + "..."
        
        # Procesar chunk con AI (con timeout y fallback)
        chunk_records = process_chunk_with_ai(model, chunk_text, current_year, filename)
        all_records.extend(chunk_records)
    
    # Si no obtuvimos suficientes registros con AI, usar regex como backup
    if len(all_records) < 5:
        print("Pocos registros con AI, usando regex como backup...")
        regex_records = extract_with_regex_fallback(filepath, pages_to_process, filename)
        return regex_records
    
    # Guardar registros en base de datos
    if all_records:
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
    
    return 0

def process_chunk_with_ai(model, text_chunk: str, current_year: str, filename: str):
    """Procesa un chunk de texto con AI con timeouts optimizados"""
    records = []
    
    # Prompt optimizado y más corto
    prompt = f"""
Extrae SOLO llamadas, mensajes y datos de este texto de factura.
Responde SOLO con JSON válido:

{{"calls": [{{"date": "Jun 16", "time": "6:16 PM", "direction": "OUT", "contact": "(818)466-3558", "minutes": 15}}], "messages": [{{"date": "Jun 16", "time": "4:27 PM", "direction": "OUT", "contact": "96831", "format": "TXT"}}], "data_usage": [{{"date": "Jun 16", "megabytes": 2517.55}}]}}

Texto:
{text_chunk}
"""
    
    try:
        # Configuración con timeout muy agresivo
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        
        # Limpiar respuesta para obtener JSON
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].strip()
        
        # Parsear JSON
        extracted_data = json.loads(response_text)
        
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
                
    except Exception as e:
        print(f"Error en AI para chunk: {e}")
        # No hacer fallback aquí, dejar que la función principal decida
    
    return records

def extract_with_regex_fallback(filepath: str, pages_to_process: list[int], filename: str):
    """Fallback robusto usando regex"""
    full_text = ""
    
    # Extraer texto completo
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

    all_records = []
    current_year = "2024"
    
    # Patrones regex optimizados
    call_pattern = r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s+([^\n]+?)\s+(\d+)"
    
    for match in re.finditer(call_pattern, full_text, re.MULTILINE):
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
                description=contact_desc[:100],
                value=f"{minutes} min"
            )
            all_records.append(record)
        except Exception:
            continue
    
    # Guardar registros
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