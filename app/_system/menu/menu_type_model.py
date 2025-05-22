import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from flask import Flask, Blueprint, current_app, g
import inspect

from app._system._core.base import BaseModel

class MenuType(BaseModel):
    __tablename__ = 'menu_types'

    name = Column(String(50), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    tiers = relationship("MenuTier", back_populates="menu_type")

