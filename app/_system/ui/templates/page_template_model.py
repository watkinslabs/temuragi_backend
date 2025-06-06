import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class PageTemplate(BaseModel):
    """
    Page template model for defining reusable page structures and layouts.
    
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
    __tablename__ = 'page_templates'

    name = Column(String(50), unique=True, nullable=False,
                 comment="Unique template identifier (kebab-case)")
    display_name = Column(String(100), nullable=False,
                         comment="Human-readable template name")
    description = Column(Text, nullable=True,
                        comment="Description of template purpose and usage")
    template_file = Column(String(255), nullable=False,
                          comment="Path to Jinja2 template file")
    theme_uuid = Column(UUID(as_uuid=True),
                       ForeignKey('themes.uuid', name='fk_page_templates_theme'),
                       nullable=False,
                       comment="Foreign key to themes table")
    menu_type_uuid = Column(UUID(as_uuid=True),
                           ForeignKey('menu.uuid', name='fk_page_templates_menu'),
                           nullable=False,
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

    # Relationships
    theme = relationship("Theme", back_populates="page_templates")
    menu_type = relationship("Menu", foreign_keys=[menu_type_uuid])
    pages = relationship("Page", back_populates="page_template")
    template_contents = relationship("PageTemplateContent", back_populates="page_template", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_page_templates_name', 'name'),
        Index('idx_page_templates_theme', 'theme_uuid'),
        Index('idx_page_templates_menu', 'menu_type_uuid'),
        Index('idx_page_templates_admin', 'is_admin_template'),
        Index('idx_page_templates_default', 'is_default_template'),
        Index('idx_page_templates_layout', 'layout_type'),
        UniqueConstraint('name', name='uq_page_templates_name'),
    )

    def validate_slug(self):
        """Validate slug format"""
        import re
        if not re.match(r'^[a-z0-9-]+$', self.slug):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")    

    @classmethod
    def create_initial_data(cls, session):
        """Create initial page template data"""
        from app.models import Theme, Menu

        # Get required foreign key values
        bootstrap_theme = session.query(Theme).filter_by(name='light-2025').first()
        admin_theme = session.query(Theme).filter_by(name='light-2025').first()
        
        main_menu = session.query(Menu).filter_by(name='MAIN').first()
        admin_menu = session.query(Menu).filter_by(name='ADMIN').first()

        if not all([bootstrap_theme, admin_theme, main_menu, admin_menu]):
            print("Warning: Required themes or menu types not found for page template creation")
            return

        initial_templates = [
            {
                'name': 'public-default',
                'display_name': 'Public Default',
                'description': 'Standard public-facing page template with main navigation',
                'template_file': 'templates/public/default.html',
                'theme_uuid': bootstrap_theme.uuid,
                'menu_type_uuid': main_menu.uuid,
                'layout_type': 'full-width',
                'container_class': 'container',
                'sidebar_enabled': False,
                'header_type': 'static',
                'footer_type': 'static',
                'breadcrumbs_enabled': True,
                'is_admin_template': False,
                'is_default_template': True
            },
            {
                'name': 'ops-default',
                'display_name': 'Logged in Default',
                'description': 'Standard public-facing page template with main navigation',
                'template_file': 'templates/public/default.html',
                'theme_uuid': bootstrap_theme.uuid,
                'menu_type_uuid': main_menu.uuid,
                'layout_type': 'full-width',
                'container_class': 'container',
                'sidebar_enabled': False,
                'header_type': 'static',
                'footer_type': 'static',
                'breadcrumbs_enabled': True,
                'is_admin_template': False,
                'is_default_template': True
            },
            {
                'name': 'admin-dashboard',
                'display_name': 'Admin Dashboard',
                'description': 'Administrative dashboard with sidebar navigation',
                'template_file': 'templates/admin/dashboard.html',
                'theme_uuid': admin_theme.uuid,
                'menu_type_uuid': admin_menu.uuid,
                'layout_type': 'sidebar-left',
                'container_class': 'container-fluid',
                'sidebar_enabled': True,
                'header_type': 'fixed',
                'footer_type': 'minimal',
                'breadcrumbs_enabled': True,
                'is_admin_template': True,
                'is_default_template': False
            }
            
        ]

        for template_data in initial_templates:
            existing = session.query(cls).filter_by(name=template_data['name']).first()
            if not existing:
                template = cls(**template_data)
                session.add(template)