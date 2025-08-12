import pdfplumber
import pandas as pd
from dateutil.parser import parse
import os
from app.config import CALL_PATTERN, MESSAGE_PATTERN, DATA_USAGE_PATTERN
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def process_pdf(filepath: str, pages: list[int]):
    all_records = []
    filename = os.path.basename(filepath)
    current_year = "2024" # Asumir año actual si no está en el texto

    with pdfplumber.open(filepath) as pdf:
        full_text = ""
        for page_num in pages:
            page = pdf.pages[page_num - 1] # pdf.pages es 0-indexed
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # Procesar llamadas
    for match in CALL_PATTERN.finditer(full_text):
        month, day, time, call_type, phone, desc, _, minutes = match.groups()
        try:
            date_str = f"{month} {day}, {current_year} {time}"
            all_records.append({
                "source_file": filename, "event_type": "Llamada", "timestamp": parse(date_str),
                "detail_1": phone.strip(), "detail_2": f"{minutes} min", "detail_3": "Recibida" if call_type == "IN" else "Realizada",
                "numeric_value": int(minutes)
            })
        except Exception: continue

    # Procesar mensajes
    for match in MESSAGE_PATTERN.finditer(full_text):
        month, day, time, msg_type, contact, destination, msg_format = match.groups()
        try:
            date_str = f"{month} {day}, {current_year} {time}"
            all_records.append({
                "source_file": filename, "event_type": "Mensaje", "timestamp": parse(date_str),
                "detail_1": contact.strip(), "detail_2": msg_format, "detail_3": "Recibido" if msg_type == "IN" else "Enviado",
                "numeric_value": None
            })
        except Exception: continue

    # Procesar uso de datos
    for match in DATA_USAGE_PATTERN.finditer(full_text):
        month, day, mb_used_str = match.groups()
        try:
            date_str = f"{month} {day}, {current_year}"
            mb_used = float(mb_used_str.replace(',', ''))
            all_records.append({
                "source_file": filename, "event_type": "Datos", "timestamp": parse(date_str),
                "detail_1": f"{mb_used:.2f} MB", "detail_2": None, "detail_3": None,
                "numeric_value": mb_used
            })
        except Exception: continue

    # Guardar en DB
    if not all_records: return 0
    
    db = SessionLocal()
    try:
        # Borrar datos viejos para este archivo
        db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
        
        # Insertar nuevos datos
        for record in all_records:
            db_record = ExtractedData(**record)
            db.add(db_record)
        
        db.commit()
        return len(all_records)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()