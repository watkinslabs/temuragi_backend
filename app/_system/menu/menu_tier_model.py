import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from flask import Flask, Blueprint, current_app, g
import inspect

from app._system._core.base import BaseModel


class MenuTier(BaseModel):
    __tablename__ = 'menu_tiers'

    name = Column(String(100), nullable=False)
    display = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    menu_type_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('menu_types.uuid'),
        nullable=False
    )
    parent_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('menu_tiers.uuid'),
        nullable=True
    )
    page_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('menu_links.uuid', use_alter=True, name='fk_menu_tiers_page'),
        nullable=True
    )
    icon = Column(String(100), nullable=True)
    position = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)
    development = Column(Boolean, default=False, nullable=False)
    search_terms = Column(Text, nullable=True)

    menu_type = relationship("MenuType", back_populates="tiers")
    page = relationship("MenuLink", foreign_keys=[page_uuid], backref="submenu_tiers")
    links = relationship("MenuLink", foreign_keys="MenuLink.tier_uuid", back_populates="tier")
    
    # Parent-child relationship fixed
    parent = relationship("MenuTier", remote_side="MenuTier.uuid", backref=backref("children", cascade="all, delete-orphan"))
     
    # Parent-child relationship
    parent = relationship("MenuTier", 
                         remote_side="MenuTier.uuid", 
                         backref=backref("children", cascade="all, delete-orphan"))
      # Create index for uniqueness
    __table_args__ = (
        Index('idx_menu_tiers_unique', slug, menu_type_uuid, 
              parent_uuid.nullsfirst(), page_uuid.nullsfirst(), unique=True),
    )


