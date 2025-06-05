import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class Role(BaseModel):
    __tablename__ = 'roles'

    name = Column(String(100), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship("RoleMenuPermission", back_populates="role", cascade="all, delete-orphan")

    @classmethod
    def create_initial_data(cls, session):
        """Create initial admin role"""
        existing = session.query(cls).filter_by(name='admin').first()
        if not existing:
            admin_role = cls(
                name='admin',
                display='Admin Role',
                description='Role for full application',
                is_admin=True
            )
            session.add(admin_role)
