import os
import pdfplumber
from app.ai_chat import get_chat_response

def process_chat_file_upload(file_path: str, user_question: str) -> str:
    """
    Procesa un archivo PDF cargado directamente en el chat y responde la pregunta del usuario
    """
    try:
        # Extraer texto del PDF
        full_text = ""
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages[:10]):  # Limitar a 10 páginas para chat
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Página {i+1} ---\n{text[:3000]}..."  # Limitar por página
        
        if not full_text:
            return "No se pudo extraer texto del archivo PDF."
        
        # Crear contexto especial para el chat con archivo adjunto
        context_prompt = f"""
El usuario ha adjuntado un archivo PDF con el siguiente contenido:

{full_text[:10000]}

Pregunta del usuario: {user_question}

Por favor responde basándote únicamente en el contenido del archivo adjunto.
"""
        
        # Usar el sistema de chat existente pero con contexto del archivo
        response = get_chat_response(context_prompt, [])
        return response
        
    except Exception as e:
        return f"Error procesando el archivo: {str(e)}"

def export_chat_history(chat_history: list) -> str:
    """
    Exporta el historial de chat a formato texto
    """
    export_text = "=== HISTORIAL DE CHAT ===\n\n"
    
    for i, message in enumerate(chat_history, 1):
        role = "USUARIO" if message.get('role') == 'user' else "ASISTENTE"
        content = message.get('content', '')
        timestamp = message.get('timestamp', 'Sin fecha')
        
        export_text += f"{i}. [{timestamp}] {role}:\n{content}\n\n"
        export_text += "-" * 50 + "\n\n"
    
    return export_text