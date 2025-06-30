from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref


from app.base.model import BaseModel
from app.register.database import get_engine_for_bind_key

db_session=get_engine_for_bind_key()

class Menu(BaseModel):

    __tablename__ = 'menu'
    __depends_on__ = []

    name = Column(String(50), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(Text, nullable=True)

    tiers = relationship("MenuTier", back_populates="menu", cascade="all, delete-orphan")

