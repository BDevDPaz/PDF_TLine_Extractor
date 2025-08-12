import os
import pdfplumber
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from app.db.database import SessionLocal
from app.db.models import ExtractedData

# --- Definir la Plantilla/Esquema de Datos con Pydantic ---
class CallRecord(BaseModel):
    phone_line: str = Field(description="La línea telefónica que realizó o recibió la llamada, ej: (818) 466-3558")
    timestamp_str: str = Field(description="La fecha y hora de la llamada, ej: 'Jun 16 6:16 PM'")
    direction: str = Field(description="La dirección de la llamada, 'IN' o 'OUT'")
    contact_number: str = Field(description="El número de teléfono al que se llamó o del que se recibió la llamada")
    description: str = Field(description="El destino o descripción de la llamada, ej: to Canogapark/CA")
    minutes: int = Field(description="La duración de la llamada en minutos")

class MessageRecord(BaseModel):
    phone_line: str = Field(description="La línea telefónica que envió o recibió el mensaje")
    timestamp_str: str = Field(description="La fecha y hora del mensaje, ej: 'Jun 16 4:27 PM'")
    direction: str = Field(description="La dirección del mensaje, 'IN' o 'OUT'")
    contact: str = Field(description="El número o contacto del mensaje")
    format: str = Field(description="El formato del mensaje, 'TXT' o 'PIC'")

class DataUsageRecord(BaseModel):
    phone_line: str = Field(description="La línea telefónica que usó los datos")
    date_str: str = Field(description="La fecha del uso de datos, ej: 'Jun 16'")
    megabytes_used: float = Field(description="La cantidad de datos usados en MB, ej: 2517.5465")

class BillingData(BaseModel):
    calls: List[CallRecord]
    messages: List[MessageRecord]
    data_usage: List[DataUsageRecord]

# --- Función de Extracción con IA ---
def extract_data_with_ai(filepath: str, pages_to_process: list[int]):
    from dateutil.parser import parse

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')

    filename = os.path.basename(filepath)
    full_text = ""
    with pdfplumber.open(filepath) as pdf:
        for page_num in pages_to_process:
            if page_num > len(pdf.pages): continue
            page = pdf.pages[page_num - 1]
            text = page.extract_text()
            if text: full_text += f"\n--- Contenido de Página {page_num} ---\n{text}"

    if not full_text: return 0

    prompt = f"Analiza el siguiente texto de una factura de T-Mobile y extrae TODAS las llamadas (TALK), mensajes (TEXT) y registros de uso de datos (DATA). Presta especial atención a qué línea telefónica pertenece cada registro. Formatea tu respuesta estrictamente como un objeto JSON que siga el esquema proporcionado. Texto de la factura:\n\n{full_text}"
    
    response = model.generate_content(
        contents=prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": BillingData.model_json_schema()
        }
    )
    
    extracted = BillingData.model_validate_json(response.text)
    
    all_records = []
    current_year = "2024"

    for call in extracted.calls:
        all_records.append(ExtractedData(
            source_file=filename, phone_line=call.phone_line, event_type='Llamada',
            timestamp=parse(f"{call.timestamp_str}, {current_year}"), direction=call.direction,
            contact=call.contact_number, description=call.description, value=f"{call.minutes} min"
        ))
    for msg in extracted.messages:
         all_records.append(ExtractedData(
            source_file=filename, phone_line=msg.phone_line, event_type='Mensaje',
            timestamp=parse(f"{msg.timestamp_str}, {current_year}"), direction=msg.direction,
            contact=msg.contact, description=None, value=msg.format
        ))
    for data in extracted.data_usage:
         all_records.append(ExtractedData(
            source_file=filename, phone_line=data.phone_line, event_type='Datos',
            timestamp=parse(f"{data.date_str}, {current_year}"), direction=None,
            contact=None, description="Uso de datos", value=f"{data.megabytes_used:.2f} MB"
        ))

    db = SessionLocal()
    try:
        db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
        db.add_all(all_records)
        db.commit()
        return len(all_records)
    finally:
        db.close()