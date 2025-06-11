import uuid
import logging
from jinja2 import Environment
from sqlalchemy.orm import Session
from flask import current_app, has_app_context
from markupsafe import Markup

class TemplateRenderer:
    """Renders templates using database fragments with bulletproof error handling"""

    def __init__(self, session: Session, logger=None):
        self.session = session
        self.logger = logger or self._get_logger()
        self.current_page_uuid = None
        self.current_env = None  # Store current environment for safe rendering

    def _get_logger(self):
        """Get logger from Flask app context or create fallback"""
        if has_app_context():
            return current_app.logger
        else:
            return logging.getLogger('template_renderer')

    def _safe_render(self, template_source, data=None, context="unknown"):
        """Safely render any template source with error handling using current environment"""
        try:
            # Use the current environment if available, otherwise create a basic one
            if self.current_env:
                template = self.current_env.from_string(template_source)
            else:
                from app.classes import SafeUndefined
                # Create environment with SafeUndefined for standalone rendering
                env = Environment(undefined=SafeUndefined)
                template = env.from_string(template_source)
            result = template.render(**(data or {}))
            
            # Mark as safe HTML to prevent double-escaping
            from markupsafe import Markup
            return Markup(result)
        except Exception as e:
            self.logger.error(f"Error rendering {context}: {e}")
            # Only handle actual template syntax errors, not undefined variables
            from markupsafe import Markup
            return Markup(f'<div class="template-error">TEMPLATE ERROR in {context}: {str(e)}</div>')

    def render_template(self, template_uuid: uuid.UUID, data: dict = None) -> str:
        """Render a template without page context (original functionality)"""
        try:
            self.logger.info(f"Rendering template {template_uuid}")
            self.current_page_uuid = None
            from app.classes import TemplateLoader, SafeUndefined
            # Create loader and environment
            loader = TemplateLoader(self.session, template_uuid, None, self.logger)
            env = Environment(
                loader=loader,
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=SafeUndefined
            )
            
            # Store environment for safe rendering
            self.current_env = env

            # Register template functions
            self._register_template_functions(env, template_uuid)

            # Get base fragment and render
            base_fragment_key = loader.get_base_fragment_key()
            template = env.get_template(base_fragment_key)

            result = template.render(**(data or {}))
            self.logger.info(f"Template {template_uuid} rendered successfully ({len(result)} chars)")
            return result
        
        except Exception as e:
            self.logger.error(f"Critical error rendering template {template_uuid}: {e}")
            return f"<!-- Template {template_uuid} failed to render: {e} -->"
        finally:
            # Clear environment reference
            self.current_env = None

    def render_page(self, page_uuid: uuid.UUID, data: dict = None) -> str:
        """Render a page using its template with page fragment support"""
        try:
            self.logger.info(f"Rendering page {page_uuid}")

            # Load page
            from app.models import Page
            from app.classes import TemplateLoader,SafeUndefined
            page = self.session.query(Page).filter_by(uuid=page_uuid).first()
            if not page:
                return f"<!-- Page {page_uuid} not found -->"

            if not page.template_uuid:
                return f"<!-- Page {page_uuid} has no template assigned -->"

            # Check if page is visible
            if not page.is_visible():
                self.logger.warning(f"Page {page_uuid} is not visible (published: {page.published})")

            # Set current page context
            self.current_page_uuid = page_uuid

            # Build page context
            page_context = self._build_page_context(page)
            merged_data = {**page_context, **(data or {})}

            # Create loader with page context and environment
            loader = TemplateLoader(self.session, page.template_uuid, page_uuid, self.logger)
            env = Environment(
                loader=loader,
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=SafeUndefined
            )
            
            # Store environment for safe rendering
            self.current_env = env

            # Register template functions with page support
            self._register_template_functions_with_page(env, page.template_uuid, page_uuid)

            # Get base fragment and render
            base_fragment_key = loader.get_base_fragment_key()
            template = env.get_template(base_fragment_key)

            result = template.render(**merged_data)
            self.logger.info(f"Page {page_uuid} rendered successfully ({len(result)} chars)")
            return result
        
        except Exception as e:
            self.logger.error(f"Critical error rendering page {page_uuid}: {e}")
            return f"<!-- Page {page_uuid} failed to render: {e} -->"
        finally:
            # Clear environment reference
            self.current_env = None

    def _build_page_context(self, page):
        """Build context data for page rendering"""
        try:
            return {
                'page': {
                    'uuid': str(page.uuid),
                    'title': getattr(page, 'title', ''),
                    'slug': getattr(page, 'slug', ''),
                    'name': getattr(page, 'name', ''),
                    'meta_description': getattr(page, 'meta_description', ''),
                    'meta_keywords': getattr(page, 'meta_keywords', ''),
                    'og_title': getattr(page, 'og_title', ''),
                    'og_description': getattr(page, 'og_description', ''),
                    'og_image': getattr(page, 'og_image', ''),
                    'canonical_url': getattr(page, 'canonical_url', ''),
                    'published': getattr(page, 'published', False),
                    'featured': getattr(page, 'featured', False),
                    'view_count': getattr(page, 'view_count', 0),
                    'requires_auth': getattr(page, 'requires_auth', False),
                    'publish_date': getattr(page, 'publish_date', None),
                    'expire_date': getattr(page, 'expire_date', None)
                }
            }
        except Exception as e:
            self.logger.error(f"Error building page context: {e}")
            return {'page': {'title': 'Page Error', 'slug': 'error'}}

    def _safe_get_flashed_messages(self, with_categories=False):
        """Safely get flashed messages, always return proper format"""
        try:
            from flask import get_flashed_messages
            messages = get_flashed_messages(with_categories=with_categories)
            
            if with_categories:
                # Ensure all items are proper 2-tuples
                safe_messages = []
                for item in messages:
                    try:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            safe_messages.append((str(item[0]), str(item[1])))
                        elif isinstance(item, (list, tuple)) and len(item) == 1:
                            safe_messages.append(('info', str(item[0])))
                        elif hasattr(item, '__iter__') and not isinstance(item, str):
                            # Handle other iterables
                            items_list = list(item)
                            if len(items_list) >= 2:
                                safe_messages.append((str(items_list[0]), str(items_list[1])))
                            elif len(items_list) == 1:
                                safe_messages.append(('info', str(items_list[0])))
                            else:
                                safe_messages.append(('info', str(item)))
                        else:
                            safe_messages.append(('info', str(item)))
                    except Exception as e:
                        safe_messages.append(('error', f'Message format error: {e}'))
                return safe_messages
            else:
                # Ensure all items are strings
                safe_messages = []
                for msg in messages:
                    try:
                        safe_messages.append(str(msg))
                    except:
                        safe_messages.append('Message conversion error')
                return safe_messages
        except ImportError:
            # Flask not available or get_flashed_messages not imported
            self.logger.warning("Flask get_flashed_messages not available")
            if with_categories:
                return []
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting flashed messages: {e}")
            if with_categories:
                return [('error', f'Flash message error: {e}')]
            else:
                return [f'Flash message error: {e}']

    def _register_theme_functions(self, env: Environment):
        """Register theme-related template functions"""
        
        def theme_css(theme_uuid_or_name=None):
            """Generate complete CSS for a theme"""
            
            return self.theme_css(self.session, theme_uuid_or_name)
        
        # Register the function
        env.globals['theme_css'] = theme_css

    def _register_template_functions(self, env: Environment, template_uuid: uuid.UUID):
        """Register template functions without page support (original functionality)"""

        def safe_render_fragment(fragment_key):
            """Safely render a template fragment by key"""
            try:
                from app.models import TemplateFragment
                from markupsafe import Markup

                self.logger.debug(f"Rendering template fragment '{fragment_key}'")

                fragment = self.session.query(TemplateFragment).filter_by(
                    template_uuid=template_uuid,
                    fragment_key=fragment_key,
                    is_active=True
                ).first()

                if not fragment or not fragment.template_source:
                    self.logger.warning(f"Template fragment '{fragment_key}' not found")
                    return Markup(f"<!-- Template fragment '{fragment_key}' not found -->")

                # Safely render the fragment
                return self._safe_render(fragment.template_source, {}, f"template fragment '{fragment_key}'")

            except Exception as e:
                self.logger.error(f"Error rendering template fragment '{fragment_key}': {e}")
                from markupsafe import Markup
                return Markup(f"<!-- Error rendering template fragment '{fragment_key}': {e} -->")

        def safe_include_fragment(fragment_key, **kwargs):
            """Safely include and render a template fragment with data"""
            try:
                from app.models import TemplateFragment
                from markupsafe import Markup

                self.logger.debug(f"Including template fragment '{fragment_key}' with data: {list(kwargs.keys())}")

                fragment = self.session.query(TemplateFragment).filter_by(
                    template_uuid=template_uuid,
                    fragment_key=fragment_key,
                    is_active=True
                ).first()

                if not fragment or not fragment.template_source:
                    self.logger.warning(f"Template fragment '{fragment_key}' not found for include")
                    return Markup(f"<!-- Template fragment '{fragment_key}' not found -->")

                # Safely render with data
                return self._safe_render(fragment.template_source, kwargs, f"template include '{fragment_key}'")

            except Exception as e:
                self.logger.error(f"Error including template fragment '{fragment_key}': {e}")
                from markupsafe import Markup
                return Markup(f"<!-- Error including template fragment '{fragment_key}': {e} -->")

        def safe_render_block(block_key, default_content=None, **kwargs):
            """Render a block from template fragments only (no page overrides)"""
            try:
                from app.models import TemplateFragment
                from markupsafe import Markup

                self.logger.debug(f"Rendering template block '{block_key}'")

                # Check for template fragment
                template_fragment = None
                try:
                    template_fragment = self.session.query(TemplateFragment).filter_by(
                        template_uuid=template_uuid,
                        fragment_key=block_key,
                        is_active=True
                    ).first()
                except:
                    pass

                if template_fragment and template_fragment.template_source:
                    self.logger.debug(f"Found template fragment for block '{block_key}'")
                    return self._safe_render(template_fragment.template_source, kwargs, f"template block '{block_key}'")

                # Use default content if provided
                if default_content is not None:
                    self.logger.debug(f"Using default content for block '{block_key}'")
                    if isinstance(default_content, str):
                        return self._safe_render(default_content, kwargs, f"default block '{block_key}'")
                    else:
                        return Markup(str(default_content))

                # No content found
                self.logger.debug(f"No content found for block '{block_key}'")
                return Markup(f"<!-- No content for block '{block_key}' -->")

            except Exception as e:
                self.logger.error(f"Error rendering block '{block_key}': {e}")
                from markupsafe import Markup
                return Markup(f"<!-- Error rendering block '{block_key}': {e} -->")

        def safe_get_flashed_messages(with_categories=False):
            """Safely get flashed messages"""
            return self._safe_get_flashed_messages(with_categories)

        self._register_theme_functions(env)

        # Register functions
        env.globals['render_fragment'] = safe_render_fragment
        env.globals['include_fragment'] = safe_include_fragment
        env.globals['render_block'] = safe_render_block
        env.globals['get_flashed_messages'] = safe_get_flashed_messages

    def _register_template_functions_with_page(self, env: Environment, template_uuid: uuid.UUID, page_uuid: uuid.UUID):
        """Register template functions with enhanced page fragment support"""

        def safe_render_fragment(fragment_key):
            """Safely render a template fragment by key"""
            try:
                from app.models import TemplateFragment

                self.logger.debug(f"Rendering template fragment '{fragment_key}'")

                fragment = self.session.query(TemplateFragment).filter_by(
                    template_uuid=template_uuid,
                    fragment_key=fragment_key,
                    is_active=True
                ).first()

                if not fragment or not fragment.template_source:
                    self.logger.warning(f"Template fragment '{fragment_key}' not found")
                    return f"<!-- Template fragment '{fragment_key}' not found -->"

                # Safely render the fragment
                return self._safe_render(fragment.template_source, {}, f"template fragment '{fragment_key}'")

            except Exception as e:
                self.logger.error(f"Error rendering template fragment '{fragment_key}': {e}")
                return f"<!-- Error rendering template fragment '{fragment_key}': {e} -->"

        def safe_include_fragment(fragment_key, **kwargs):
            """Safely include and render a template fragment with data"""
            try:
                from app.models import TemplateFragment

                self.logger.debug(f"Including template fragment '{fragment_key}' with data: {list(kwargs.keys())}")

                fragment = self.session.query(TemplateFragment).filter_by(
                    template_uuid=template_uuid,
                    fragment_key=fragment_key,
                    is_active=True
                ).first()

                if not fragment or not fragment.template_source:
                    self.logger.warning(f"Template fragment '{fragment_key}' not found for include")
                    return f"<!-- Template fragment '{fragment_key}' not found -->"

                # Safely render with data
                return self._safe_render(fragment.template_source, kwargs, f"template include '{fragment_key}'")

            except Exception as e:
                self.logger.error(f"Error including template fragment '{fragment_key}': {e}")
                return f"<!-- Error including template fragment '{fragment_key}': {e} -->"

        def safe_render_page_fragment(fragment_key, default_block=None, **kwargs):
            """Safely render page fragment with block-like fallback behavior"""
            try:
                from app.models import PageFragment
                from app.classes import BlockProcessor
                from markupsafe import Markup

                self.logger.debug(f"Rendering page fragment '{fragment_key}' for page {page_uuid}")

                # Try to get page fragment first
                page_fragment = PageFragment.get_active_by_key(self.session, page_uuid, fragment_key)

                if page_fragment and page_fragment.content_source:
                    self.logger.debug(f"Found page fragment '{fragment_key}'")

                    # Handle different content types
                    if getattr(page_fragment, 'content_type', 'text/html') == 'text/html':
                        # HTML content - process blocks and render as template with page context
                        page_vars = kwargs.copy()
                        # Make page fragment variables available if they exist
                        try:
                            if hasattr(page_fragment, 'get_variables_data_dict'):
                                page_vars.update(page_fragment.get_variables_data_dict())
                        except:
                            pass

                        # IMPORTANT: Process blocks in page fragment content
                        block_processor = BlockProcessor(self.session, template_uuid, page_uuid, self.logger)
                        processed_content = block_processor.process_template_source(page_fragment.content_source)
                        
                        return self._safe_render(processed_content, page_vars, f"page fragment '{fragment_key}'")
                    else:
                        # Plain text or other - return as-is but still as Markup
                        return Markup(str(page_fragment.content_source))

                # No page fragment found - use default block if provided
                elif default_block is not None:
                    self.logger.debug(f"No page fragment '{fragment_key}' found, using default block")

                    if isinstance(default_block, str):
                        # Process blocks in default content too
                        block_processor = BlockProcessor(self.session, template_uuid, page_uuid, self.logger)
                        processed_default = block_processor.process_template_source(default_block)
                        return self._safe_render(processed_default, kwargs, f"default block for '{fragment_key}'")
                    else:
                        # Return as string
                        return Markup(str(default_block))

                # No content at all
                else:
                    self.logger.debug(f"No page fragment or default block for '{fragment_key}'")
                    return Markup(f"<!-- No content for page fragment '{fragment_key}' -->")

            except Exception as e:
                self.logger.error(f"Error rendering page fragment '{fragment_key}': {e}")
                from markupsafe import Markup
                return Markup(f"<!-- Error rendering page fragment '{fragment_key}': {e} -->")

        def safe_render_block(block_key, default_content=None, **kwargs):
            """Render a block with page fragment override capability"""
            try:
                from app.models import PageFragment
                from app.models import TemplateFragment
                from app.classes import BlockProcessor
                
                from markupsafe import Markup

                self.logger.debug(f"Rendering block '{block_key}' for page {page_uuid}")

                # First priority: Check for page fragment override
                page_fragment = None
                try:
                    page_fragment = PageFragment.get_active_by_key(self.session, page_uuid, block_key)
                except:
                    pass

                if page_fragment and page_fragment.content_source:
                    self.logger.debug(f"Found page fragment override for block '{block_key}'")
                    
                    # Handle different content types
                    if getattr(page_fragment, 'content_type', 'text/html') == 'text/html':
                        # HTML content - process blocks and render as template with context
                        block_vars = kwargs.copy()
                        try:
                            if hasattr(page_fragment, 'get_variables_data_dict'):
                                block_vars.update(page_fragment.get_variables_data_dict())
                        except:
                            pass
                        
                        # IMPORTANT: Process blocks in page fragment content
                        block_processor = BlockProcessor(self.session, template_uuid, page_uuid, self.logger)
                        processed_content = block_processor.process_template_source(page_fragment.content_source)
                        
                        return self._safe_render(processed_content, block_vars, f"page block '{block_key}'")
                    else:
                        # Plain text or other - return as-is
                        return Markup(str(page_fragment.content_source))

                # Second priority: Check for template fragment
                template_fragment = None
                try:
                    template_fragment = self.session.query(TemplateFragment).filter_by(
                        template_uuid=template_uuid,
                        fragment_key=block_key,
                        is_active=True
                    ).first()
                except:
                    pass

                if template_fragment and template_fragment.template_source:
                    self.logger.debug(f"Found template fragment for block '{block_key}'")
                    # Template fragments are already processed by the TemplateLoader
                    return self._safe_render(template_fragment.template_source, kwargs, f"template block '{block_key}'")

                # Third priority: Use default content if provided
                if default_content is not None:
                    self.logger.debug(f"Using default content for block '{block_key}'")
                    if isinstance(default_content, str):
                        # Process blocks in default content too
                        block_processor = BlockProcessor(self.session, template_uuid, page_uuid, self.logger)
                        processed_default = block_processor.process_template_source(default_content)
                        return self._safe_render(processed_default, kwargs, f"default block '{block_key}'")
                    else:
                        return Markup(str(default_content))

                # No content found
                self.logger.debug(f"No content found for block '{block_key}'")
                return Markup(f"<!-- No content for block '{block_key}' -->")

            except Exception as e:
                self.logger.error(f"Error rendering block '{block_key}': {e}")
                from markupsafe import Markup
                return Markup(f"<!-- Error rendering block '{block_key}': {e} -->")

        def safe_get_flashed_messages(with_categories=False):
            """Safely get flashed messages"""
            return self._safe_get_flashed_messages(with_categories)

        self._register_theme_functions(env)

        # Register all functions
        env.globals['render_fragment'] = safe_render_fragment
        env.globals['include_fragment'] = safe_include_fragment
        env.globals['render_page_fragment'] = safe_render_page_fragment
        env.globals['render_block'] = safe_render_block
        env.globals['get_flashed_messages'] = safe_get_flashed_messages

    def theme_css(self, session, theme_uuid_or_name=None):
        """
        Generate complete CSS for a theme including variables and custom styles.
        Can be called in templates like {{ theme_css() }}
        
        Args:
            session: SQLAlchemy session
            theme_uuid_or_name: Theme UUID string, name, or None for default theme
            
        Returns:
            Complete CSS as a string ready for <style> block
        """
        try:
            from app.models import Theme
            from sqlalchemy import or_
            from markupsafe import Markup
            
            # Get the theme
            theme = None
            if theme_uuid_or_name:
                theme = session.query(Theme).filter(
                    or_(
                        Theme.uuid == theme_uuid_or_name,
                        Theme.name == theme_uuid_or_name
                    )
                ).first()
            
            if not theme:
                theme = session.query(Theme).filter_by(is_default=True).first()
                
            if not theme:
                theme = session.query(Theme).first()
                
            if not theme:
                return "/* No theme found */"
                
            # Build CSS variables section
            css_vars = []
            
            # Core color variables (light theme)
            css_vars.extend([
                f"--theme-primary: {theme.primary_color};",
                f"--theme-secondary: {theme.secondary_color};",
                f"--theme-success: {theme.success_color};",
                f"--theme-warning: {theme.warning_color};",
                f"--theme-danger: {theme.danger_color};",
                f"--theme-info: {theme.info_color};",
                f"--theme-background: {theme.background_color};",
                f"--theme-surface: {theme.surface_color};",
                f"--theme-text: {theme.text_color};",
                f"--theme-text-muted: {theme.text_muted_color};",
                f"--theme-border-color: {theme.border_color};"
            ])
            
            # Dark mode color variables
            if theme.supports_dark_mode:
                css_vars.extend([
                    f"--theme-primary-dark: {theme.primary_color_dark or theme.primary_color};",
                    f"--theme-secondary-dark: {theme.secondary_color_dark or theme.secondary_color};",
                    f"--theme-success-dark: {theme.success_color_dark or theme.success_color};",
                    f"--theme-warning-dark: {theme.warning_color_dark or theme.warning_color};",
                    f"--theme-danger-dark: {theme.danger_color_dark or theme.danger_color};",
                    f"--theme-info-dark: {theme.info_color_dark or theme.info_color};",
                    f"--theme-background-dark: {theme.background_color_dark or theme.background_color};",
                    f"--theme-surface-dark: {theme.surface_color_dark or theme.surface_color};",
                    f"--theme-text-dark: {theme.text_color_dark or theme.text_color};",
                    f"--theme-text-muted-dark: {theme.text_muted_color_dark or theme.text_muted_color};",
                    f"--theme-border-color-dark: {theme.border_color_dark or theme.border_color};"
                ])
            
            # Typography variables
            css_vars.extend([
                f"--theme-font-primary: {theme.font_family_primary};",
                f"--theme-font-heading: {theme.font_family_heading or theme.font_family_primary};",
                f"--theme-font-mono: {theme.font_family_mono};",
                f"--theme-font-size-base: {theme.font_size_base};",
                f"--theme-font-weight-normal: {theme.font_weight_normal};",
                f"--theme-font-weight-bold: {theme.font_weight_bold};",
                f"--theme-line-height-base: {theme.line_height_base};"
            ])
            
            # Layout variables
            css_vars.extend([
                f"--theme-container-max-width: {theme.container_max_width};",
                f"--theme-grid-columns: {theme.grid_columns};",
                f"--theme-border-radius: {theme.border_radius};",
                f"--theme-spacing-unit: {theme.spacing_unit};"
            ])
            
            # Responsive breakpoints
            css_vars.extend([
                f"--theme-breakpoint-xs: {theme.breakpoint_xs};",
                f"--theme-breakpoint-sm: {theme.breakpoint_sm};",
                f"--theme-breakpoint-md: {theme.breakpoint_md};",
                f"--theme-breakpoint-lg: {theme.breakpoint_lg};",
                f"--theme-breakpoint-xl: {theme.breakpoint_xl};",
                f"--theme-breakpoint-xxl: {theme.breakpoint_xxl};"
            ])
            
            # Visual effects
            css_vars.extend([
                f"--theme-shadow-sm: {theme.shadow_sm};",
                f"--theme-shadow-md: {theme.shadow_md};",
                f"--theme-shadow-lg: {theme.shadow_lg};",
                f"--theme-border-width: {theme.border_width};",
                f"--theme-focus-ring-color: {theme.focus_ring_color};",
                f"--theme-focus-ring-width: {theme.focus_ring_width};"
            ])
            
            # Animation variables
            css_vars.extend([
                f"--theme-transition-duration: {theme.transition_duration};",
                f"--theme-animation-easing: {theme.animation_easing};"
            ])
            
            # Component styling
            css_vars.extend([
                f"--theme-button-border-radius: {theme.button_border_radius or theme.border_radius};",
                f"--theme-input-border-radius: {theme.input_border_radius or theme.border_radius};",
                f"--theme-card-border-radius: {theme.card_border_radius or theme.border_radius};",
                f"--theme-navbar-height: {theme.navbar_height};",
                f"--theme-sidebar-width: {theme.sidebar_width};",
                f"--theme-footer-height: {theme.footer_height};"
            ])
            
            # Parse JSON CSS variables if they exist
            import json
            if theme.css_variables:
                try:
                    custom_vars = json.loads(theme.css_variables)
                    for key, value in custom_vars.items():
                        if not key.startswith('--'):
                            key = f"--{key}"
                        css_vars.append(f"{key}: {value};")
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Build the complete CSS
            css_output = []
            
            # CSS Variables in :root
            css_output.append(":root {")
            for var in css_vars:
                css_output.append(f"  {var}")
            css_output.append("}")
            
            # Body defaults using theme variables
            css_output.extend([
                "",
                "body {",
                "  font-family: var(--theme-font-primary);",
                "  font-size: var(--theme-font-size-base);",
                "  font-weight: var(--theme-font-weight-normal);",
                "  line-height: var(--theme-line-height-base);",
                "  color: var(--theme-text);",
                "  background-color: var(--theme-background);",
                "}"
            ])
            
            # Heading defaults
            css_output.extend([
                "",
                "h1, h2, h3, h4, h5, h6 {",
                "  font-family: var(--theme-font-heading);",
                "  font-weight: var(--theme-font-weight-bold);",
                "}"
            ])
            
            # RTL support
            if theme.rtl_support:
                css_output.extend([
                    "",
                    "/* RTL support */",
                    "[dir='rtl'] {",
                    "  text-align: right;",
                    "}",
                    "",
                    "[dir='rtl'] .float-left {",
                    "  float: right !important;",
                    "}",
                    "",
                    "[dir='rtl'] .float-right {",
                    "  float: left !important;",
                    "}"
                ])
            
            # High contrast support
            if theme.supports_high_contrast:
                css_output.extend([
                    "",
                    "@media (prefers-contrast: high) {",
                    "  :root {",
                    "    --theme-border-width: 2px;",
                    "    --theme-focus-ring-width: 0.5rem;",
                    "  }",
                    "  ",
                    "  .btn, .form-control, .card {",
                    "    border-width: var(--theme-border-width);",
                    "  }",
                    "}"
                ])
            
            # Dark mode support
            if theme.supports_dark_mode:
                if theme.mode == 'dark':
                    # Force dark mode - override root variables
                    css_output.extend([
                        "",
                        "/* Force dark mode */",
                        ":root {",
                        f"  --theme-primary: {theme.primary_color_dark or theme.primary_color};",
                        f"  --theme-secondary: {theme.secondary_color_dark or theme.secondary_color};",
                        f"  --theme-success: {theme.success_color_dark or theme.success_color};",
                        f"  --theme-warning: {theme.warning_color_dark or theme.warning_color};",
                        f"  --theme-danger: {theme.danger_color_dark or theme.danger_color};",
                        f"  --theme-info: {theme.info_color_dark or theme.info_color};",
                        f"  --theme-background: {theme.background_color_dark or theme.background_color};",
                        f"  --theme-surface: {theme.surface_color_dark or theme.surface_color};",
                        f"  --theme-text: {theme.text_color_dark or theme.text_color};",
                        f"  --theme-text-muted: {theme.text_muted_color_dark or theme.text_muted_color};",
                        f"  --theme-border-color: {theme.border_color_dark or theme.border_color};",
                        "}"
                    ])
                elif theme.mode == 'auto':
                    # Auto mode with manual override support
                    css_output.extend([
                        "",
                        "/* Auto dark mode (only when no manual theme is set) */",
                        "@media (prefers-color-scheme: dark) {",
                        "  :root:not([data-theme]) {",
                        f"    --theme-primary: {theme.primary_color_dark or theme.primary_color};",
                        f"    --theme-secondary: {theme.secondary_color_dark or theme.secondary_color};",
                        f"    --theme-success: {theme.success_color_dark or theme.success_color};",
                        f"    --theme-warning: {theme.warning_color_dark or theme.warning_color};",
                        f"    --theme-danger: {theme.danger_color_dark or theme.danger_color};",
                        f"    --theme-info: {theme.info_color_dark or theme.info_color};",
                        f"    --theme-background: {theme.background_color_dark or theme.background_color};",
                        f"    --theme-surface: {theme.surface_color_dark or theme.surface_color};",
                        f"    --theme-text: {theme.text_color_dark or theme.text_color};",
                        f"    --theme-text-muted: {theme.text_muted_color_dark or theme.text_muted_color};",
                        f"    --theme-border-color: {theme.border_color_dark or theme.border_color};",
                        "  }",
                        "}",
                        "",
                        "/* Manual dark theme override */",
                        ":root[data-theme=\"dark\"] {",
                        f"  --theme-primary: {theme.primary_color_dark or theme.primary_color};",
                        f"  --theme-secondary: {theme.secondary_color_dark or theme.secondary_color};",
                        f"  --theme-success: {theme.success_color_dark or theme.success_color};",
                        f"  --theme-warning: {theme.warning_color_dark or theme.warning_color};",
                        f"  --theme-danger: {theme.danger_color_dark or theme.danger_color};",
                        f"  --theme-info: {theme.info_color_dark or theme.info_color};",
                        f"  --theme-background: {theme.background_color_dark or theme.background_color};",
                        f"  --theme-surface: {theme.surface_color_dark or theme.surface_color};",
                        f"  --theme-text: {theme.text_color_dark or theme.text_color};",
                        f"  --theme-text-muted: {theme.text_muted_color_dark or theme.text_muted_color};",
                        f"  --theme-border-color: {theme.border_color_dark or theme.border_color};",
                        "}",
                        "",
                        "/* Manual light theme override */",
                        ":root[data-theme=\"light\"] {",
                        f"  --theme-primary: {theme.primary_color};",
                        f"  --theme-secondary: {theme.secondary_color};",
                        f"  --theme-success: {theme.success_color};",
                        f"  --theme-warning: {theme.warning_color};",
                        f"  --theme-danger: {theme.danger_color};",
                        f"  --theme-info: {theme.info_color};",
                        f"  --theme-background: {theme.background_color};",
                        f"  --theme-surface: {theme.surface_color};",
                        f"  --theme-text: {theme.text_color};",
                        f"  --theme-text-muted: {theme.text_muted_color};",
                        f"  --theme-border-color: {theme.border_color};",
                        "}"
                    ])
            
            # Animation controls
            if not theme.enable_animations:
                css_output.extend([
                    "",
                    "/* Disable animations */",
                    "*, *::before, *::after {",
                    "  animation-duration: 0s !important;",
                    "  animation-delay: 0s !important;",
                    "}"
                ])
                
            if not theme.enable_transitions:
                css_output.extend([
                    "",
                    "/* Disable transitions */", 
                    "*, *::before, *::after {",
                    "  transition-duration: 0s !important;",
                    "  transition-delay: 0s !important;",
                    "}"
                ])
            
            # Add custom CSS if present
            if theme.custom_css:
                css_output.extend([
                    "",
                    "/* Custom theme CSS */",
                    theme.custom_css.strip()
                ])
            
            return Markup("\n".join(css_output))
            
        except Exception as e:
            return f"/* Error generating theme CSS: {e} */"