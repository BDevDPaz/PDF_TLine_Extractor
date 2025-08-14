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