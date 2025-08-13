import re
import pdfplumber
from datetime import datetime
from dateutil import parser as dateutil_parser
from app.db.database import SessionLocal
from app.db.models import ExtractedData

def limpiar_numero_telefono(numero_str):
    """Limpia números telefónicos eliminando caracteres no numéricos"""
    if not numero_str:
        return None
    return re.sub(r'\D', '', numero_str)

def extract_data_with_enhanced_regex(filepath, selected_pages):
    """
    Extractor mejorado basado en tus procesadores existentes
    Específicamente diseñado para facturas T-Mobile
    """
    db = SessionLocal()
    try:
        # Limpiar datos existentes del mismo archivo
        filename = filepath.split('/')[-1]
        db.query(ExtractedData).filter(ExtractedData.source_file == filename).delete()
        
        record_count = 0
        
        with pdfplumber.open(filepath) as pdf:
            # Extraer año de facturación
            texto_primera_pagina = pdf.pages[0].extract_text(x_tolerance=2) or ""
            match_anual = re.search(r'Bill issue date.*?(\b20\d{2}\b)', texto_primera_pagina, re.DOTALL)
            bill_year = int(match_anual.group(1)) if match_anual else datetime.now().year
            
            # Estado persistente
            fecha_actual_str = None
            seccion_actual = "Desconocida"
            linea_actual = "Desconocida"
            
            # Patrones regex mejorados basados en tus extractores
            regex_usuario_linea = re.compile(r"^\s*(\(\d{3}\)\s*\d{3}-\d{4})\s+(\w{3}\s+\d{1,2}\s+-\s+\w{3}\s+\d{1,2})")
            
            regex_talk_detail = re.compile(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+"
                r"(\d{1,2}:\d{2}\s+(?:AM|PM))\s+"
                r"(IN|OUT)\s+"
                r"((?:\(\d{3}\)\s*\d{3}-\d{4})|\d{3,15}|(?:1-8\d{2}\s*\#)|[\w\s\./\(\)\-\:]+?)\s+"
                r"(.*?)\s+"
                r"([A-ZCHFWG]|-)\s+"
                r"(\d+|-)\s*"
                r"(-|\$[\d\.]+)$"
            )
            
            regex_text_detail = re.compile(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+"
                r"(\d{1,2}:\d{2}\s+(?:AM|PM))\s+"
                r"(IN|OUT)\s+"
                r"(.+?)\s+"
                r"(TXT|PIC)\s*"
                r"(-|\$[\d\.]+)$"
            )
            
            for page_num in selected_pages:
                if page_num > len(pdf.pages):
                    continue
                    
                page = pdf.pages[page_num - 1]
                texto_pagina = page.extract_text(x_tolerance=2, layout=True)
                if not texto_pagina:
                    continue
                
                # Detectar sección actual
                if "TALK" in texto_pagina:
                    seccion_actual = "LLAMADA"
                elif "TEXT" in texto_pagina:
                    seccion_actual = "TEXTO/MMS"
                elif "DATA" in texto_pagina:
                    seccion_actual = "DATOS"
                
                # Detectar línea telefónica
                match_linea_header = regex_usuario_linea.search(texto_pagina)
                if match_linea_header:
                    linea_actual = limpiar_numero_telefono(match_linea_header.group(1))
                
                for linea in texto_pagina.split('\n'):
                    linea_texto = linea.strip()
                    
                    if not linea_texto or "CONTINUED" in linea_texto or "TOTALS" in linea_texto:
                        continue
                    
                    # Actualizar fecha actual
                    match_fecha = re.search(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', linea_texto, re.IGNORECASE)
                    if match_fecha:
                        try:
                            fecha_obj = datetime.strptime(f"{match_fecha.group(0)} {bill_year}", "%b %d %Y")
                            fecha_actual_str = fecha_obj.strftime("%Y-%m-%d")
                        except ValueError:
                            pass
                    
                    # Procesar llamadas
                    if seccion_actual == "LLAMADA":
                        match_detalle = regex_talk_detail.match(linea_texto)
                        if match_detalle and fecha_actual_str:
                            mes_str, dia_str, hora_str, direccion, campo_quien_raw, desc_larga_raw, tipo_llamada, minutos_str, costo_str = match_detalle.groups()
                            
                            fecha_str_completa = f"{mes_str} {dia_str} {bill_year} {hora_str}"
                            try:
                                fecha_evento = dateutil_parser.parse(fecha_str_completa)
                            except:
                                continue
                            
                            # Extraer número de contacto
                            numero_otra_parte = "N/A"
                            descripcion_final = f"{campo_quien_raw.strip()} {desc_larga_raw.strip()}".strip()
                            
                            num_match_quien = re.match(r"((?:\(\d{3}\)\s*\d{3}-\d{4})|\d{7,15}|1-8\d{2}\s*\#|\d{3,4})", campo_quien_raw.strip())
                            if num_match_quien and num_match_quien.group(0) == campo_quien_raw.strip():
                                numero_otra_parte = limpiar_numero_telefono(campo_quien_raw)
                                descripcion_final = desc_larga_raw.strip() if desc_larga_raw.strip() != "-" else ""
                            
                            # Crear registro
                            new_record = ExtractedData(
                                source_file=filename,
                                phone_line=linea_actual,
                                event_type="Llamada",
                                timestamp=fecha_evento,
                                direction="IN" if direccion == "IN" else "OUT",
                                contact=numero_otra_parte,
                                description=descripcion_final,
                                value=f"{minutos_str} min" if minutos_str.isdigit() else None
                            )
                            db.add(new_record)
                            record_count += 1
                    
                    # Procesar mensajes
                    elif seccion_actual == "TEXTO/MMS":
                        match_detalle = regex_text_detail.match(linea_texto)
                        if match_detalle and fecha_actual_str:
                            mes_str, dia_str, hora_str, direccion, destino_str_raw, tipo_msg, costo_str = match_detalle.groups()
                            
                            fecha_str_completa = f"{mes_str} {dia_str} {bill_year} {hora_str}"
                            try:
                                fecha_evento = dateutil_parser.parse(fecha_str_completa)
                            except:
                                continue
                            
                            # Limpiar destino
                            destino_limpio = destino_str_raw.strip()
                            num_destino_match = re.match(r"((?:\(\d{3}\)\s*\d{3}-\d{4})|\d{3,15}|(?:1-8\d{2}\s*\#))", destino_limpio)
                            numero_otra_parte = limpiar_numero_telefono(num_destino_match.group(1)) if num_destino_match else limpiar_numero_telefono(destino_limpio.split(" ")[0])
                            
                            # Crear registro
                            new_record = ExtractedData(
                                source_file=filename,
                                phone_line=linea_actual,
                                event_type="Mensaje",
                                timestamp=fecha_evento,
                                direction="IN" if direccion == "IN" else "OUT",
                                contact=numero_otra_parte,
                                description=destino_limpio,
                                value=tipo_msg.strip()
                            )
                            db.add(new_record)
                            record_count += 1
        
        db.commit()
        return record_count
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()