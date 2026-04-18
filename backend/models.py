from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://seth:your_password@localhost:5432/integrateai")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    source_type = Column(String)
    source_config = Column(JSON)
    target_type = Column(String)
    target_config = Column(JSON)
    field_mapping = Column(JSON)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    integration_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Float)
    rows_read = Column(Integer)
    rows_written = Column(Integer)
    api_calls = Column(Integer)
    status = Column(String)

class SyncHash(Base):
    __tablename__ = "sync_hashes"
    
    integration_id = Column(String, primary_key=True)
    last_hash = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()