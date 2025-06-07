import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel




class Theme(BaseModel):
    """
    Comprehensive theme model for managing visual styling across all devices and contexts.
    
    Core Identity:
    - name: Unique identifier for the theme (kebab-case)
    - display_name: Human-readable theme name
    - description: Detailed description of theme purpose/style
    - theme_version: Version number for theme updates
    
    Framework & Technical:
    - css_framework: Primary CSS framework (bootstrap, tailwind, bulma)
    - css_version: Framework version (e.g., "5.3.0")
    - custom_css: Additional custom CSS overrides
    - css_variables: JSON object of CSS custom properties
    
    Core Colors (Light/Dark Aware):
    - mode: Theme mode (light, dark, auto)
    - primary_color: Main brand color (hex)
    - secondary_color: Secondary accent color (hex)
    - success_color: Success state color (hex)
    - warning_color: Warning state color (hex)
    - danger_color: Error/danger state color (hex)
    - info_color: Information state color (hex)
    - background_color: Main background color (hex)
    - surface_color: Card/panel background color (hex)
    - text_color: Primary text color (hex)
    - text_muted_color: Secondary text color (hex)
    
    Typography:
    - font_family_primary: Main content font
    - font_family_heading: Heading font family
    - font_family_mono: Monospace font for code
    - font_size_base: Base font size (rem/px)
    - font_weight_normal: Normal text weight (400)
    - font_weight_bold: Bold text weight (600/700)
    - line_height_base: Base line height (1.5)
    
    Layout & Spacing:
    - container_max_width: Maximum container width (px/rem)
    - grid_columns: Number of grid columns (12)
    - border_radius: Default border radius (px/rem)
    - spacing_unit: Base spacing unit (rem/px)
    
    Responsive Breakpoints:
    - breakpoint_xs: Extra small devices (px)
    - breakpoint_sm: Small devices (px)
    - breakpoint_md: Medium devices (px)
    - breakpoint_lg: Large devices (px)
    - breakpoint_xl: Extra large devices (px)
    - breakpoint_xxl: Extra extra large devices (px)
    
    Visual Effects:
    - shadow_sm: Small shadow definition
    - shadow_md: Medium shadow definition
    - shadow_lg: Large shadow definition
    - border_width: Default border width (px)
    - border_color: Default border color (hex)
    - focus_ring_color: Focus state ring color (hex)
    - focus_ring_width: Focus ring width (px)
    
    Animation & Transitions:
    - transition_duration: Default transition time (ms)
    - animation_easing: Default easing function
    - enable_animations: Whether animations are enabled
    - enable_transitions: Whether transitions are enabled
    
    Component Styling:
    - button_border_radius: Button border radius
    - input_border_radius: Form input border radius
    - card_border_radius: Card component border radius
    - navbar_height: Navigation bar height
    - sidebar_width: Sidebar width when expanded
    - footer_height: Footer height
    
    System & Metadata:
    - is_default: Whether this is the default theme
    - is_system_theme: Whether this is a core system theme
    - supports_dark_mode: Whether theme has dark mode variant
    - supports_high_contrast: Whether theme supports accessibility high contrast
    - rtl_support: Whether theme supports right-to-left languages
    """
    __tablename__ = 'themes'

    # Core Identity
    name = Column(String(50), unique=True, nullable=False, 
                 comment="Unique theme identifier (kebab-case)")
    display_name = Column(String(100), nullable=False,
                         comment="Human-readable theme name")
    description = Column(Text, nullable=True,
                        comment="Detailed description of theme purpose and style")
    theme_version = Column(String(20), nullable=False, default='1.0.0',
                          comment="Version number for theme updates")
    
    # Framework & Technical
    css_framework = Column(String(50), nullable=False, default='bootstrap',
                          comment="Primary CSS framework (bootstrap, tailwind, bulma)")
    css_version = Column(String(20), nullable=False, default='5.3.0',
                        comment="Framework version (e.g., '5.3.0')")
    custom_css = Column(Text, nullable=True,
                       comment="Additional custom CSS overrides")
    css_variables = Column(Text, nullable=True,
                          comment="JSON object of CSS custom properties")
    
    # Core Colors (Light/Dark Aware)
    mode = Column(String(10), nullable=False, default='light',
                 comment="Theme mode (light, dark, auto)")
    primary_color = Column(String(7), nullable=False, default='#0d6efd',
                          comment="Main brand color (hex)")
    secondary_color = Column(String(7), nullable=False, default='#6c757d',
                            comment="Secondary accent color (hex)")
    success_color = Column(String(7), nullable=False, default='#198754',
                          comment="Success state color (hex)")
    warning_color = Column(String(7), nullable=False, default='#ffc107',
                          comment="Warning state color (hex)")
    danger_color = Column(String(7), nullable=False, default='#dc3545',
                         comment="Error/danger state color (hex)")
    info_color = Column(String(7), nullable=False, default='#0dcaf0',
                       comment="Information state color (hex)")
    background_color = Column(String(7), nullable=False, default='#ffffff',
                             comment="Main background color (hex)")
    surface_color = Column(String(7), nullable=False, default='#f8f9fa',
                          comment="Card/panel background color (hex)")
    text_color = Column(String(7), nullable=False, default='#212529',
                       comment="Primary text color (hex)")
    text_muted_color = Column(String(7), nullable=False, default='#6c757d',
                             comment="Secondary text color (hex)")
    
    # Typography - UPDATED LENGTHS
    font_family_primary = Column(String(300), nullable=False, 
                                default='system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                                comment="Main content font family")
    font_family_heading = Column(String(300), nullable=True,
                                comment="Heading font family (inherits primary if null)")
    font_family_mono = Column(String(300), nullable=False, 
                             default='"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
                             comment="Monospace font for code")
    font_size_base = Column(String(10), nullable=False, default='1rem',
                           comment="Base font size (rem/px)")
    font_weight_normal = Column(Integer, nullable=False, default=400,
                               comment="Normal text weight")
    font_weight_bold = Column(Integer, nullable=False, default=600,
                             comment="Bold text weight")
    line_height_base = Column(String(10), nullable=False, default='1.5',
                             comment="Base line height")
    
    # Layout & Spacing - NO CHANGES
    container_max_width = Column(String(10), nullable=False, default='1320px',
                                comment="Maximum container width")
    grid_columns = Column(Integer, nullable=False, default=12,
                         comment="Number of grid columns")
    border_radius = Column(String(10), nullable=False, default='0.375rem',
                          comment="Default border radius")
    spacing_unit = Column(String(10), nullable=False, default='1rem',
                         comment="Base spacing unit")
    
    # Responsive Breakpoints - NO CHANGES
    breakpoint_xs = Column(String(10), nullable=False, default='0px',
                          comment="Extra small devices breakpoint")
    breakpoint_sm = Column(String(10), nullable=False, default='576px',
                          comment="Small devices breakpoint")
    breakpoint_md = Column(String(10), nullable=False, default='768px',
                          comment="Medium devices breakpoint")
    breakpoint_lg = Column(String(10), nullable=False, default='992px',
                          comment="Large devices breakpoint")
    breakpoint_xl = Column(String(10), nullable=False, default='1200px',
                          comment="Extra large devices breakpoint")
    breakpoint_xxl = Column(String(10), nullable=False, default='1400px',
                           comment="Extra extra large devices breakpoint")
    
    # Visual Effects - UPDATED LENGTHS
    shadow_sm = Column(String(150), nullable=False, default='0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
                      comment="Small shadow definition")
    shadow_md = Column(String(150), nullable=False, default='0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
                      comment="Medium shadow definition")
    shadow_lg = Column(String(150), nullable=False, default='0 1rem 3rem rgba(0, 0, 0, 0.175)',
                      comment="Large shadow definition")
    border_width = Column(String(10), nullable=False, default='1px',
                         comment="Default border width")
    border_color = Column(String(7), nullable=False, default='#dee2e6',
                         comment="Default border color (hex)")
    focus_ring_color = Column(String(50), nullable=False, default='rgba(13, 110, 253, 0.25)',
                             comment="Focus state ring color")
    focus_ring_width = Column(String(10), nullable=False, default='0.25rem',
                             comment="Focus ring width")
    
    # Animation & Transitions
    transition_duration = Column(String(10), nullable=False, default='150ms',
                                comment="Default transition time")
    animation_easing = Column(String(50), nullable=False, default='ease-in-out',
                             comment="Default easing function")
    enable_animations = Column(Boolean, default=True, nullable=False,
                              comment="Whether animations are enabled")
    enable_transitions = Column(Boolean, default=True, nullable=False,
                               comment="Whether transitions are enabled")
    
    # Component Styling
    button_border_radius = Column(String(10), nullable=True,
                                 comment="Button border radius (inherits border_radius if null)")
    input_border_radius = Column(String(10), nullable=True,
                                comment="Form input border radius (inherits border_radius if null)")
    card_border_radius = Column(String(10), nullable=True,
                               comment="Card component border radius (inherits border_radius if null)")
    navbar_height = Column(String(10), nullable=False, default='56px',
                          comment="Navigation bar height")
    sidebar_width = Column(String(10), nullable=False, default='280px',
                          comment="Sidebar width when expanded")
    footer_height = Column(String(10), nullable=False, default='60px',
                          comment="Footer height")
    
    # System & Metadata
    is_default = Column(Boolean, default=False, nullable=False,
                       comment="Whether this is the default theme")
    is_system_theme = Column(Boolean, default=False, nullable=False,
                            comment="System theme that cannot be deleted")
    supports_dark_mode = Column(Boolean, default=False, nullable=False,
                               comment="Whether theme has dark mode variant")
    supports_high_contrast = Column(Boolean, default=False, nullable=False,
                                   comment="Whether theme supports accessibility high contrast")
    rtl_support = Column(Boolean, default=False, nullable=False,
                        comment="Whether theme supports right-to-left languages")

    # Relationships
    templates = relationship("Template", back_populates="theme")

    # Relationships
    templates = relationship("Template", back_populates="theme")

    # Indexes
    __table_args__ = (
        Index('idx_themes_name', 'name'),
        Index('idx_themes_default', 'is_default'),
        Index('idx_themes_system', 'is_system_theme'),
        Index('idx_themes_mode', 'mode'),
        Index('idx_themes_framework', 'css_framework'),
        Index('idx_themes_version', 'theme_version'),
        UniqueConstraint('name', name='uq_themes_name'),
    )

    @classmethod
    def create_initial_data(cls, session):
        """Create initial theme data"""
        initial_themes = [
            {
                'name': 'light-2025',
                'display_name': 'Light 2025',
                'description': 'Clean, professional theme using Bootstrap 5 with default styling',
                'theme_version': '1.0.0',
                'css_framework': 'bootstrap',
                'css_version': '5.3.0',
                'mode': 'light',
                'primary_color': '#0d6efd',
                'secondary_color': '#6c757d',
                'success_color': '#198754',
                'warning_color': '#ffc107',
                'danger_color': '#dc3545',
                'info_color': '#0dcaf0',
                'background_color': '#ffffff',
                'surface_color': '#f8f9fa',
                'text_color': '#212529',
                'text_muted_color': '#6c757d',
                'font_family_primary': 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                'font_family_mono': '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
                'font_size_base': '1rem',
                'font_weight_normal': 400,
                'font_weight_bold': 600,
                'line_height_base': '1.5',
                'container_max_width': '1320px',
                'grid_columns': 12,
                'border_radius': '0.375rem',
                'spacing_unit': '1rem',
                'breakpoint_xs': '0px',
                'breakpoint_sm': '576px',
                'breakpoint_md': '768px',
                'breakpoint_lg': '992px',
                'breakpoint_xl': '1200px',
                'breakpoint_xxl': '1400px',
                'shadow_sm': '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
                'shadow_md': '0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
                'shadow_lg': '0 1rem 3rem rgba(0, 0, 0, 0.175)',
                'border_width': '1px',
                'border_color': '#dee2e6',
                'focus_ring_color': 'rgba(13, 110, 253, 0.25)',
                'focus_ring_width': '0.25rem',
                'transition_duration': '150ms',
                'animation_easing': 'ease-in-out',
                'enable_animations': True,
                'enable_transitions': True,
                'navbar_height': '56px',
                'sidebar_width': '280px',
                'footer_height': '60px',
                'is_default': True,
                'is_system_theme': True,
                'supports_dark_mode': False,
                'supports_high_contrast': False,
                'rtl_support': False
            },
            {
                'name': 'dark-2025',
                'display_name': 'Dark 2025',
                'description': 'Dark mode theme with Bootstrap 5 for reduced eye strain',
                'theme_version': '1.0.0',
                'css_framework': 'bootstrap',
                'css_version': '5.3.0',
                'mode': 'dark',
                'primary_color': '#0d6efd',
                'secondary_color': '#adb5bd',
                'success_color': '#198754',
                'warning_color': '#ffc107',
                'danger_color': '#dc3545',
                'info_color': '#0dcaf0',
                'background_color': '#212529',
                'surface_color': '#343a40',
                'text_color': '#ffffff',
                'text_muted_color': '#adb5bd',
                'font_family_primary': 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                'font_family_mono': '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
                'font_size_base': '1rem',
                'font_weight_normal': 400,
                'font_weight_bold': 600,
                'line_height_base': '1.5',
                'container_max_width': '1320px',
                'grid_columns': 12,
                'border_radius': '0.375rem',
                'spacing_unit': '1rem',
                'breakpoint_xs': '0px',
                'breakpoint_sm': '576px',
                'breakpoint_md': '768px',
                'breakpoint_lg': '992px',
                'breakpoint_xl': '1200px',
                'breakpoint_xxl': '1400px',
                'shadow_sm': '0 0.125rem 0.25rem rgba(0, 0, 0, 0.3)',
                'shadow_md': '0 0.5rem 1rem rgba(0, 0, 0, 0.4)',
                'shadow_lg': '0 1rem 3rem rgba(0, 0, 0, 0.5)',
                'border_width': '1px',
                'border_color': '#495057',
                'focus_ring_color': 'rgba(13, 110, 253, 0.4)',
                'focus_ring_width': '0.25rem',
                'transition_duration': '150ms',
                'animation_easing': 'ease-in-out',
                'enable_animations': True,
                'enable_transitions': True,
                'navbar_height': '56px',
                'sidebar_width': '280px',
                'footer_height': '60px',
                'custom_css': 'body { background-color: #212529; color: #ffffff; }',
                'is_default': False,
                'is_system_theme': True,
                'supports_dark_mode': True,
                'supports_high_contrast': False,
                'rtl_support': False
            },
         
        ]

        for theme_data in initial_themes:
            existing = session.query(cls).filter_by(name=theme_data['name']).first()
            if not existing:
                theme = cls(**theme_data)
                session.add(theme)