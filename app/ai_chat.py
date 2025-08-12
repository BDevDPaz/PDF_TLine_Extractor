import os
import pandas as pd
import google.generativeai as genai
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def get_chat_response(user_prompt: str, history: list):
    # Configurar la API de Google
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Obtener los datos de la base de datos como contexto
    db = SessionLocal()
    try:
        data = db.query(ExtractedData).all()
        if not data:
            context = "No hay datos extraídos en la base de datos todavía. El usuario necesita subir y procesar un PDF primero."
        else:
            # Crear un resumen estructurado de los datos
            context_lines = []
            context_lines.append(f"Total de registros: {len(data)}")
            
            # Agrupar por tipo de evento
            events_by_type = {}
            for item in data:
                event_type = item.event_type
                if event_type not in events_by_type:
                    events_by_type[event_type] = []
                events_by_type[event_type].append({
                    'phone_line': item.phone_line,
                    'timestamp': str(item.timestamp),
                    'direction': item.direction,
                    'contact': item.contact,
                    'description': item.description,
                    'value': item.value
                })
            
            for event_type, items in events_by_type.items():
                context_lines.append(f"\n{event_type}s ({len(items)} registros):")
                for item in items[:10]:  # Limitar a 10 ejemplos por tipo
                    context_lines.append(f"  - {item}")
            
            context = "\n".join(context_lines)
    finally:
        db.close()

    # Crear el prompt con contexto
    system_instruction = f"""
Eres un analista de datos experto en facturas de telecomunicaciones.
Tu tarea es responder preguntas del usuario basándote únicamente en los siguientes datos extraídos.
No inventes información. Si la respuesta no está en los datos, dilo claramente.

DATOS DISPONIBLES:
{context}

Responde de manera clara y concisa en español. Si el usuario pregunta por estadísticas, calcula los números basándote en los datos proporcionados.
"""
    
    full_prompt = f"{system_instruction}\n\nPregunta del usuario: {user_prompt}"
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error al procesar la consulta: {str(e)}"