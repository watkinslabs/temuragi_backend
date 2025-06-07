import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class Template(BaseModel):  # FIXED: Changed from PageTemplate
    """
    Template model for defining reusable page structures and layouts.

    Columns:
    - name: Unique identifier for the template (kebab-case)
    - display_name: Human-readable template name
    - description: Description of template purpose and usage
    - template_file: Path to Jinja2 template file relative to templates directory
    - theme_uuid: Foreign key to themes table
    - menu_type_uuid: Foreign key to menu table (which menu to display)
    - layout_type: Layout style (full-width, sidebar-left, sidebar-right, centered)
    - container_class: CSS class for main container
    - sidebar_enabled: Whether template includes sidebar navigation
    - header_type: Header style (fixed, static, minimal, none)
    - footer_type: Footer style (fixed, static, minimal, none)
    - breadcrumbs_enabled: Whether to show breadcrumb navigation
    - is_admin_template: Whether this template requires admin access
    - is_default_template: Whether this is the default template for new pages
    """
    __depends_on__ = ['Theme', 'Menu']  # Depends on Theme and Menu
    __tablename__ = 'templates'

    name = Column(String(50), unique=True, nullable=False,
                 comment="Unique template identifier (kebab-case)")
    display_name = Column(String(100), nullable=False,
                         comment="Human-readable template name")
    description = Column(Text, nullable=True,
                        comment="Description of template purpose and usage")
    template_file = Column(String(255), nullable=False,
                          comment="Path to Jinja2 template file")
    theme_uuid = Column(UUID(as_uuid=True),
                       ForeignKey('themes.uuid', name='fk_templates_theme'),  # FIXED: Updated name
                       nullable=True,
                       comment="Foreign key to themes table")
    menu_type_uuid = Column(UUID(as_uuid=True),
                           ForeignKey('menu.uuid', name='fk_templates_menu'),  # FIXED: Updated name
                           nullable=True,
                           comment="Foreign key to menu table")
    layout_type = Column(String(50), nullable=False, default='full-width',
                        comment="Layout style (full-width, sidebar-left, sidebar-right, centered)")
    container_class = Column(String(100), nullable=False, default='container-fluid',
                            comment="CSS class for main container")
    sidebar_enabled = Column(Boolean, default=False, nullable=False,
                            comment="Whether template includes sidebar navigation")
    header_type = Column(String(50), nullable=False, default='static',
                        comment="Header style (fixed, static, minimal, none)")
    footer_type = Column(String(50), nullable=False, default='static',
                        comment="Footer style (fixed, static, minimal, none)")
    breadcrumbs_enabled = Column(Boolean, default=True, nullable=False,
                                comment="Whether to show breadcrumb navigation")
    is_admin_template = Column(Boolean, default=False, nullable=False,
                              comment="Whether template requires admin access")
    is_default_template = Column(Boolean, default=False, nullable=False,
                                comment="Whether this is default template for new pages")

    # Relationships - FIXED: Updated relationship names
    theme = relationship("Theme", back_populates="templates")  # UPDATED
    menu_type = relationship("Menu", foreign_keys=[menu_type_uuid])
    pages = relationship("Page", back_populates="template")  # UPDATED
    template_fragments = relationship("TemplateFragments", back_populates="template", cascade="all, delete-orphan")  # UPDATED

    # Indexes - FIXED: Updated all index names
    __table_args__ = (
        Index('idx_templates_name', 'name'),  # UPDATED
        Index('idx_templates_theme', 'theme_uuid'),  # UPDATED
        Index('idx_templates_menu', 'menu_type_uuid'),  # UPDATED
        Index('idx_templates_admin', 'is_admin_template'),  # UPDATED
        Index('idx_templates_default', 'is_default_template'),  # UPDATED
        Index('idx_templates_layout', 'layout_type'),  # UPDATED
        UniqueConstraint('name', name='uq_templates_name'),  # UPDATED
    )

    def validate_slug(self):
        """Validate slug format"""
        import re
        if not re.match(r'^[a-z0-9-]+$', self.name):  # FIXED: Changed from self.slug to self.name
            raise ValueError("Name must contain only lowercase letters, numbers, and hyphens")
