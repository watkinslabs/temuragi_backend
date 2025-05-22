import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from flask import Flask, Blueprint, current_app, g
import inspect

from app._system._core.base import BaseModel

class UserQuickLink(BaseModel):
    __tablename__ = 'user_quick_links'

    user_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('users.uuid'),
        nullable=False
    )
    menu_link_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('menu_links.uuid'),
        nullable=False
    )
    position = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="quick_links")
    link = relationship("MenuLink", back_populates="user_quick_links")

    __table_args__ = (
        UniqueConstraint('user_uuid', 'menu_link_uuid', name='uq_user_link'),
    )


