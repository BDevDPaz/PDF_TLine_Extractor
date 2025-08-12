import os
import pandas as pd
from google import genai
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def get_chat_response(user_prompt: str, history: list):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Obtener los datos de la base de datos como contexto
    db = SessionLocal()
    try:
        query = db.query(ExtractedData)
        df = pd.read_sql(query.statement, query.session.bind)
        if df.empty:
            context = "No hay datos extraídos en la base de datos todavía."
        else:
            context = df.to_string()
    finally:
        db.close()

    system_instruction = f"""
    Eres un analista de datos experto en facturas de telecomunicaciones.
    Tu tarea es responder preguntas del usuario basándote únicamente en los siguientes datos extraídos.
    No inventes información. Si la respuesta no está en los datos, dilo claramente.
    Aquí están los datos:
    ---
    {context}
    ---
    """
    
    # Construir el historial de conversación para la API
    messages = [{"role": "system", "parts": [system_instruction]}]
    for item in history:
        messages.append({"role": item["role"], "parts": [item["parts"][0]]})
    messages.append({"role": "user", "parts": [user_prompt]})
    
    response = model.generate_content(messages)
    return response.text