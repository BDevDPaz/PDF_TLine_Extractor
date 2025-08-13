import json
import os
from datetime import datetime, timezone, timedelta
from dateutil import parser # Para parseo de fechas avanzado

# --- Inicio: Helper para parsear fechas en español ---
def parsear_fecha_es(fecha_str_es):
    meses_es = {
        'enero': 'January', 'febrero': 'February', 'marzo': 'March',
        'abril': 'April', 'mayo': 'May', 'junio': 'June',
        'julio': 'July', 'agosto': 'August', 'septiembre': 'September',
        'octubre': 'October', 'noviembre': 'November', 'diciembre': 'December'
    }
    try:
        fecha_str_en = fecha_str_es.lower()
        for es, en in meses_es.items():
            fecha_str_en = fecha_str_en.replace(f" de {es} de ", f" {en} ")
            fecha_str_en = fecha_str_en.replace(f" {es} ", f" {en} ")
        
        parts = fecha_str_en.split()
        if len(parts) > 3 and parts[1] in meses_es.values() and parts[2] == "de":
            fecha_str_en = parts[0] + " " + parts[1] + " " + parts[3] + " " + " ".join(parts[4:])
        elif len(parts) > 3 and parts[2] in meses_es.values() and parts[1] == "de":
             fecha_str_en = parts[0] + " " + parts[2] + " " + parts[3] + " " + " ".join(parts[4:])

        dt_obj = parser.parse(fecha_str_en)
        return dt_obj
    except Exception:
        try:
            dt_obj = parser.parse(fecha_str_es)
            return dt_obj
        except Exception as e2:
            print(f"Advertencia (parsear_fecha_es): Falló parseo de '{fecha_str_es}'. Error: {e2}")
            return None
# --- Fin: Helper para parsear fechas en español ---

def _parse_google_timestamp(ts_str_or_int):
    if ts_str_or_int is None: return None
    try:
        if isinstance(ts_str_or_int, (int, float)):
            return datetime.fromtimestamp(ts_str_or_int / 1000, timezone.utc)
        return datetime.fromisoformat(ts_str_or_int.replace('Z', '+00:00'))
    except Exception as e:
        print(f"Advertencia (_parse_google_timestamp): Falló parseo de '{ts_str_or_int}'. Error: {e}")
        return None

# --- Función para procesar un item JSON individual ---
def _procesar_item_json_individual(item_data, nombre_archivo_base, fecha_modificacion_archivo):
    item_comun = {
        'id_original': nombre_archivo_base, 'fecha_evento_inicio': None, 'fecha_evento_fin': None,
        'titulo_evento': None,
        'descripcion_completa': json.dumps(item_data, indent=2, ensure_ascii=False),
        'tipo_contenido': 'json_item_desconocido',
        'tags_generales': [], 'aplicacion_origen': 'Desconocido (JSON)',
        'archivo_origen': nombre_archivo_base.split('_item_')[0] if '_item_' in nombre_archivo_base else nombre_archivo_base,
        'ruta_archivo_origen': f"/storage/emulated/0/Download/TermuxApp/Archives/Reales/Historial de ubicaciones (Rutas) (6)/Semantic Location History/2022/{nombre_archivo_base.split('_item_')[0] if '_item_' in nombre_archivo_base else nombre_archivo_base}",
        'texto_extraido': json.dumps(item_data, ensure_ascii=False),
        'resumen_contenido': None, 'ids_internos_relevantes': {}, 'tags_especificos': {},
        'errores_procesamiento': None,
        # Campos Fase 4
        'place_id': None, 'place_tag': None, 'device_id': None, 'device_tag': None,
        'user_id': None, 'user_tag': None,
        # Nuevos campos recomendados
        'latitud': None, 'longitud': None,
        'location_confidence': None, 'visit_confidence': None,
        'activity_confidence': None, 'activity_distance_meters': None,
        'source_device_tag': None, # Unificado para deviceTag de location o activity
        'datos_adicionales_json': item_data
    }

    if 'placeVisit' in item_data:
        pv = item_data['placeVisit']
        item_comun['tipo_contenido'] = 'json_place_visit'
        item_comun['tags_generales'].append('visita_lugar')
        item_comun['aplicacion_origen'] = 'Google Location History (PlaceVisit)'
        
        loc = pv.get('location', {})
        item_comun['place_id'] = loc.get('placeId')
        
        # Lógica mejorada para titulo_evento
        nombre_lugar = loc.get('name')
        direccion_lugar = loc.get('address')
        if nombre_lugar and nombre_lugar.lower() != 'lugar desconocido' and nombre_lugar.lower() != 'unknown location':
            item_comun['titulo_evento'] = nombre_lugar
        elif direccion_lugar:
            item_comun['titulo_evento'] = direccion_lugar
        else:
            item_comun['titulo_evento'] = 'Lugar desconocido'
            
        item_comun['place_tag'] = nombre_lugar or direccion_lugar # place_tag puede tener nombre o dirección
        
        if loc.get('semanticType') and isinstance(loc.get('semanticType'), str):
            item_comun['tags_generales'].append(loc.get('semanticType').upper()) # Ej. TYPE_HOME -> TYPE_HOME

        if 'latitudeE7' in loc and 'longitudeE7' in loc:
            item_comun['latitud'] = loc['latitudeE7'] / 1e7
            item_comun['longitud'] = loc['longitudeE7'] / 1e7
        
        duration = pv.get('duration', {})
        item_comun['fecha_evento_inicio'] = _parse_google_timestamp(duration.get('startTimestampMs') or duration.get('startTimestamp'))
        item_comun['fecha_evento_fin'] = _parse_google_timestamp(duration.get('endTimestampMs') or duration.get('endTimestamp'))
        
        item_comun['ids_internos_relevantes']['placeId'] = item_comun['place_id']
        item_comun['resumen_contenido'] = f"Visita a: {item_comun['titulo_evento']}"
        if item_comun['fecha_evento_inicio'] and isinstance(item_comun['fecha_evento_inicio'], datetime):
            item_comun['resumen_contenido'] += f" el {item_comun['fecha_evento_inicio'].strftime('%Y-%m-%d')}"

        # Campos recomendados
        item_comun['location_confidence'] = loc.get('locationConfidence')
        item_comun['visit_confidence'] = pv.get('visitConfidence')
        if loc.get('sourceInfo') and loc['sourceInfo'].get('deviceTag'):
            item_comun['source_device_tag'] = loc['sourceInfo']['deviceTag']

    elif 'activitySegment' in item_data:
        act = item_data['activitySegment']
        item_comun['tipo_contenido'] = 'json_activity_segment'
        item_comun['tags_generales'].append('segmento_actividad')
        item_comun['aplicacion_origen'] = 'Google Location History (ActivitySegment)'
        
        activity_type = act.get('activityType', 'ACTIVIDAD_DESCONOCIDA')
        item_comun['tags_generales'].append(activity_type)
        item_comun['titulo_evento'] = f"Actividad: {activity_type.replace('_', ' ').title()}"

        duration = act.get('duration', {})
        item_comun['fecha_evento_inicio'] = _parse_google_timestamp(duration.get('startTimestampMs') or duration.get('startTimestamp'))
        item_comun['fecha_evento_fin'] = _parse_google_timestamp(duration.get('endTimestampMs') or duration.get('endTimestamp'))

        start_loc = act.get('startLocation', {})
        if 'latitudeE7' in start_loc and 'longitudeE7' in start_loc:
            item_comun['latitud'] = start_loc['latitudeE7'] / 1e7
            item_comun['longitud'] = start_loc['longitudeE7'] / 1e7
        
        item_comun['resumen_contenido'] = f"Segmento de actividad: {activity_type}"
        if item_comun['fecha_evento_inicio'] and isinstance(item_comun['fecha_evento_inicio'], datetime):
             item_comun['resumen_contenido'] += f" el {item_comun['fecha_evento_inicio'].strftime('%Y-%m-%d')}"
        
        # Campos recomendados
        item_comun['activity_confidence'] = act.get('confidence')
        item_comun['activity_distance_meters'] = act.get('distance')
        if act.get('sourceInfo') and act['sourceInfo'].get('deviceTag'):
            item_comun['source_device_tag'] = act['sourceInfo']['deviceTag']


    else: # Lógica para prueba.json u otros JSON genéricos
        item_comun['tipo_contenido'] = 'json_generic_item'
        item_comun['aplicacion_origen'] = item_data.get('nombre_del_programa', 'JSON Genérico')
        item_comun['titulo_evento'] = item_data.get('nombre_del_programa', 'Item JSON Genérico')
        
        if 'uid' in item_data:
            item_comun['id_original'] = item_data.get('uid')
        else: # Asegurar que id_original no sea solo el nombre del archivo base para genéricos
             item_comun['id_original'] = f"{nombre_archivo_base}_generic_{sum(1 for char in json.dumps(item_data) if char.isalnum()) % 10000}"


        if 'published_at' in item_data:
            fecha_evento_dt = parsear_fecha_es(item_data.get('published_at'))
            if fecha_evento_dt: item_comun['fecha_evento_inicio'] = fecha_evento_dt
        
        if 'caracteristicas_planeadas' in item_data and isinstance(item_data['caracteristicas_planeadas'], list):
            item_comun['tags_generales'].extend(item_data['caracteristicas_planeadas'])
        item_comun['resumen_contenido'] = item_comun['titulo_evento']

    # Convertir fechas a ISO string para el item_comun final
    if isinstance(item_comun['fecha_evento_inicio'], datetime):
        item_comun['fecha_evento_inicio'] = item_comun['fecha_evento_inicio'].isoformat()
    if isinstance(item_comun['fecha_evento_fin'], datetime):
        item_comun['fecha_evento_fin'] = item_comun['fecha_evento_fin'].isoformat()

    if not item_comun['resumen_contenido']:
         item_comun['resumen_contenido'] = json.dumps(item_data, ensure_ascii=False)[:250] + "..."
    if not item_comun['id_original']: # Fallback final para id_original
        item_comun['id_original'] = nombre_archivo_base

    return item_comun
# --- Fin: Función para procesar un item JSON individual ---

def procesar_archivo_json(ruta_completa_archivo, nombre_archivo_original, fecha_mod_archivo=None):
    items_procesados_final = []
    if fecha_mod_archivo is None and os.path.exists(ruta_completa_archivo):
        try:
            timestamp_mod = os.path.getmtime(ruta_completa_archivo)
            fecha_mod_archivo = datetime.fromtimestamp(timestamp_mod, timezone.utc)
        except Exception as e:
            print(f"Advertencia ({nombre_archivo_original}): No se pudo obtener fecha mod: {e}")
    try:
        with open(ruta_completa_archivo, 'r', encoding='utf-8') as f:
            contenido_json_crudo = json.load(f)
        items_a_procesar_individualmente = []
        if isinstance(contenido_json_crudo, list):
            for item_en_lista in contenido_json_crudo:
                if isinstance(item_en_lista, dict): items_a_procesar_individualmente.append(item_en_lista)
                else: print(f"Adv ({nombre_archivo_original}): Elemento no-dict en lista JSON. Tipo: {type(item_en_lista)}")
        elif isinstance(contenido_json_crudo, dict):
            if "timelineObjects" in contenido_json_crudo and isinstance(contenido_json_crudo["timelineObjects"], list):
                for i, item_en_timeline in enumerate(contenido_json_crudo["timelineObjects"]):
                    if isinstance(item_en_timeline, dict): items_a_procesar_individualmente.append(item_en_timeline)
                    else: print(f"Adv ({nombre_archivo_original}): Elemento no-dict en 'timelineObjects'. Tipo: {type(item_en_timeline)}")
            else: items_a_procesar_individualmente.append(contenido_json_crudo)
        else:
            print(f"Error ({nombre_archivo_original}): Contenido no es lista ni dict JSON válido.")
            return []

        for i, item_data_individual in enumerate(items_a_procesar_individualmente):
            nombre_base_item = f"{nombre_archivo_original}_item_{i+1}" if len(items_a_procesar_individualmente) > 1 else nombre_archivo_original
            item_transformado = _procesar_item_json_individual(item_data_individual, nombre_base_item, fecha_mod_archivo)
            if item_transformado: items_procesados_final.append(item_transformado)
    except FileNotFoundError: print(f"Error ({nombre_archivo_original}): Archivo no encontrado '{ruta_completa_archivo}'")
    except json.JSONDecodeError: print(f"Error ({nombre_archivo_original}): No se pudo decodificar JSON.")
    except Exception as e:
        print(f"Error ({nombre_archivo_original}): Error inesperado: {e}")
        import traceback; traceback.print_exc()
    return items_procesados_final

if __name__ == '__main__':
    print(f"--- Iniciando prueba de procesador_json.py ---")
    nombre_archivo_prueba = "2022_DECEMBER.json"
    ruta_archivo_prueba = "/storage/emulated/0/Download/TermuxApp/Archives/Reales/Historial de ubicaciones (Rutas) (6)/Semantic Location History/2022/2022_DECEMBER.json"
    print(f"Probando con: {ruta_archivo_prueba}")
    fecha_mod_prueba = None
    if os.path.exists(ruta_archivo_prueba):
        timestamp_mod = os.path.getmtime(ruta_archivo_prueba)
        fecha_mod_prueba = datetime.fromtimestamp(timestamp_mod, timezone.utc)
        print(f"Fecha de modificación del archivo de prueba: {fecha_mod_prueba.isoformat() if fecha_mod_prueba else 'No disponible'}")
    else:
        print(f"ERROR CRÍTICO: El archivo de prueba '{ruta_archivo_prueba}' NO fue encontrado. Verifica la ruta.")
        exit()

    items_extraidos = procesar_archivo_json(ruta_archivo_prueba, nombre_archivo_prueba, fecha_mod_prueba)
    
    if items_extraidos:
        print(f"\nSe extrajeron {len(items_extraidos)} ítems de '{nombre_archivo_prueba}'.")
        print(f"Mostrando los primeros 3 ítems (si los hay):\n")
        for i, item in enumerate(items_extraidos[:3]): # Imprime solo los primeros 3 para brevedad
            print(f"--- Ítem {i+1} ({item.get('tipo_contenido')}) ---")
            print(f"  ID Original: {item.get('id_original')}")
            print(f"  Título Evento: {item.get('titulo_evento')}")
            print(f"  Fecha Inicio: {item.get('fecha_evento_inicio')}")
            print(f"  Fecha Fin: {item.get('fecha_evento_fin')}")
            print(f"  Place ID: {item.get('place_id')}")
            print(f"  Place Tag: {item.get('place_tag')}")
            print(f"  Latitud: {item.get('latitud')}, Longitud: {item.get('longitud')}")
            print(f"  Location Confidence: {item.get('location_confidence')}") # Nuevo
            print(f"  Visit Confidence: {item.get('visit_confidence')}") # Nuevo
            print(f"  Activity Confidence: {item.get('activity_confidence')}") # Nuevo
            print(f"  Activity Distance (m): {item.get('activity_distance_meters')}") # Nuevo
            print(f"  Source Device Tag: {item.get('source_device_tag')}") # Nuevo
            print(f"  Tags Generales: {item.get('tags_generales')}")
            print(f"  Resumen: {item.get('resumen_contenido')}")
            # Para ver todo el item procesado:
            # print(json.dumps(item, indent=2, ensure_ascii=False))
    else:
        print(f"No se extrajeron ítems o hubo un error procesando '{nombre_archivo_prueba}'.")
    print(f"--- Fin de prueba de procesador_json.py ---")
