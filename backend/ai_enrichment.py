try:
    import google.generativeai as genai
except ImportError:
    genai = None
import os
from models import SessionLocal, CallEvent, TextEvent
from sqlalchemy import distinct

def configure_ai():
    try:
        if not genai:
            print("ADVERTENCIA: Módulo google-generativeai no disponible.")
            return None
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("ADVERTENCIA: GOOGLE_API_KEY no encontrada. La IA no funcionará.")
            return None
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"Error al configurar la API de IA: {e}")
        return None

model = configure_ai()

def categorize_phone_numbers():
    if not model: return
    
    session = SessionLocal()
    try:
        # Obtener todos los números únicos que no han sido categorizados
        call_numbers = session.query(distinct(CallEvent.counterpart_number)).filter(CallEvent.ai_category == "Desconocido").all()
        text_numbers = session.query(distinct(TextEvent.counterpart_number)).filter(TextEvent.ai_category == "Desconocido").all()
        
        unique_numbers = {num[0] for num in call_numbers + text_numbers if num[0]}

        for number in unique_numbers:
            prompt = f"Categoriza este número de teléfono: {number}. Las categorías son: 'Empresa/Servicio', 'Spam Potencial', 'Personal', 'Desconocido'. Responde solo con una categoría."
            try:
                response = model.generate_content(prompt)
                category = response.text.strip()
                
                # Actualizar todos los registros con este número
                session.query(CallEvent).filter(CallEvent.counterpart_number == number).update({"ai_category": category})
                session.query(TextEvent).filter(TextEvent.counterpart_number == number).update({"ai_category": category})

            except Exception as e:
                print(f"Error de IA categorizando {number}: {e}")
        
        session.commit()
        print("Categorización por IA completada.")
    except Exception as e:
        session.rollback()
        print(f"Error de base de datos durante la categorización: {e}")
    finally:
        session.close()