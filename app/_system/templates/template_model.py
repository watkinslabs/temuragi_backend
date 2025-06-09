from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class Template(BaseModel):
    """
    Template model for defining reusable page structures and layouts.

    Columns:
    - name: Unique identifier for the template (kebab-case)
    - display_name: Human-readable template name
    - description: Description of template purpose and usage
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
    __depends_on__ = ['Theme', 'Menu','Module']
    __tablename__ = 'templates'

    name = Column(String(50), unique=True, nullable=False,
                 comment="Unique template identifier (kebab-case)")
    display_name = Column(String(100), nullable=False,
                         comment="Human-readable template name")
    description = Column(Text, nullable=True,
                        comment="Description of template purpose and usage")
    theme_uuid = Column(UUID(as_uuid=True),
                       ForeignKey('themes.uuid', name='fk_templates_theme'),
                       nullable=True,
                       comment="Foreign key to themes table")
    menu_type_uuid = Column(UUID(as_uuid=True),
                           ForeignKey('menu.uuid', name='fk_templates_menu'),
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

    module_uuid = Column(UUID(as_uuid=True),
                    ForeignKey('modules.uuid', name='fk_templates_module'),
                    nullable=True,
                    comment="Module that owns this template (NULL for system)")

    is_system = Column(Boolean, default=False, nullable=False,
                    comment="System-level template/page vs module-owned")
    is_admin_template = Column(Boolean, default=False, nullable=False,
                              comment="Whether template requires admin access")
    is_default_template = Column(Boolean, default=False, nullable=False,
                                comment="Whether this is default template for new pages")

    # Relationships - FIXED
    theme = relationship("Theme", back_populates="templates")
    menu_type = relationship("Menu", foreign_keys=[menu_type_uuid])
    pages = relationship("Page", back_populates="template")
    template_fragments = relationship("TemplateFragment", back_populates="template", cascade="all, delete-orphan")
    module = relationship("Module", back_populates="templates")

    # Indexes
    __table_args__ = (
        Index('idx_templates_name', 'name'),
        Index('idx_templates_theme', 'theme_uuid'),
        Index('idx_templates_menu', 'menu_type_uuid'),
        Index('idx_templates_admin', 'is_admin_template'),
        Index('idx_templates_default', 'is_default_template'),
        Index('idx_templates_layout', 'layout_type'),
        Index('idx_templates_module', 'module_uuid'),

        UniqueConstraint('module_uuid', 'name', name='uq_templates_module_name'),
    )

    def validate_slug(self):
        """Validate slug format"""
        import re
        if not re.match(r'^[a-z0-9-]+$', self.name):
            raise ValueError("Name must contain only lowercase letters, numbers, and hyphens")
