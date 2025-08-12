from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.database import Base

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    call_type = Column(String(20), nullable=False)  # "Recibida" or "Realizada"
    phone_number = Column(String(50), nullable=False)
    description = Column(String(200))
    duration_minutes = Column(Integer, nullable=False)
    source_file = Column(String(100), nullable=False)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    message_type = Column(String(20), nullable=False)  # "Recibido" or "Enviado"
    contact = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    format = Column(String(10), nullable=False)  # "TXT" or "PIC"
    source_file = Column(String(100), nullable=False)

class DataUsage(Base):
    __tablename__ = "data_usage"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    data_type = Column(String(50), nullable=False)
    mb_used = Column(Float, nullable=False)
    source_file = Column(String(100), nullable=False)
