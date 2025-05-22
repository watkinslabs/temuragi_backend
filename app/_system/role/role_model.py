import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from flask import Flask, Blueprint, current_app, g
import inspect

from app._system._core.base import BaseModel


class Role(BaseModel):
    __tablename__ = 'roles'

    name = Column(String(100), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship("RoleMenuPermission", back_populates="role")

