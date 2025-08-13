"""
Sistema de filtros avanzados y visualizaciones
Enfocado en análisis discreto y privacidad de datos
"""
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, extract
from app.db.database import SessionLocal
from app.db.models import ExtractedData

class AdvancedDataFilter:
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def filter_by_timeframe(self, start_date=None, end_date=None, timeframe='all'):
        """Filtrado temporal avanzado"""
        query = self.db.query(ExtractedData)
        
        if timeframe != 'all':
            now = datetime.now()
            if timeframe == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == 'week':
                start_date = now - timedelta(days=7)
            elif timeframe == 'month':
                start_date = now - timedelta(days=30)
            elif timeframe == 'quarter':
                start_date = now - timedelta(days=90)
        
        if start_date:
            query = query.filter(ExtractedData.timestamp >= start_date)
        if end_date:
            query = query.filter(ExtractedData.timestamp <= end_date)
            
        return query
    
    def filter_by_contact_patterns(self, pattern_type='frequent'):
        """Filtrado por patrones de contacto"""
        if pattern_type == 'frequent':
            # Contactos con más de 5 interacciones
            subquery = self.db.query(
                ExtractedData.contact,
                func.count(ExtractedData.id).label('count')
            ).group_by(ExtractedData.contact).having(func.count(ExtractedData.id) > 5).subquery()
            
            return self.db.query(ExtractedData).join(
                subquery, ExtractedData.contact == subquery.c.contact
            )
        elif pattern_type == 'recent':
            # Contactos de los últimos 7 días
            week_ago = datetime.now() - timedelta(days=7)
            return self.db.query(ExtractedData).filter(ExtractedData.timestamp >= week_ago)
    
    def get_usage_analytics(self, group_by='hour'):
        """Análisis de patrones de uso"""
        if group_by == 'hour':
            result = self.db.query(
                extract('hour', ExtractedData.timestamp).label('hour'),
                func.count(ExtractedData.id).label('count')
            ).group_by(extract('hour', ExtractedData.timestamp)).all()
        elif group_by == 'day_of_week':
            result = self.db.query(
                extract('dow', ExtractedData.timestamp).label('day'),
                func.count(ExtractedData.id).label('count')
            ).group_by(extract('dow', ExtractedData.timestamp)).all()
        else:
            result = []
        
        return [{'label': r[0], 'value': r[1]} for r in result]
    
    def get_communication_summary(self):
        """Resumen de comunicaciones sin exponer números específicos"""
        summary = self.db.query(
            ExtractedData.event_type,
            ExtractedData.direction,
            func.count(ExtractedData.id).label('count')
        ).group_by(ExtractedData.event_type, ExtractedData.direction).all()
        
        result = {}
        for event_type, direction, count in summary:
            if event_type not in result:
                result[event_type] = {}
            result[event_type][direction] = count
            
        return result
    
    def get_filtered_data(self, filters=None):
        """Obtiene datos filtrados de forma segura"""
        query = self.db.query(ExtractedData)
        
        if filters:
            if 'event_type' in filters:
                query = query.filter(ExtractedData.event_type.in_(filters['event_type']))
            if 'direction' in filters:
                query = query.filter(ExtractedData.direction.in_(filters['direction']))
            if 'phone_line' in filters:
                query = query.filter(ExtractedData.phone_line.in_(filters['phone_line']))
            if 'date_from' in filters:
                query = query.filter(ExtractedData.timestamp >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(ExtractedData.timestamp <= filters['date_to'])
        
        return query.all()

class PrivateCSVExporter:
    @staticmethod
    def generate_secure_csv(data, anonymize_contacts=True):
        """Genera CSV con opciones de anonimización"""
        import pandas as pd
        import io
        
        # Convertir a DataFrame
        records = []
        for item in data:
            record = {
                'id': item.id,
                'archivo_origen': item.source_file,
                'linea_telefonica': item.phone_line,
                'tipo_evento': item.event_type,
                'fecha_hora': item.timestamp.strftime('%Y-%m-%d %H:%M:%S') if item.timestamp else '',
                'direccion': item.direction,
                'contacto': item.contact if not anonymize_contacts else f"Contact_{hash(item.contact) % 1000:03d}" if item.contact else '',
                'descripcion': item.description,
                'valor': item.value
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Generar CSV en memoria
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue()