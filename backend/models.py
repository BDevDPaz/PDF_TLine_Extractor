import logging
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de base de datos
DATABASE_URL = "sqlite:///./app_data.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Line(Base):
    __tablename__ = "lines"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)

    # Relaciones
    call_events = relationship("CallEvent", back_populates="line")
    text_events = relationship("TextEvent", back_populates="line")
    data_events = relationship("DataEvent", back_populates="line")

class CallEvent(Base):
    __tablename__ = "call_events"

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, ForeignKey("lines.id"))
    timestamp = Column(DateTime)
    counterpart_number = Column(String)
    description = Column(Text)
    call_type = Column(String)
    duration_minutes = Column(Integer)
    ai_category = Column(String, default="Desconocido")

    # Relación
    line = relationship("Line", back_populates="call_events")

class TextEvent(Base):
    __tablename__ = "text_events"

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, ForeignKey("lines.id"))
    timestamp = Column(DateTime)
    counterpart_number = Column(String)
    destination = Column(String)
    message_type = Column(String)
    ai_category = Column(String, default="Desconocido")

    # Relación
    line = relationship("Line", back_populates="text_events")

class DataEvent(Base):
    __tablename__ = "data_events"

    id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, ForeignKey("lines.id"))
    date = Column(DateTime)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data_type = Column(String, default="Unknown")
    amount_mb = Column(Float, default=0.0)
    usage_mb = Column(Float, default=0.0)
    description = Column(Text, default="")
    ai_category = Column(String, default="Desconocido")

    # Relación
    line = relationship("Line", back_populates="data_events")

def init_db():
    """Inicializar la base de datos"""
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("💾 BASE DE DATOS: Inicializada correctamente")
    except Exception as e:
        logging.error(f"❌ Error inicializando BD: {e}")
        raise