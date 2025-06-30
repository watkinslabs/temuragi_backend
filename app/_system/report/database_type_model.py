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

