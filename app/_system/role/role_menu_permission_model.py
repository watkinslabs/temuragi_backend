import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from flask import Flask, Blueprint, current_app, g
import inspect

from app._system._core.base import BaseModel

class RoleMenuPermission(BaseModel):
    __tablename__ = 'role_menu_permissions'

    role_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('roles.uuid'),
        nullable=False
    )
    menu_link_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('menu_links.uuid'),
        nullable=False
    )

    role = relationship("Role", back_populates="permissions")
    link = relationship("MenuLink", back_populates="role_permissions")

    __table_args__ = (
        UniqueConstraint('role_uuid', 'menu_link_uuid', name='uq_role_link'),
    )




