from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.database import Base

class ExtractedData(Base):
    __tablename__ = "extracted_data"
    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String, index=True)
    phone_line = Column(String, index=True)
    event_type = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    direction = Column(String)
    contact = Column(String)
    description = Column(String)
    value = Column(String)
