import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from app._system._core.base import BaseModel

class DataType(BaseModel):
    __tablename__ = 'data_types'

    name = Column(String, unique=True, nullable=False)
    display = Column(String, nullable=False)

    