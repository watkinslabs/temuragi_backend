import logging
from jinja2 import Environment as JinjaEnvironment, BaseLoader, TemplateNotFound
from flask import current_app, has_app_context


class ContextAwareEnvironment(JinjaEnvironment):
    def __init__(self, renderer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._renderer = renderer
        self._context_renderer = renderer

    def get_template(self, name, parent=None, globals=None):
        if not name or not isinstance(name, str):
            raise TemplateNotFound(name)

        if ':' not in name:
            ctx = self._renderer._get_current_context()
            if ctx:
                if ctx['type'] == 'template':
                    name = f"template_fragment:{ctx['uuid']}:{name}"
                elif ctx['type'] == 'page':
                    name = f"page_fragment:{ctx['uuid']}:{name}"

        return super().get_template(name, parent, globals)


class DbLoader(BaseLoader):
    def __init__(self, session):
        self.session = session
        self._logger = self._get_logger()
        self._recursion_depth = 0
        self._max_recursion = 5

    @staticmethod
    def _get_logger():
        if has_app_context():
            return current_app.logger
        return logging.getLogger('db_loader')

    def get_source(self, environment, template):
        self._logger.debug(f"get_source: {template}")

        parts = template.split(':')
        if len(parts) != 3:
            raise TemplateNotFound(template)

        fragment_type, uuid, fragment_key = parts

        renderer = getattr(environment, "_context_renderer", None)
        if renderer:
            renderer._push_context(fragment_type.replace('_fragment', ''), uuid, fragment_key)

        if fragment_type == 'template_fragment':
            from app.models import TemplateFragment
            fragment = TemplateFragment.get_active_by_key(self.session, uuid, fragment_key)
        elif fragment_type == 'page_fragment':
            from app.models import PageFragment
            fragment = PageFragment.get_active_by_key(self.session, uuid, fragment_key)
        else:
            raise TemplateNotFound(template)

        if not fragment:
            raise TemplateNotFound(template)

        source = getattr(fragment, 'template_source', None) or fragment.content_source

        def uptodate():
            current_fragment = type(fragment).get_active_by_key(self.session, uuid, fragment_key)
            if not current_fragment:
                return False
            current_hash = getattr(current_fragment, 'template_hash', None) or current_fragment.content_hash
            original_hash = getattr(fragment, 'template_hash', None) or fragment.content_hash
            return current_hash == original_hash

        return source, template, uptodate

class TemplateRenderer:
    """Dynamic template render engine for Flask"""
    __depends_on__ = ['Page', 'Template', 'Theme', 'PageFragment', 'TemplateFragment']

    def __init__(self, session):
        self.session = session
        self._logger = self._get_logger()
        self._jinja_env = None
        self._recursion_depth = 0
        self._max_recursion = 5
        self._context_stack = []
    
    @staticmethod
    def _get_logger():
        if has_app_context():
            return current_app.logger
        else:
            return logging.getLogger('renderer')
    
    @property
    def jinja_env(self):
        """Lazy initialize Jinja2 environment"""
        if self._jinja_env is None:
            loader = DbLoader(self.session)
            self._jinja_env = ContextAwareEnvironment(
                    renderer=self,
                    loader=loader,
                    autoescape=True
                )
            
            # Register custom functions
            self._jinja_env.globals['include'] = self._context_include
            self._jinja_env.globals['include_page_fragment'] = self._include_fragment
            self._jinja_env.globals['include_template_fragment'] = self._include_template_fragment
            self._jinja_env.globals['theme_css'] = lambda theme_uuid_or_name=None: self.theme_css(self.session, theme_uuid_or_name)
            self._jinja_env.globals['get_flashed_messages'] = self._get_flashed_messages
            self._jinja_env.globals['url_for'] = self._url_for
            self._jinja_env.globals['render_menu'] = self._render_menu

        return self._jinja_env

    def _url_for(self, endpoint, **values):
        """
        Generate URL for the given endpoint with the method provided.
        Wrapper around Flask's url_for.
        """
        from flask import url_for
        return url_for(endpoint, **values)
    
    def _get_flashed_messages(self, with_categories=False, category_filter=()):
            """
            Get flashed messages from Flask session.
            Mimics Flask's get_flashed_messages functionality.
            """
            from flask import session
            
            flashes = session.pop('_flashes', [])
            
            if category_filter:
                # Filter by categories if specified
                flashes = [f for f in flashes if f[0] in category_filter]
            
            if with_categories:
                # Return tuples of (category, message)
                return flashes
            else:
                # Return just the messages
                return [f[1] for f in flashes]    
    def _context_include(self, fragment_key, **kwargs):
        for i in range(0,100):
            print("CONTEXT")
        current = self._get_current_context()
        if not current:
            return "NO"
            raise TemplateNotFound(fragment_key)
        print(current['type'],fragment_key)
        if current['type'] == 'template':
            return "NOOOO"
            return self._include_template_fragment(current['uuid'], fragment_key, **kwargs)
        elif current['type'] == 'page':
            return "NOPE"
            return self._include_fragment(current['uuid'], fragment_key, **kwargs)
        
        raise TemplateNotFound(fragment_key)

    def _push_context(self, context_type, uuid, fragment_key=None):
        """Push rendering context onto stack"""
        context = {
            'type': context_type,
            'uuid': uuid,
            'fragment_key': fragment_key
        }
        self._context_stack.append(context)
        self._logger.debug(f"Pushed context: {context}")
    
    def _pop_context(self):
        """Pop rendering context from stack"""
        if self._context_stack:
            context = self._context_stack.pop()
            self._logger.debug(f"Popped context: {context}")
            return context
        return None
    
    def _get_current_context(self):
        """Get current rendering context"""
        return self._context_stack[-1] if self._context_stack else None
    
    def _check_recursion(self):
        """Check and increment recursion depth"""
        self._recursion_depth += 1
        if self._recursion_depth > self._max_recursion:
            raise RecursionError(f"Template recursion exceeded maximum depth of {self._max_recursion}")
    
    def _reset_recursion(self):
        """Reset recursion counter"""
        self._recursion_depth = 0
    
    def _include_fragment(self, target_uuid, fragment_key, **kwargs):
        """Context-aware fragment include - works for both page and template fragments"""
        self._check_recursion()
        
        current_context = self._get_current_context()
        self._logger.debug(f"Including fragment {target_uuid}:{fragment_key} from context {current_context}")
        
        # If we're in a template fragment context, try template fragment first
        if current_context and current_context['type'] == 'template':
            template_uuid = current_context['uuid']
            try:
                result = self._include_template_fragment(template_uuid, fragment_key, **kwargs)
                self._recursion_depth -= 1
                return result
            except TemplateNotFound:
                self._logger.debug(f"Template fragment not found, trying page fragment")
        
        # Default or fallback: try page fragment
        from app.models import PageFragment
        fragment = PageFragment.get_active_by_key(self.session, target_uuid, fragment_key)
        
        if not fragment:
            self._logger.warning(f"Page fragment not found: {target_uuid}:{fragment_key}")
            self._recursion_depth -= 1
            return ""
        
        # Push page fragment context
        self._push_context('page', target_uuid, fragment_key)
        
        try:
            # If fragment has template_fragment_key, use template rendering
            if fragment.template_fragment_key:
                # Get the page's template for template fragment lookup
                from app.models import Page
                page = self.session.query(Page).filter_by(uuid=target_uuid).first()
                if page and page.template_uuid:
                    template_name = f"template_fragment:{page.template_uuid}:{fragment.template_fragment_key}"
                    try:
                        template = self.jinja_env.get_template(template_name)
                        # Merge fragment variables with passed kwargs
                        context = fragment.get_variables_data_dict()
                        context.update(kwargs)
                        result = template.render(**context)
                        return result
                    except TemplateNotFound:
                        self._logger.warning(f"Template fragment not found: {fragment.template_fragment_key}")
            
            # Return content source directly
            return fragment.content_source
            
        finally:
            self._pop_context()
            self._recursion_depth -= 1
    
    def _include_template_fragment(self, template_uuid, fragment_key, **kwargs):
        """Include a template fragment"""
        self._check_recursion()
        
        self._logger.debug(f"Including template fragment: {template_uuid}:{fragment_key}")
        
        # Push template fragment context
        self._push_context('template', template_uuid, fragment_key)
        
        try:
            template_name = f"template_fragment:{template_uuid}:{fragment_key}"
            template = self.jinja_env.get_template(template_name)
            result = template.render(**kwargs)
            return result
        except TemplateNotFound:
            self._logger.warning(f"Template fragment not found: {template_uuid}:{fragment_key}")
            return ""
        finally:
            self._pop_context()
            self._recursion_depth -= 1
    
    def _load_page(self, page_uuid):
        """Load and validate page"""
        from app.models import Page
        page = self.session.query(Page).filter_by(uuid=page_uuid).first()
        
        if not page:
            raise ValueError(f"Page not found: {page_uuid}")
        
        if not page.is_visible():
            raise ValueError(f"Page not visible: {page_uuid}")
        
        return page
    
    def _load_template(self, template_uuid):
        """Load template"""
        from app.models import Template
        template = self.session.query(Template).filter_by(uuid=template_uuid).first()
        
        if not template:
            raise ValueError(f"Template not found: {template_uuid}")
        
        return template
    
    def _load_theme(self, theme_uuid):
        """Load theme"""
        from app.models import Theme
        theme = self.session.query(Theme).filter_by(uuid=theme_uuid).first()
        
        if not theme:
            raise ValueError(f"Theme not found: {theme_uuid}")
        
        return theme
    
    def _build_context(self, page, template, theme, **data):
        """Build render context with proper data separation"""
        context = {}
        
        # Add passed data at root level
        context.update(data)
        
        # Add page object (read-write for page/fragments)
        context['page'] = {
            'uuid': str(page.uuid),
            'name': page.name,
            'title': page.title,
            'slug': page.slug,
            'meta_description': page.meta_description,
            'meta_keywords': page.meta_keywords,
            'og_title': page.og_title,
            'og_description': page.og_description,
            'og_image': page.og_image,
            'canonical_url': page.canonical_url,
            'requires_auth': page.requires_auth
        }
        
        # Add template context
        if template:
            context.update(template.get_render_context())
        
        # Add theme object (read-only)
        if theme:
            context['theme'] = {
                'uuid': str(theme.uuid),
                'name': theme.name,
                'display_name': theme.display_name,
                'description': theme.description,
                # Add other theme properties as needed
            }
        
        return context
    
    def _create_extended_template(self, page_uuid, page_template, theme_template):
        """Create a template that extends template base with page fragments"""
        from app.models import PageFragment, TemplateFragment
        
        # Get template base fragment
        template_base = None
        if page_template:
            template_base = TemplateFragment.get_active_by_key(
                self.session, page_template.uuid, 'base'
            )
        
        if not template_base and theme_template:
            template_base = TemplateFragment.get_active_by_key(
                self.session, theme_template.uuid, 'base'
            )
        
        if not template_base:
            raise ValueError("No base template found")
        
        # Get all active page fragments
        page_fragments = PageFragment.get_all_active_for_page(self.session, page_uuid)
        
        # Build extended template source
        extends_line = f"template_fragment:{template_base.template_uuid}:base"
        
        template_source = f"{{% extends '{extends_line}' %}}\n\n"
        
        # Add each page fragment as a block override
        for fragment in page_fragments:
            # Extract block content from fragment content_source
            content = fragment.content_source.strip()
            
            # If content has {% block %} declarations, use them
            if '{% block ' in content:
                template_source += content + "\n\n"
            else:
                # Wrap content in a content block if no blocks defined
                template_source += f"{{% block content %}}\n{content}\n{{% endblock %}}\n\n"
        
        return template_source
    
    def render_page(self, page_uuid, data=None):
        """Alias for render_template for backward compatibility"""
        if data is None:
            data = {}
        return self.render_template(page_uuid, **data)

    def render_template(self, page_uuid, **data):
        """Main render function"""
        self._logger.info(f"Rendering page: {page_uuid}")
        self._reset_recursion()
        self._context_stack = []  # Clear context stack
        
        try:
            # Load page
            page = self._load_page(page_uuid)
            
            # Push initial page context
            self._push_context('page', page_uuid)
            
            # Load page template
            page_template = None
            if page.template_uuid:
                page_template = self._load_template(page.template_uuid)
            
            # Load theme template
            theme_template = None
            theme = None
            if page_template and page_template.theme_uuid:
                theme = self._load_theme(page_template.theme_uuid)
                # Assume theme has a default template or get from theme.default_template_uuid
                if hasattr(theme, 'default_template_uuid') and theme.default_template_uuid:
                    theme_template = self._load_template(theme.default_template_uuid)
            
            # Build context
            context = self._build_context(page, page_template, theme, **data)
            
            # Create extended template with auto-extension
            extended_template_source = self._create_extended_template(page_uuid, page_template, theme_template)
            
            # Render the extended template
            template = self.jinja_env.from_string(extended_template_source)
            rendered_content = template.render(**context)
            
            # Increment view count
            page.increment_view_count(self.session)
            
            self._logger.info(f"Successfully rendered page: {page.slug}")
            return rendered_content
            
        except Exception as e:
            self._logger.error(f"Failed to render page {page_uuid}: {e}")
            raise
        finally:
            self._context_stack = []  # Clean up context stack


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
        

    # Then add this method to the TemplateRenderer class:
    def _render_menu(self, menu_name='ADMIN', user_uuid=None, **kwargs):
        """
        Render menu directly in templates using {{ render_menu('ADMIN') }}
        
        Args:
            menu_name: Name of the menu to render (default: 'ADMIN')
            user_uuid: Optional user UUID for permission filtering
            **kwargs: Additional context variables
        
        Returns:
            Rendered menu HTML
        """
        from app.classes import MenuBuilder
        from app.models import Template, TemplateFragment
        
        try:
            # Get menu structure
            menu_builder = MenuBuilder(self.session)
            menu_structure = menu_builder.get_menu_structure(menu_name, user_uuid)
            
            if not menu_structure:
                return f"<!-- Menu '{menu_name}' not found -->"
            
            # Try to find a template for this menu type
            template_name = f"menu_{menu_name.lower()}"  # e.g., menu_admin, menu_main
            template = self.session.query(Template).filter_by(name=template_name).first()
            
            # Fallback to generic sidebar_menu template
            if not template:
                template = self.session.query(Template).filter_by(name='sidebar_menu').first()
            
            if template:
                # Get base fragment
                base_fragment = TemplateFragment.get_active_by_key(
                    self.session, template.uuid, 'base'
                )
                
                if base_fragment:
                    # Render the fragment with menu structure
                    context = {
                        'menu': menu_structure,
                        'template_uuid': str(template.uuid),
                        **kwargs
                    }
                    
                    # Push template context
                    self._push_context('template', template.uuid)
                    
                    try:
                        template_obj = self.jinja_env.from_string(base_fragment.template_source)
                        return template_obj.render(**context)
                    finally:
                        self._pop_context()
            
            # Fallback to simple rendering
            return menu_builder.render_menu(menu_structure, **kwargs)
            
        except Exception as e:
            self._logger.error(f"Error rendering menu '{menu_name}': {e}")
            return f"<!-- Error rendering menu: {e} -->"        

def render_template(page_uuid, **data):
    """Convenience function for rendering templates"""
    from app.database import get_db_session  # Adjust import as needed
    
    session = get_db_session()
    try:
        engine = TemplateRenderer(session)
        return engine.render_template(page_uuid, **data)
    finally:
        session.close()


