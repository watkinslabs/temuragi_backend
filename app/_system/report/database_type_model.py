from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.base.model import BaseModel


class DatabaseType(BaseModel):
    __tablename__ = 'database_types'
    __depends_on__=[]
    
    name = Column(
        Text,
        unique=True,
        nullable=False
    )
    display = Column(
        Text,
        nullable=False
    )

    @classmethod
    def create_initial_data(cls, session):
        """Create initial database types"""
        initial_types = [
            ('postgres', 'PostgreSQL', True),
            ('mysql', 'MySQL', True),
            ('mssql', 'MSSQL', True),
            ('oracle', 'Oracle', True),
            ('sqlite', 'SQLite', True),
            ('mongodb', 'mongodb', True)
        ]
        
        for name, display, active in initial_types:
            existing = session.query(cls).filter_by(name=name).first()
            if not existing:
                db_type = cls(name=name, display=display, is_active=active)
                session.add(db_type)
        
        
    def __repr__(self):
        return f"<DatabaseType(name='{self.name}', display='{self.display}')>"