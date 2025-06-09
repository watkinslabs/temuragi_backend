from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref


from app.base.model import BaseModel

class Menu(BaseModel):

    __tablename__ = 'menu'

    name = Column(String(50), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    tiers = relationship("MenuTier", back_populates="menu_type", cascade="all, delete-orphan")

    @classmethod
    def create_initial_data(cls, session):
        """Create initial menus"""
        initial_types = [
            ('MAIN', 'Main Navigation', 'Top-level application navigation'),
            ('ADMIN', 'System', 'System Setup and integration'),
        ]

        for name, display, description in initial_types:
            existing = session.query(cls).filter_by(name=name).first()
            if not existing:
                menu_type = cls(name=name, display=display, description=description)
                session.add(menu_type)
