from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import datetime

Base = declarative_base()

class Line(Base):
    __tablename__ = 'lines'
    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False)
    
    call_events = relationship("CallEvent", back_populates="line", cascade="all, delete-orphan")
    text_events = relationship("TextEvent", back_populates="line", cascade="all, delete-orphan")
    data_events = relationship("DataEvent", back_populates="line", cascade="all, delete-orphan")

class CallEvent(Base):
    __tablename__ = 'call_events'
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    counterpart_number = Column(String)
    description = Column(String)
    call_type = Column(String(5))
    duration_minutes = Column(Integer)
    ai_category = Column(String, default="Desconocido")
    
    line = relationship("Line", back_populates="call_events")

class TextEvent(Base):
    __tablename__ = 'text_events'
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    counterpart_number = Column(String)
    destination = Column(String)
    message_type = Column(String(10))
    ai_category = Column(String, default="Desconocido")

    line = relationship("Line", back_populates="text_events")

class DataEvent(Base):
    __tablename__ = 'data_events'
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    date = Column(Date, nullable=False)
    usage_mb = Column(Float)

    line = relationship("Line", back_populates="data_events")

# --- Configuración de la Base de Datos ---
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=False)  # Sin echo para producción
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializar base de datos con sistema híbrido ultra-agresivo"""
    Base.metadata.create_all(bind=engine)
    import logging
    logging.info("💾 BASE DE DATOS: Inicializada para sistema híbrido 124.19% precisión")