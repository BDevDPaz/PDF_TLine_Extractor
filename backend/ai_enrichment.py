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
import os
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Variable global para el modelo
model = None

def initialize_ai():
    """Inicializar el modelo de IA si está disponible"""
    global model
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logging.warning("⚠️ GOOGLE_API_KEY no configurada - IA deshabilitada")
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logging.info("✅ IA Gemini inicializada correctamente")
        return True
    except ImportError:
        logging.warning("⚠️ google-generativeai no instalado - IA deshabilitada")
        return False
    except Exception as e:
        logging.error(f"❌ Error inicializando IA: {e}")
        return False

def categorize_phone_numbers():
    """Categorizar números telefónicos usando IA"""
    try:
        if not model:
            logging.info("🔄 Intentando inicializar IA...")
            if not initialize_ai():
                logging.warning("⚠️ IA no disponible para categorización")
                return
        
        from models import SessionLocal, CallEvent, TextEvent
        
        session = SessionLocal()
        try:
            # Categorizar llamadas
            calls = session.query(CallEvent).filter(CallEvent.ai_category == "Desconocido").limit(50).all()
            for call in calls:
                try:
                    if call.counterpart_number:
                        # Categoría simple basada en patrones
                        if any(keyword in (call.description or "").lower() for keyword in ["voicemail", "buzón"]):
                            call.ai_category = "Buzón de Voz"
                        elif call.counterpart_number.startswith("1"):
                            call.ai_category = "Llamada Nacional"
                        elif len(call.counterpart_number.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")) > 10:
                            call.ai_category = "Internacional"
                        else:
                            call.ai_category = "Local"
                except Exception as e:
                    logging.debug(f"Error categorizando llamada {call.id}: {e}")
            
            # Categorizar mensajes
            texts = session.query(TextEvent).filter(TextEvent.ai_category == "Desconocido").limit(50).all()
            for text in texts:
                try:
                    if text.message_type and "pic" in text.message_type.lower():
                        text.ai_category = "Mensaje con Imagen"
                    elif text.message_type and "mms" in text.message_type.lower():
                        text.ai_category = "Mensaje Multimedia"
                    else:
                        text.ai_category = "Mensaje de Texto"
                except Exception as e:
                    logging.debug(f"Error categorizando texto {text.id}: {e}")
            
            session.commit()
            logging.info(f"✅ Categorización completada: {len(calls)} llamadas, {len(texts)} mensajes")
            
        except Exception as e:
            session.rollback()
            logging.error(f"❌ Error en categorización: {e}")
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"❌ Error general en categorización: {e}")

# Inicializar al importar
initialize_ai()
