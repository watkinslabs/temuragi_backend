from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from app.base.model import BaseModel

class DataType(BaseModel):
    __tablename__ = 'data_types'
    __depends_on__ = []  


    name = Column(String, unique=True, nullable=False)
    display = Column(String, nullable=False)



    @classmethod
    def create_initial_data(cls, session):
        """Create initial data types"""
        initial_types = [
            ('string', 'String', True),
            ('number', 'Number', True),
            ('integer', 'Integer', True),
            ('boolean', 'Boolean', True),
            ('date', 'Date', True),
            ('datetime', 'DateTime', True),
            ('time', 'Time', True),
            ('json', 'JSON', True),
            ('array', 'Array', True),
            ('money', 'Money', True),
            # New types specifically useful for reports
            ('decimal', 'Decimal', True),
            ('percentage', 'Percentage', True),
            ('email', 'Email', True),
            ('url', 'URL', True),
            ('id', 'UUID', True),
            ('ip_address', 'IP Address', True),
            ('color', 'Color', True),
            ('file', 'File', True),
            ('image', 'Image', True),
            ('markdown', 'Markdown', True),
            ('html', 'HTML', True),
            ('code', 'Code', True)
        ]
        
        for name, display, active in initial_types:
            existing = session.query(cls).filter_by(name=name).first()
            if not existing:
                data_type = cls(name=name, display=display, is_active=active)
                session.add(data_type)
