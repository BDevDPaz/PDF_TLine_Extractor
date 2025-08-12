from sqlalchemy import Column, Integer, String, DateTime, Float, Date
from app.db.database import Base

class ExtractedData(Base):
    __tablename__ = "extracted_data"
    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String, index=True)
    event_type = Column(String, index=True) # 'Llamada', 'Mensaje', 'Datos'
    timestamp = Column(DateTime, index=True)
    detail_1 = Column(String) # Ej: Número de teléfono, Contacto
    detail_2 = Column(String) # Ej: Duración, Formato
    detail_3 = Column(String) # Ej: Tipo (IN/OUT), Descripción
    numeric_value = Column(Float) # Ej: MB usados, minutos
