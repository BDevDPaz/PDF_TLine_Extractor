import json
import os
import re
from datetime import datetime, timezone, timedelta
from PyPDF2 import PdfReader
from dateutil import tz, parser as dateutil_parser

def parse_pdf_date(pdf_date_str):
    if not pdf_date_str or not pdf_date_str.startswith("D:"): return None
    try:
        datestr = pdf_date_str[2:]
        offset_char = None
        if '+' in datestr: offset_char = '+'
        elif '-' in datestr: offset_char = '-'
        elif 'Z' in datestr: datestr = datestr.replace('Z', "+00'00'"); offset_char = '+'
        offset_str = None
        if offset_char:
            parts = datestr.split(offset_char)
            datestr = parts[0]
            if len(parts) > 1: offset_str = offset_char + parts[1].replace("'", "")
        dt_obj = datetime(
            year=int(datestr[0:4]), month=int(datestr[4:6]), day=int(datestr[6:8]),
            hour=int(datestr[8:10]) if len(datestr) >= 10 else 0,
            minute=int(datestr[10:12]) if len(datestr) >= 12 else 0,
            second=int(datestr[12:14]) if len(datestr) >= 14 else 0
        )
        if offset_str:
            offset_hours = int(offset_str[1:3]); offset_minutes = int(offset_str[3:5]) if len(offset_str) >= 5 else 0
            offset_delta = timedelta(hours=offset_hours, minutes=offset_minutes)
            if offset_str.startswith('-'): dt_obj += offset_delta
            else: dt_obj -= offset_delta
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        else: dt_obj = dt_obj.replace(tzinfo=None)
        return dt_obj
    except Exception: return None

def limpiar_numero_telefono(numero_str):
    if not numero_str: return None
    # Elimina todos los caracteres que no sean dígitos
    return re.sub(r'\D', '', numero_str)

def extraer_telefonos_generico_del_texto(texto):
    if not texto: return []
    texto_limpio = texto.replace("\u00a0", " ")
    patron = r"(\+1\s*[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})"
    coincidencias = re.findall(patron, texto_limpio)
    telefonos_limpios = set()
    for m in coincidencias:
        telefono_base = f"{m[1]}{m[2]}{m[3]}"
        telefonos_limpios.add(limpiar_numero_telefono(telefono_base))
    return list(filter(None, telefonos_limpios))

def buscar_palabras_clave_comunicacion(texto):
    if not texto: return {}
    palabras_clave = {
        "llamada": ["call", "llamada", "voice", "voice mail", "buzón de voz"],
        "mensaje": ["message", "mensaje", "sms", "mms", "text", "texto"],
        "entrante": ["incoming", "entrante", "received", "recibido", "from", "de"],
        "saliente": ["outgoing", "saliente", "sent", "enviado", "to", "para", "a"],
        "duracion_clave": ["duration", "duración"],
        "destinatario_clave": ["recipient", "destinatario", "to:", "para:"],
        "remitente_clave": ["sender", "remitente", "from:", "de:"]
    }
    encontradas = {}; texto_lower = texto.lower()
    for cat, terminos in palabras_clave.items():
        for term in terminos:
            if term in texto_lower:
                if cat not in encontradas: encontradas[cat] = []
                encontradas[cat].append(term)
    return encontradas

def extraer_duraciones_del_texto(texto):
    if not texto: return []
    patrones = [
        r'\b(\d{1,2}:\d{2}:\d{2})\b', r'\b(\d{1,2}:\d{2})\b(?!\d)',
        r'\b(\d+)\s*(?:minutos|minuto|min|m)\s*(\d+)\s*(?:segundos|segundo|sec|s)\b',
        r'\b(\d+)\s*(?:minutos|minuto|min|m)\b', r'\b(\d+)\s*(?:segundos|segundo|sec|s)\b'
    ]
    dur_encontradas = set()
    for p in patrones:
        for m in re.findall(p, texto, re.IGNORECASE):
            dur_str = f"{m[0]} min {m[1]} sec" if isinstance(m, tuple) and len(m) > 1 and m[1] else (f"{m[0]} min" if isinstance(m, tuple) else m)
            dur_encontradas.add(dur_str.strip())
    return list(dur_encontradas)

def extraer_cantidades_mensajes_del_texto(texto):
    if not texto: return []
    patron = r'\b(\d+)\s*(?:sms|mms|mensaje[s]?|message[s]?)\b'
    return list(set(m.strip() for m in re.findall(patron, texto, re.IGNORECASE)))

def parsear_detalles_uso_factura_tmobile(texto_completo, ano_factura_predeterminado=str(datetime.now().year)):
    detalles_comunicaciones = []
    lineas_texto = texto_completo.split('\n')
    
    regex_usuario_linea = re.compile(r"^\s*(\(\d{3}\)\s*\d{3}-\d{4})\s+(\w{3}\s+\d{1,2}\s+-\s+\w{3}\s+\d{1,2})")
    regex_talk_detail = re.compile(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+"        # Mes y Día
        r"(\d{1,2}:\d{2}\s+(?:AM|PM))\s+"                                         # Hora
        r"(IN|OUT)\s+"                                                           # Dirección
        r"((?:\(\d{3}\)\s*\d{3}-\d{4})|\d{3,15}|(?:1-8\d{2}\s*\#)|[\w\s\./\(\)\-\:]+?)\s+" # Quién/Num o parte de desc
        r"(.*?)\s+"                                                              # Descripción larga (no golosa)
        r"([A-ZCHFWG]|-)\s+"                                                     # Tipo de llamada
        r"(\d+|-)\s*"                                                            # Minutos
        r"(-|\$[\d\.]+)$"                                                        # Costo
    )
    regex_text_detail = re.compile(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+"        # Mes y Día
        r"(\d{1,2}:\d{2}\s+(?:AM|PM))\s+"                                         # Hora
        r"(IN|OUT)\s+"                                                           # Dirección
        r"(.+?)\s+"                                                              # Destino (puede ser número o texto)
        r"(TXT|PIC)\s*"                                                          # Tipo de mensaje
        r"(-|\$[\d\.]+)$"                                                        # Costo
    )
    
    usuario_linea_actual = None; periodo_actual = None; modo_actual = None 
    ano_factura = ano_factura_predeterminado
    match_fecha_emision = re.search(r"Bill issue date\s+\w{3}\s+\d{1,2},\s*(\d{4})", texto_completo)
    if match_fecha_emision: ano_factura = match_fecha_emision.group(1)

    for i, linea_original in enumerate(lineas_texto):
        linea = linea_original.strip()
        if not linea: continue

        match_usuario = regex_usuario_linea.match(linea_original) 
        if not match_usuario: match_usuario = regex_usuario_linea.match(linea)

        if match_usuario:
            usuario_linea_actual = limpiar_numero_telefono(match_usuario.group(1)) # Limpieza aplicada
            periodo_actual = match_usuario.group(2)
            modo_actual = None 
            continue

        if usuario_linea_actual:
            if linea == "TALK": modo_actual = "TALK"; continue
            elif linea == "TEXT": modo_actual = "TEXT"; continue
            
            if "When Who Description Type Min Cost" in linea_original or \
               "When Who Destination Type Cost" in linea_original or \
               "Totals " in linea or \
               "...CONTINUED -" in linea_original or \
               "APPENDIX_BEGIN" in linea_original or \
               "The date and time corresponds to" in linea_original or \
               linea.startswith("WHO:") or linea.startswith("TYPE:"):
                continue

            if modo_actual == "TALK":
                match_detalle = regex_talk_detail.match(linea)
                if match_detalle:
                    mes_str, dia_str, hora_str, direccion, campo_quien_raw, desc_larga_raw, tipo_llamada, minutos_str, costo_str = match_detalle.groups()
                    fecha_str_completa = f"{mes_str} {dia_str} {ano_factura} {hora_str}"
                    fecha_evento = dateutil_parser.parse(fecha_str_completa) if fecha_str_completa else None
                    
                    numero_otra_parte = "N/A"
                    descripcion_final = f"{campo_quien_raw.strip()} {desc_larga_raw.strip()}".strip()

                    # Intentar identificar si campo_quien_raw es el número
                    num_match_quien = re.match(r"((?:\(\d{3}\)\s*\d{3}-\d{4})|\d{7,15}|1-8\d{2}\s*\#|\d{3,4})", campo_quien_raw.strip())
                    if num_match_quien and num_match_quien.group(0) == campo_quien_raw.strip(): # Si todo el campo es un número
                        numero_otra_parte = limpiar_numero_telefono(campo_quien_raw)
                        descripcion_final = desc_larga_raw.strip() if desc_larga_raw.strip() != "-" else ""
                    elif desc_larga_raw.strip().lower().startswith("to ") or desc_larga_raw.strip().lower() == "incoming":
                         # Esto podría significar que campo_quien_raw es el número
                         if num_match_quien: # Si campo_quien_raw parece un número, usarlo
                            numero_otra_parte = limpiar_numero_telefono(campo_quien_raw)
                            descripcion_final = desc_larga_raw.strip()
                    
                    detalles_comunicaciones.append({
                        "usuario_linea": usuario_linea_actual, "periodo_linea": periodo_actual,
                        "tipo_comunicacion": "llamada",
                        "fecha_hora_iso": fecha_evento.isoformat() if fecha_evento else None,
                        "direccion_flujo": "entrante" if direccion == "IN" else "saliente",
                        "numero_otra_parte": numero_otra_parte,
                        "descripcion_adicional": descripcion_final,
                        "tipo_servicio_factura": tipo_llamada.strip(),
                        "duracion_minutos": int(minutos_str) if minutos_str.isdigit() else None,
                        "costo_str": costo_str })
            elif modo_actual == "TEXT":
                match_detalle = regex_text_detail.match(linea)
                if match_detalle:
                    mes_str, dia_str, hora_str, direccion, destino_str_raw, tipo_msg, costo_str = match_detalle.groups()
                    fecha_str_completa = f"{mes_str} {dia_str} {ano_factura} {hora_str}"
                    fecha_evento = dateutil_parser.parse(fecha_str_completa) if fecha_str_completa else None
                    
                    destino_limpio = destino_str_raw.strip()
                    num_destino_match = re.match(r"((?:\(\d{3}\)\s*\d{3}-\d{4})|\d{3,15}|(?:1-8\d{2}\s*\#))", destino_limpio)
                    numero_otra_parte = limpiar_numero_telefono(num_destino_match.group(1)) if num_destino_match else limpiar_numero_telefono(destino_limpio.split(" ")[0])

                    detalles_comunicaciones.append({
                        "usuario_linea": usuario_linea_actual, "periodo_linea": periodo_actual,
                        "tipo_comunicacion": "mensaje",
                        "fecha_hora_iso": fecha_evento.isoformat() if fecha_evento else None,
                        "direccion_flujo": "entrante" if direccion == "IN" else "saliente",
                        "numero_otra_parte": numero_otra_parte,
                        "descripcion_adicional": destino_limpio,
                        "tipo_servicio_factura": tipo_msg.strip(), "cantidad": 1, "costo_str": costo_str })
    print(f"INFO (parsear_detalles_uso): Finalizado. Detalles estructurados encontrados: {len(detalles_comunicaciones)}")
    return detalles_comunicaciones

def procesar_archivo_pdf(ruta_completa_archivo, nombre_archivo_original, fecha_mod_archivo_fs=None):
    item_comun = {
        'id_original': nombre_archivo_original, 'fecha_evento_inicio': None, 'fecha_evento_fin': None,
        'titulo_evento': nombre_archivo_original, 'descripcion_completa': None,
        'tipo_contenido': 'pdf_documento_factura', 'tags_generales': [], 
        'aplicacion_origen': 'Desconocido (PDF)', 'archivo_origen': nombre_archivo_original,
        'ruta_archivo_origen': ruta_completa_archivo, 'texto_extraido': None,
        'resumen_contenido': None, 'ids_internos_relevantes': {},
        'tags_especificos': {}, 'errores_procesamiento': None,
        'place_id': None, 'place_tag': None, 'device_id': None, 'device_tag': None,
        'user_id': None, 'user_tag': None, 'pdf_autor': None, 'pdf_asunto': None,
        'pdf_productor': None, 'pdf_creador_herramienta': None,
        'pdf_fecha_creacion': None, 'pdf_fecha_modificacion': None,
        'pdf_titular_cuenta': None, 'pdf_numero_cuenta': None,
        'datos_adicionales_json': {}, 'telefonos_encontrados_global': [],
        'palabras_clave_comunicacion_global': {},
        'duraciones_detectadas_texto_global': [], 'cantidades_detectadas_texto_global': [],
        'entidades_nombradas': [], 'detalles_llamadas_mensajes': []
    }
    pdf_metadata_leida_dict = None 
    try:
        with open(ruta_completa_archivo, 'rb') as f:
            reader = PdfReader(f)
            metadata = reader.metadata 
            if metadata:
                pdf_metadata_leida_dict = dict(metadata) 
                item_comun['datos_adicionales_json']['pdf_metadata_crudo'] = str(pdf_metadata_leida_dict)
            else:
                item_comun['datos_adicionales_json']['pdf_metadata_crudo'] = "No metadata found"

            texto_completo_pdf_list = [p.extract_text() or "" for p in reader.pages]
            item_comun['texto_extraido'] = "\n".join(texto_completo_pdf_list).strip()
            item_comun['descripcion_completa'] = item_comun['texto_extraido']
            
            match_titular = re.search(r"Hi\s+(\w+),", item_comun['texto_extraido'])
            if match_titular: item_comun['pdf_titular_cuenta'] = match_titular.group(1).title()
            else:
                match_titular_alt = re.search(r"Y ou are paying by AutoPay (KATERIN SAYROJASDEDEPAZ)", item_comun['texto_extraido'], re.IGNORECASE)
                if match_titular_alt: item_comun['pdf_titular_cuenta'] = match_titular_alt.group(1).title()
            
            match_cuenta = re.search(r"Account\s*:\s*(\d{9})", item_comun['texto_extraido'], re.IGNORECASE)
            if not match_cuenta and 'Account\n' in item_comun['texto_extraido']:
                 match_cuenta = re.search(r"Account\n(\d{9})", item_comun['texto_extraido'])
            if match_cuenta: item_comun['pdf_numero_cuenta'] = match_cuenta.group(1)

            if item_comun['texto_extraido']:
                item_comun['resumen_contenido'] = (item_comun['texto_extraido'][:500] + '...') if len(item_comun['texto_extraido']) > 500 else item_comun['texto_extraido']
                item_comun['telefonos_encontrados_global'] = extraer_telefonos_generico_del_texto(item_comun['texto_extraido'])
                item_comun['palabras_clave_comunicacion_global'] = buscar_palabras_clave_comunicacion(item_comun['texto_extraido'])
                item_comun['duraciones_detectadas_texto_global'] = extraer_duraciones_del_texto(item_comun['texto_extraido'])
                item_comun['cantidades_detectadas_texto_global'] = extraer_cantidades_mensajes_del_texto(item_comun['texto_extraido'])
                item_comun['detalles_llamadas_mensajes'] = parsear_detalles_uso_factura_tmobile(item_comun['texto_extraido'])

            if pdf_metadata_leida_dict:
                if pdf_metadata_leida_dict.get('/Title'): item_comun['titulo_evento'] = str(pdf_metadata_leida_dict.get('/Title'))
                if pdf_metadata_leida_dict.get('/Author'):
                    item_comun['pdf_autor'] = str(pdf_metadata_leida_dict.get('/Author')); item_comun['tags_generales'].append(f"autor:{str(pdf_metadata_leida_dict.get('/Author'))}")
                if pdf_metadata_leida_dict.get('/Subject'):
                    item_comun['pdf_asunto'] = str(pdf_metadata_leida_dict.get('/Subject')); item_comun['tags_generales'].append(f"asunto:{str(pdf_metadata_leida_dict.get('/Subject'))}")
                if pdf_metadata_leida_dict.get('/Creator'):
                    item_comun['pdf_creador_herramienta'] = str(pdf_metadata_leida_dict.get('/Creator')); item_comun['aplicacion_origen'] = str(pdf_metadata_leida_dict.get('/Creator'))
                if pdf_metadata_leida_dict.get('/Producer'): item_comun['pdf_productor'] = str(pdf_metadata_leida_dict.get('/Producer'))
                
                fecha_creacion_pdf_dt = parse_pdf_date(pdf_metadata_leida_dict.get('/CreationDate'))
                fecha_mod_pdf_dt = parse_pdf_date(pdf_metadata_leida_dict.get('/ModDate'))

                if fecha_creacion_pdf_dt: item_comun['pdf_fecha_creacion'] = fecha_creacion_pdf_dt.isoformat()
                if fecha_mod_pdf_dt: item_comun['pdf_fecha_modificacion'] = fecha_mod_pdf_dt.isoformat()
                
                # Asignación de fechas de evento
                if item_comun['titulo_evento'] == "T-Mobile" and item_comun['texto_extraido']: # Heurística para facturas T-Mobile
                    bill_issue_date_match = re.search(r"Bill issue date\s+((\w{3})\s+(\d{1,2}),\s*(\d{4}))", item_comun['texto_extraido'])
                    if bill_issue_date_match:
                        try:
                           parsed_bill_date = dateutil_parser.parse(bill_issue_date_match.group(1))
                           item_comun['fecha_evento_inicio'] = parsed_bill_date.replace(tzinfo=timezone.utc).isoformat()
                           due_date_match = re.search(r"due by\s+((\w{3})\s+(\d{1,2}),\s*(\d{4}))", item_comun['texto_extraido'])
                           if due_date_match:
                               parsed_due_date = dateutil_parser.parse(due_date_match.group(1))
                               item_comun['fecha_evento_fin'] = parsed_due_date.replace(tzinfo=timezone.utc).isoformat()
                        except Exception: 
                            if fecha_creacion_pdf_dt: item_comun['fecha_evento_inicio'] = fecha_creacion_pdf_dt.isoformat()
                elif fecha_creacion_pdf_dt:
                    item_comun['fecha_evento_inicio'] = fecha_creacion_pdf_dt.isoformat()
                    if fecha_mod_pdf_dt and fecha_mod_pdf_dt > fecha_creacion_pdf_dt:
                        item_comun['fecha_evento_fin'] = fecha_mod_pdf_dt.isoformat()
                elif fecha_mod_pdf_dt: item_comun['fecha_evento_inicio'] = fecha_mod_pdf_dt.isoformat()
                elif fecha_mod_archivo_fs: item_comun['fecha_evento_inicio'] = fecha_mod_archivo_fs.isoformat()
        
        if item_comun['titulo_evento'] == nombre_archivo_original and item_comun['texto_extraido']:
            primera_linea = item_comun['texto_extraido'].split('\n', 1)[0].strip()
            if primera_linea and len(primera_linea) < 150 and primera_linea not in item_comun['titulo_evento'] : 
                 item_comun['titulo_evento'] = primera_linea if not item_comun['titulo_evento'] or item_comun['titulo_evento']==nombre_archivo_original else item_comun['titulo_evento'] + " | " + primera_linea
                
    except FileNotFoundError: item_comun['errores_procesamiento'] = f"Archivo no encontrado: {ruta_completa_archivo}"
    except Exception as e:
        item_comun['errores_procesamiento'] = f"Error procesando PDF '{ruta_completa_archivo}': {e}"
        import traceback; traceback.print_exc()
    return [item_comun], pdf_metadata_leida_dict # Devolver también metadatos para if __name__

if __name__ == '__main__':
    print(f"--- Iniciando prueba de procesador_pdf.py ---")
    nombre_archivo_prueba = "9BillSummaryFb.pdf" 
    ruta_archivo_original_prueba = f"/storage/emulated/0/Download/TermuxApp/Archives/{nombre_archivo_prueba}"
    carpeta_reportes = "/storage/emulated/0/Download/TermuxApp/Reportes"
    if not os.path.exists(carpeta_reportes): os.makedirs(carpeta_reportes)
    ruta_archivo_salida_detalles = os.path.join(carpeta_reportes, f"detalles_procesados_pdf_{nombre_archivo_prueba}_v3.txt") # Nuevo nombre v3

    print(f"Probando con: {ruta_archivo_original_prueba}")
    fecha_mod_prueba_fs = None
    if os.path.exists(ruta_archivo_original_prueba):
        timestamp_mod = os.path.getmtime(ruta_archivo_original_prueba)
        fecha_mod_prueba_fs = datetime.fromtimestamp(timestamp_mod, timezone.utc)
        print(f"Fecha de modificación (filesystem): {fecha_mod_prueba_fs.isoformat() if fecha_mod_prueba_fs else 'N/A'}")
    else:
        print(f"ERROR: Archivo de prueba '{ruta_archivo_original_prueba}' NO encontrado."); exit()

    items_extraidos, metadata_leida_para_consola = procesar_archivo_pdf(ruta_archivo_original_prueba, nombre_archivo_prueba, fecha_mod_prueba_fs)
    
    if items_extraidos:
        item = items_extraidos[0] 
        print(f"\n--- Ítem PDF 1 (Resultado del Procesamiento Detallado) ---")
        print(f"  Título Evento: {item.get('titulo_evento')}")
        print(f"  Titular Cuenta: {item.get('pdf_titular_cuenta')}")
        print(f"  Número Cuenta: {item.get('pdf_numero_cuenta')}")
        print(f"  PDF Autor: {item.get('pdf_autor')}")
        print(f"  PDF Fecha Creación (metadato): {item.get('pdf_fecha_creacion')}")
        print(f"  Fecha Evento Inicio (calculada): {item.get('fecha_evento_inicio')}")
        
        detalles_com = item.get('detalles_llamadas_mensajes', [])
        print(f"  Total de Detalles de Llamadas/Mensajes Estructurados: {len(detalles_com)}") # Este es un print importante
        
        if detalles_com:
            print(f"\n  Mostrando los primeros 3 detalles estructurados (si los hay):") # Cambiado de 5 a 3
            for i, detalle in enumerate(detalles_com[:3]):
                print(f"    --- Detalle Comunicación {i+1} ---")
                print(f"      Línea: {detalle.get('usuario_linea')}, Tipo: {detalle.get('tipo_comunicacion')}, Dirección: {detalle.get('direccion_flujo')}")
                print(f"      Fecha/Hora: {detalle.get('fecha_hora_iso')}")
                print(f"      Otra Parte: {detalle.get('numero_otra_parte')}") # Ahora debería estar limpio
                print(f"      Descripción: {detalle.get('descripcion_adicional')}")
                if detalle.get('tipo_comunicacion') == 'llamada': print(f"      Duración (min): {detalle.get('duracion_minutos')}")
                else: print(f"      Cantidad: {detalle.get('cantidad')}")
        try:
            with open(ruta_archivo_salida_detalles, 'w', encoding='utf-8') as f_out:
                f_out.write("--- RESUMEN DEL ITEM PROCESADO ---\n")
                campos_a_guardar = ['id_original', 'titulo_evento', 'pdf_titular_cuenta', 'pdf_numero_cuenta', 
                                    'fecha_evento_inicio', 'pdf_autor', 'pdf_asunto', 
                                    'pdf_fecha_creacion', 'pdf_fecha_modificacion',
                                    'telefonos_encontrados_global', 'palabras_clave_comunicacion_global',
                                    'duraciones_detectadas_texto_global', 'cantidades_detectadas_texto_global']
                for campo in campos_a_guardar: f_out.write(f"{campo}: {item.get(campo)}\n")
                f_out.write(f"Total detalles estructurados: {len(detalles_com)}\n") # Añadido al archivo
                
                f_out.write("\n--- DETALLES DE LLAMADAS/MENSAJES ESTRUCTURADOS ---\n")
                if detalles_com:
                    for detalle in detalles_com: f_out.write(f"{json.dumps(detalle)}\n")
                else: f_out.write("No se encontraron detalles estructurados de llamadas/mensajes en esta ejecución.\n") # Mensaje corregido
                
                f_out.write(f"\n--- METADATOS CRUDOS DEL PDF (desde PyPDF2) ---\n")
                f_out.write(str(item.get('datos_adicionales_json', {}).get('pdf_metadata_crudo', 'No metadata object available')))
                f_out.write(f"\n\n--- TEXTO EXTRAIDO (primeros 2000 caracteres) ---\n{item.get('texto_extraido', '')[:2000]}...")
            print(f"\nRESUMEN Y DETALLES ESTRUCTURADOS (Y METADATOS CRUDOS) GUARDADOS EN:")
            print(f"  {ruta_archivo_salida_detalles}")
        except Exception as e_write: print(f"Error al guardar detalles: {e_write}")
        print(f"  Errores de procesamiento del PDF: {item.get('errores_procesamiento')}")
    else: print(f"No se extrajeron ítems de '{nombre_archivo_prueba}'.")
    
    if metadata_leida_para_consola: 
        print("\n--- Metadatos Crudos del PDF (Diagnóstico Consola) ---")
        print(metadata_leida_para_consola)
    else:
        print("\n--- Metadatos Crudos del PDF (Diagnóstico Consola): No disponibles o PyPDF2 no los leyó. ---")

    print(f"--- Fin de prueba de procesador_pdf.py ---")
