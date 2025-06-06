import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

from app._system._core.base import BaseModel


class MenuTier(BaseModel):
    __depends_on__ = ['Menu']  # Add this line (self-reference for parent_uuid)
    __tablename__ = 'menu_tiers'

    name = Column(String(100), nullable=False)
    display = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)

    parent_uuid = Column(UUID(as_uuid=True),
        ForeignKey('menu_tiers.uuid', name='fk_menu_tiers_parent', ondelete='CASCADE'),
        nullable=True)
        
    menu_type_uuid = Column(UUID(as_uuid=True), 
        ForeignKey('menu.uuid', name='fk_menu_tiers_menu', ondelete='CASCADE'), 
        nullable=False)
                            
    icon = Column(String(100), nullable=True)
    position = Column(Integer, default=0, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)
    development = Column(Boolean, default=False, nullable=False)
    search_terms = Column(Text, nullable=True)

    menu_type = relationship("Menu", back_populates="tiers")
    links = relationship("MenuLink", foreign_keys="MenuLink.tier_uuid", back_populates="tier", cascade="all, delete-orphan")
    
    parent = relationship("MenuTier", 
                     remote_side="MenuTier.uuid", 
                     backref=backref("children", cascade="all, delete-orphan"))   
    
    # Create index for uniqueness
    __table_args__ = (
        Index('idx_menu_tiers_unique', 'slug', 'menu_type_uuid', 
            'parent_uuid', unique=True),
    )
