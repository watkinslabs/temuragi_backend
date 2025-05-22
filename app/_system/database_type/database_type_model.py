import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app._system._core.base import BaseModel


class DatabaseType(BaseModel):
    __tablename__ = 'database_types'

    name = Column(
        Text,
        unique=True,
        nullable=False
    )
    display = Column(
        Text,
        nullable=False
    )

    def __repr__(self):
        return f"<DatabaseType(name='{self.name}', display='{self.display}')>"