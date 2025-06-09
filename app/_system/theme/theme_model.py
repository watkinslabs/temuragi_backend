from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class Theme(BaseModel):
    """
    Comprehensive theme model for managing visual styling across all devices and contexts.
    """
    __tablename__ = 'themes'

    # Core Identity
    name = Column(String(100), unique=True, nullable=False, 
                 comment="Unique theme identifier (kebab-case)")
    display_name = Column(String(200), nullable=False,
                         comment="Human-readable theme name")
    description = Column(Text, nullable=True,
                        comment="Detailed description of theme purpose and style")
    theme_version = Column(String(50), nullable=False, default='1.0.0',
                          comment="Version number for theme updates")
    
    # Framework & Technical
    css_framework = Column(String(100), nullable=False, default='bootstrap',
                          comment="Primary CSS framework (bootstrap, tailwind, bulma)")
    css_version = Column(String(50), nullable=False, default='5.3.0',
                        comment="Framework version (e.g., '5.3.0')")
    custom_css = Column(Text, nullable=True,
                       comment="Additional custom CSS overrides")
    css_variables = Column(Text, nullable=True,
                          comment="JSON object of CSS custom properties")
    
    # Core Colors (Light/Dark Aware)
    mode = Column(String(50), nullable=False, default='light',
                 comment="Theme mode (light, dark, auto)")
    primary_color = Column(String(50), nullable=False, default='#0d6efd',
                          comment="Main brand color (hex)")
    secondary_color = Column(String(50), nullable=False, default='#6c757d',
                            comment="Secondary accent color (hex)")
    success_color = Column(String(50), nullable=False, default='#198754',
                          comment="Success state color (hex)")
    warning_color = Column(String(50), nullable=False, default='#ffc107',
                          comment="Warning state color (hex)")
    danger_color = Column(String(50), nullable=False, default='#dc3545',
                         comment="Error/danger state color (hex)")
    info_color = Column(String(50), nullable=False, default='#0dcaf0',
                       comment="Information state color (hex)")
    background_color = Column(String(50), nullable=False, default='#ffffff',
                             comment="Main background color (hex)")
    surface_color = Column(String(50), nullable=False, default='#f8f9fa',
                          comment="Card/panel background color (hex)")
    text_color = Column(String(50), nullable=False, default='#212529',
                       comment="Primary text color (hex)")
    text_muted_color = Column(String(50), nullable=False, default='#6c757d',
                             comment="Secondary text color (hex)")
    
    # Typography
    font_family_primary = Column(String(500), nullable=False, 
                                default='system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                                comment="Main content font family")
    font_family_heading = Column(String(500), nullable=True,
                                comment="Heading font family (inherits primary if null)")
    font_family_mono = Column(String(500), nullable=False, 
                             default='"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
                             comment="Monospace font for code")
    font_size_base = Column(String(50), nullable=False, default='1rem',
                           comment="Base font size (rem/px)")
    font_weight_normal = Column(Integer, nullable=False, default=400,
                               comment="Normal text weight")
    font_weight_bold = Column(Integer, nullable=False, default=600,
                             comment="Bold text weight")
    line_height_base = Column(String(50), nullable=False, default='1.5',
                             comment="Base line height")
    
    # Layout & Spacing
    container_max_width = Column(String(50), nullable=False, default='1320px',
                                comment="Maximum container width")
    grid_columns = Column(Integer, nullable=False, default=12,
                         comment="Number of grid columns")
    border_radius = Column(String(50), nullable=False, default='0.375rem',
                          comment="Default border radius")
    spacing_unit = Column(String(50), nullable=False, default='1rem',
                         comment="Base spacing unit")
    
    # Responsive Breakpoints
    breakpoint_xs = Column(String(50), nullable=False, default='0px',
                          comment="Extra small devices breakpoint")
    breakpoint_sm = Column(String(50), nullable=False, default='576px',
                          comment="Small devices breakpoint")
    breakpoint_md = Column(String(50), nullable=False, default='768px',
                          comment="Medium devices breakpoint")
    breakpoint_lg = Column(String(50), nullable=False, default='992px',
                          comment="Large devices breakpoint")
    breakpoint_xl = Column(String(50), nullable=False, default='1200px',
                          comment="Extra large devices breakpoint")
    breakpoint_xxl = Column(String(50), nullable=False, default='1400px',
                           comment="Extra extra large devices breakpoint")
    
    # Visual Effects
    shadow_sm = Column(String(200), nullable=False, default='0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
                      comment="Small shadow definition")
    shadow_md = Column(String(200), nullable=False, default='0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
                      comment="Medium shadow definition")
    shadow_lg = Column(String(200), nullable=False, default='0 1rem 3rem rgba(0, 0, 0, 0.175)',
                      comment="Large shadow definition")
    border_width = Column(String(50), nullable=False, default='1px',
                         comment="Default border width")
    border_color = Column(String(50), nullable=False, default='#dee2e6',
                         comment="Default border color (hex)")
    focus_ring_color = Column(String(100), nullable=False, default='rgba(13, 110, 253, 0.25)',
                             comment="Focus state ring color")
    focus_ring_width = Column(String(50), nullable=False, default='0.25rem',
                             comment="Focus ring width")
    
    # Animation & Transitions
    transition_duration = Column(String(50), nullable=False, default='150ms',
                                comment="Default transition time")
    animation_easing = Column(String(100), nullable=False, default='ease-in-out',
                             comment="Default easing function")
    enable_animations = Column(Boolean, default=True, nullable=False,
                              comment="Whether animations are enabled")
    enable_transitions = Column(Boolean, default=True, nullable=False,
                               comment="Whether transitions are enabled")
    
    # Component Styling
    button_border_radius = Column(String(50), nullable=True,
                                 comment="Button border radius (inherits border_radius if null)")
    input_border_radius = Column(String(50), nullable=True,
                                comment="Form input border radius (inherits border_radius if null)")
    card_border_radius = Column(String(50), nullable=True,
                               comment="Card component border radius (inherits border_radius if null)")
    navbar_height = Column(String(50), nullable=False, default='56px',
                          comment="Navigation bar height")
    sidebar_width = Column(String(50), nullable=False, default='280px',
                          comment="Sidebar width when expanded")
    footer_height = Column(String(50), nullable=False, default='60px',
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
