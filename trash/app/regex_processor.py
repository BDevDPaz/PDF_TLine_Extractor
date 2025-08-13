import os
import pdfplumber
import re
from datetime import datetime
from dateutil.parser import parse
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def extract_data_with_regex(filepath: str, pages_to_process: list[int]):
    """Extractor robusto basado en patrones regex para facturas de telecomunicaciones"""
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

    all_records = []
    current_year = "2024"
    
    # Patrón mejorado para llamadas - busca registros con fecha, hora, dirección, contacto y duración
    call_patterns = [
        # Patrón principal: Jun 16 6:16 PM OUT (818) 466-3558 to Canogapark/CA 15
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM))\s+(IN|OUT)\s+\(?([^)]+|\d{10}|\(\d{3}\)\s*\d{3}-\d{4})\)?\s*(?:to|from)?\s*([^\d]*?)\s*(\d+)",
        # Patrón alternativo: fecha hora dirección número duración
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s*([AP]M)?\s+(IN|OUT)\s+([^\s]+)\s+.*?(\d+)\s*(?:min|mins)?",
        # Patrón simplificado
        r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s+(IN|OUT)\s+([^\\n]+?)\s+(\d+)\s*$"
    ]
    
    for pattern in call_patterns:
        matches = re.finditer(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) >= 6:
                    month, day, time = groups[0], groups[1], groups[2]
                    # Buscar dirección en los grupos
                    direction = None
                    contact = None
                    minutes = None
                    
                    for group in groups[3:]:
                        if group and group.upper() in ['IN', 'OUT']:
                            direction = group.upper()
                        elif group and group.isdigit() and not minutes:
                            minutes = int(group)
                        elif group and not contact:
                            contact = group.strip()
                    
                    if direction and minutes:
                        # Asegurar que el tiempo tenga AM/PM
                        if 'AM' not in time.upper() and 'PM' not in time.upper():
                            hour = int(time.split(':')[0])
                            if hour < 12:
                                time += ' AM'
                            else:
                                time += ' PM'
                        
                        date_str = f"{month} {day}, {current_year} {time}"
                        timestamp = parse(date_str)
                        
                        record = ExtractedData(
                            source_file=filename,
                            phone_line="N/A",
                            event_type='Llamada',
                            timestamp=timestamp,
                            direction=direction,
                            contact=contact or 'Unknown',
                            description=f"Llamada {direction.lower()}",
                            value=f"{minutes} min"
                        )
                        all_records.append(record)
            except Exception as e:
                continue
    
    # Patrón para mensajes - busca TEXT con fecha, hora y dirección
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
                    
                    record = ExtractedData(
                        source_file=filename,
                        phone_line="N/A",
                        event_type='Mensaje',
                        timestamp=timestamp,
                        direction=direction.upper(),
                        contact=contact,
                        description=f"Mensaje {direction.lower()}",
                        value="TXT"
                    )
                    all_records.append(record)
            except Exception:
                continue
    
    # Patrón para uso de datos - busca registros con MB o GB
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
                    
                    record = ExtractedData(
                        source_file=filename,
                        phone_line="N/A",
                        event_type='Datos',
                        timestamp=timestamp,
                        direction=None,
                        contact=None,
                        description="Uso de datos",
                        value=f"{usage} MB"
                    )
                    all_records.append(record)
            except Exception:
                continue
    
    # Si no encontramos registros específicos, buscar cualquier patrón de fecha/hora
    if not all_records:
        # Patrón genérico para cualquier línea con fecha y hora
        generic_pattern = r"(\w{3})\s+(\d{1,2})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s+(.+)"
        matches = re.finditer(generic_pattern, full_text, re.MULTILINE)
        
        for match in matches:
            try:
                month, day, time, content = match.groups()
                
                # Determinar tipo de evento basado en contenido
                event_type = 'Llamada'
                direction = None
                contact = 'Unknown'
                value = 'N/A'
                
                content_upper = content.upper()
                if 'IN' in content_upper:
                    direction = 'IN'
                elif 'OUT' in content_upper:
                    direction = 'OUT'
                
                if 'TEXT' in content_upper or 'TXT' in content_upper:
                    event_type = 'Mensaje'
                    value = 'TXT'
                elif 'DATA' in content_upper or 'MB' in content_upper:
                    event_type = 'Datos'
                    mb_match = re.search(r'(\d+(?:\.\d+)?)\s*MB', content_upper)
                    if mb_match:
                        value = f"{mb_match.group(1)} MB"
                
                # Buscar números de teléfono en el contenido
                phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
                if phone_match:
                    contact = phone_match.group()
                
                # Asegurar que el tiempo tenga AM/PM
                if time and 'AM' not in time.upper() and 'PM' not in time.upper():
                    hour = int(time.split(':')[0])
                    if hour < 12:
                        time += ' AM'
                    else:
                        time += ' PM'
                
                date_str = f"{month} {day}, {current_year} {time}"
                timestamp = parse(date_str)
                
                record = ExtractedData(
                    source_file=filename,
                    phone_line="N/A",
                    event_type=event_type,
                    timestamp=timestamp,
                    direction=direction,
                    contact=contact,
                    description=content[:100],
                    value=value
                )
                all_records.append(record)
                
                # Limitar a 50 registros genéricos para evitar ruido
                if len(all_records) >= 50:
                    break
                    
            except Exception:
                continue
    
    # Guardar en la base de datos
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