import os
import google.generativeai as genai

def generate_ai_content(prompt: str) -> tuple[bool, str]:
    """
    Generate AI content using Google Gemini API
    
    Args:
        prompt: The text prompt to send to the AI
        
    Returns:
        Tuple of (success: bool, content: str)
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return False, "La API de IA no está configurada en el servidor."
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return True, response.text
        
    except Exception as e:
        return False, f"Error en la API de IA: {str(e)}"
