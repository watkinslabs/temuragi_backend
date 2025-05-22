import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from flask import Flask, Blueprint, current_app, g
import inspect

from app._system._core.base import BaseModel

class MenuLink(BaseModel):
    __tablename__ = 'menu_links'

    name = Column(String(100), nullable=False)
    display = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    tier_uuid = Column(UUID(as_uuid=True), ForeignKey('menu_tiers.uuid', use_alter=True, name='fk_menu_links_tier'),nullable=True)

    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    position = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)
    development = Column(Boolean, default=False, nullable=False)
    new_tab = Column(Boolean, default=False, nullable=False)
    has_submenu = Column(Boolean, default=False, nullable=False)
    search_terms = Column(Text, nullable=True)
    blueprint_name = Column(String(100), nullable=True)  # Store the blueprint name for tracking
    endpoint = Column(String(255), nullable=True)  # Store the endpoint for tracking

    tier = relationship("MenuTier", foreign_keys=[tier_uuid], back_populates="links")
    role_permissions = relationship("RoleMenuPermission", back_populates="link")
    user_quick_links = relationship("UserQuickLink", back_populates="link")

