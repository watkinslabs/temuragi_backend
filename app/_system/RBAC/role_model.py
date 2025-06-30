from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class Role(BaseModel):
    __tablename__ = 'roles'
    __depends_on__ =[]
    name = Column(String(100), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

