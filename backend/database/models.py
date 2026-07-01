from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class MigrationJob(Base):
    __tablename__ = "migration_jobs"
    
    id = Column(String, primary_key=True)
    project_name = Column(String)
    apl_source = Column(Text)
    python_target = Column(Text)
    status = Column(String)
    overall_score = Column(Float)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
