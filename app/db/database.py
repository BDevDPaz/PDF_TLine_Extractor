from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database setup
DATABASE_URL = "sqlite:///data/timeline_data.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize the database and create all tables"""
    from app.db.models import Call, Message, DataUsage
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Get a database session"""
    return SessionLocal()
