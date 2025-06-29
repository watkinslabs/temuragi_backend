import logging
from jinja2 import Environment as JinjaEnvironment, BaseLoader, TemplateNotFound, pass_context
from flask import current_app, has_app_context, request, g


# Place this class definition above your TemplateRenderer class
class ContextWrapper:
    """
    A smart wrapper for the template context that allows dot-notation
    for list indices without breaking any other functionality.
    """
    __depends_on__=[]
    
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        """
        This makes the wrapper behave like a dictionary for Jinja's lookups.
        """
        return self._data[key]

    def __getattr__(self, name):
        """
        This is called by Jinja for dot-notation access.
        """
        # First, try to access it like a dictionary key
        if isinstance(self._data, dict) and name in self._data:
            return self._data[name]

        # If that fails, check if we are accessing a list by index
        if name.isdigit() and isinstance(self._data, (list, tuple)):
            try:
                return self._data[int(name)]
            except IndexError:
                # This is the correct way to tell Jinja the attribute is missing
                raise AttributeError

        # Finally, try to get it as a regular object attribute
        return getattr(self._data, name)
  

class ContextAwareEnvironment(JinjaEnvironment):
    __depends_on__=[]
    
    def __init__(self, renderer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._renderer = renderer
        self._context_renderer = renderer

        self.original_getattr = super().getattr
        self.getattr = self._custom_getattr

    def make_context(self, vars_=None, shared=False, locals_=None):
        """Override to inject Flask context processors"""
        context = super().make_context(vars_, shared, locals_)
        
        # Debug logging
        #print("=== MAKE CONTEXT CALLED ===")
        
        if has_app_context():
            processors = current_app.template_context_processors.get(None, [])
            
            for func in processors:
                data = func()
                context.vars.update(data)
        
        return context

    def _custom_getattr(self, obj, attribute):
        """
        Custom getattr that handles numeric list access and falls back
        to the original method for everything else.
        """
        if isinstance(attribute, str) and attribute.isdigit() and isinstance(obj, (list, tuple)):
            try:
                return obj[int(attribute)]
            except IndexError:
                pass

        return self.original_getattr(obj, attribute)

    def get_template(self, name, parent=None, globals=None):
        """Override to include Flask globals and context processors"""
        # Your existing logic
        if not name or not isinstance(name, str):
            raise TemplateNotFound(name)

        if ':' not in name:
            ctx = self._renderer._get_current_context()
            if ctx:
                if ctx['type'] == 'template':
                    name = f"template_fragment:{ctx['id']}:{name}"
                elif ctx['type'] == 'page':
                    name = f"page_fragment:{ctx['id']}:{name}"
        
        # Get the template
        template = super().get_template(name, parent, globals)
        
        # Inject Flask's context processors into the template module
        if has_app_context():
            # Create a new module with Flask's context
            def get_flask_context():
                ctx = {}
                for func in current_app.template_context_processors[None]:
                    ctx.update(func())
                return ctx
            
            # Monkey patch the template module to include Flask context
            original_root_render = template.root_render_func
            
            def wrapped_root_render(context):
                # Inject Flask context processors
                flask_ctx = get_flask_context()
                context.vars.update(flask_ctx)
                return original_root_render(context)
            
            template.root_render_func = wrapped_root_render
        
        return template
    

class DbLoader(BaseLoader):
    __depends_on__=[]
    
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
        #self._logger.debug(f"get_source: {template}")

        parts = template.split(':')
        if len(parts) != 3:
            raise TemplateNotFound(template)

        fragment_type, id, fragment_key = parts

        renderer = getattr(environment, "_context_renderer", None)
        if renderer:
            renderer._push_context(fragment_type.replace('_fragment', ''), id, fragment_key)

        # --- Import models needed for the type check ---
        from app.models import PageFragment, TemplateFragment

        if fragment_type == 'template_fragment':
            fragment = TemplateFragment.get_active_by_key(self.session, id, fragment_key)
        elif fragment_type == 'page_fragment':
            fragment = PageFragment.get_active_by_key(self.session, id, fragment_key)
        else:
            raise TemplateNotFound(template)

        if not fragment:
            raise TemplateNotFound(template)

        is_template_fragment = isinstance(fragment, TemplateFragment)

        if is_template_fragment:
            source = fragment.template_source
        else:
            # Fallback logic for PageFragment, etc.
            source = getattr(fragment, 'template_source', None) or fragment.content_source

        def uptodate():
            current_fragment = type(fragment).get_active_by_key(self.session, id, fragment_key)
            if not current_fragment:
                return False

            if is_template_fragment:
                # TemplateFragment only has a template_hash
                current_hash = getattr(current_fragment, 'template_hash', None)
                original_hash = getattr(fragment, 'template_hash', None)
            else:
                # PageFragment logic
                current_hash = getattr(current_fragment, 'template_hash', None) or getattr(current_fragment, 'content_hash', None)
                original_hash = getattr(fragment, 'template_hash', None) or getattr(fragment, 'content_hash', None)

            if original_hash is None:
                return current_hash is None
                
            return current_hash == original_hash

        return source, template, uptodate

class TemplateRenderer:
    """Dynamic template render engine for Flask"""
    __depends_on__ = ['ContextAwareEnvironment', 'DbLoader', 'MenuBuilder','Template', 'TemplateFragment','Page','PageFragment']

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
            


            
            original_compile = self._jinja_env.compile_expression
            
            def custom_compile(source, undefined_to_none=True):
                # Handle import statements for database templates
                if 'import' in source:
                    # Let Jinja2 handle it normally - our loader will resolve the path
                    pass
                return original_compile(source, undefined_to_none)
            
            self._jinja_env.compile_expression = custom_compile
            
            @pass_context
            def context_include_wrapper(context, fragment_key, **kwargs):
                # build the template name exactly as before
                template_name = f"template_fragment:{ context.get('page')['id'] }:{ fragment_key }"
                tpl = context.environment.get_template(template_name)

                # merge Jinja context + any overrides
                merged = context.get_all()
                merged.update(kwargs)

                # **use the Template's new_context**, not env.new_context**
                subctx = tpl.new_context(merged)

                # render with root_render_func to keep Jinja's dot‐lookup logic
                return tpl.root_render_func(subctx)

            self._jinja_env.globals['include'] = context_include_wrapper

            self._jinja_env.globals['include_page_fragment'] = self._include_fragment
            self._jinja_env.globals['include_template_fragment'] = self._include_template_fragment
            self._jinja_env.globals['theme_css'] = lambda theme_id_or_name=None: self.theme_css(self.session, theme_id_or_name)
            self._jinja_env.globals['get_flashed_messages'] = self._get_flashed_messages
            self._jinja_env.globals['url_for'] = self._url_for
            self._jinja_env.globals['model_url'] = self._model_url
            self._jinja_env.globals['render_menu'] = self._render_menu

        return self._jinja_env

    def _model_url(self,endpoint):

        model,action=endpoint.split('.')
        action2='home'
        if action=='list':
            action2='list'
        elif action=='manage':
            action2='manage'
        elif action=='edit':
            action2='manage'
        elif action=='create':
            action2='manage'

        return f"/v2/f/{model}/{action2}"
    

    def _url_for(self, endpoint, _external=False, _anchor=None, **values):
        """
        Safe wrapper around Flask's url_for that returns /not_found on error.
        """
        from flask import url_for
        from werkzeug.routing import BuildError
        
        try:
            return url_for(endpoint, _external=_external, _anchor=_anchor, **values)
        except BuildError:
            self._logger.error(f"url_for failed: Endpoint '{endpoint}' not found")
            return "/not_found"
        except Exception as e:
            # Some other error
            self._logger.error(f"url_for failed for '{endpoint}': {type(e).__name__}: {e}")
            return "/not_found"
    
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
    
    def _context_include(self, context, fragment_key, **kwargs):
        """Context-aware include that passes template context to fragments"""
        current = self._get_current_context()
        if not current:
            raise TemplateNotFound(fragment_key)
        
        
        # Extract variables from Jinja2 context
        merged_context = {}
        
        # Jinja2 context has a different structure
        if hasattr(context, 'get_all'):
            # This gets all variables including inherited ones
            merged_context = context.get_all()
        elif hasattr(context, 'parent'):
            # Manual extraction for older Jinja2 versions
            if context.parent:
                merged_context.update(context.parent)
            if hasattr(context, 'vars'):
                merged_context.update(context.vars)
        else:
            # Fallback - try to use it as dict
            try:
                merged_context = dict(context)
            except:
                self._logger.error(f"Could not extract context variables from {type(context)}")
        
        # Add passed kwargs on top
        merged_context.update(kwargs)
        
        
        if current['type'] == 'template':
            return self._include_template_fragment(current['id'], fragment_key, **merged_context)
        if current['type'] == 'page':
            return self._include_fragment(current['id'], fragment_key, **merged_context)
        
        raise TemplateNotFound(fragment_key)

    def _push_context(self, context_type, id, fragment_key=None):
        """Push rendering context onto stack"""
        context = {
            'type': context_type,
            'id': id,
            'fragment_key': fragment_key
        }
        self._context_stack.append(context)
    
    def _pop_context(self):
        """Pop rendering context from stack"""
        if self._context_stack:
            context = self._context_stack.pop()
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
    
    def _include_fragment(self, target_id, fragment_key, **kwargs):
        """Context-aware fragment include - works for both page and template fragments"""
        self._check_recursion()
        
        current_context = self._get_current_context()
        
        # If we're in a template fragment context, try template fragment first
        if current_context and current_context['type'] == 'template':
            template_id = current_context['id']
            try:
                result = self._include_template_fragment(template_id, fragment_key, **kwargs)
                self._recursion_depth -= 1
                return result
            except TemplateNotFound:
                self._logger.debug(f"Template fragment not found, trying page fragment")
        
        # Default or fallback: try page fragment
        from app.models import PageFragment
        fragment = PageFragment.get_active_by_key(self.session, target_id, fragment_key)
        
        if not fragment:
            #self._logger.warning(f"Page fragment not found: {target_id}:{fragment_key}")
            self._recursion_depth -= 1
            return ""
        
        # Push page fragment context
        self._push_context('page', target_id, fragment_key)
        
        try:
            # If fragment has template_fragment_key, use template rendering
            if fragment.template_fragment_key:
                # Get the page's template for template fragment lookup
                from app.models import Page
                page = self.session.query(Page).filter_by(id=target_id).first()
                if page and page.template_id:
                    template_name = f"template_fragment:{page.template_id}:{fragment.template_fragment_key}"
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
    
    def _include_template_fragment(self, template_id, fragment_key, **kwargs):
        """Include a template fragment with passed context"""
        self._check_recursion()
        
        
        # Push template fragment context
        self._push_context('template', template_id, fragment_key)
        
        try:
            template_name = f"template_fragment:{template_id}:{fragment_key}"
            template = self.jinja_env.get_template(template_name)
            
            # Use the passed context directly - it already includes parent context
            result = template.render(**kwargs)
            return result
        except TemplateNotFound:
            self._logger.warning(f"Template fragment not found: {template_id}:{fragment_key}")
            return ""
        finally:
            self._pop_context()
            self._recursion_depth -= 1
            
    
    def _load_page(self, page_identifier):
        """Load and validate page by UUID or slug"""
        from app.models import Page
        import uuid
        
        # Check if it's a valid UUID
        try:
            # If it's a valid UUID string, use it as UUID
            page_id = uuid.UUID(str(page_identifier))
            page = self.session.query(Page).filter_by(id=page_id).first()
        except ValueError:
            # Not a UUID, treat as slug
            page = self.session.query(Page).filter_by(slug=page_identifier).first()
        
        if not page:
            raise ValueError(f"Page not found: {page_identifier}")
        
        if not page.is_visible():
            raise ValueError(f"Page not visible: {page_identifier}")
        
        return page

    
    def _load_template(self, template_id):
        """Load template"""
        from app.models import Template
        template = self.session.query(Template).filter_by(id=template_id).first()
        
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        return template
    
    def _load_theme(self, theme_id):
        """Load theme"""
        from app.models import Theme
        theme = self.session.query(Theme).filter_by(id=theme_id).first()
        
        if not theme:
            raise ValueError(f"Theme not found: {theme_id}")
        
        return theme
    
    def _build_context(self, page, template, theme, **data):
        """Build render context with proper data separation"""
        context = {}
        
        # Add passed data at root level
        context.update(data)
        
        # Add page object (read-write for page/fragments)
        context['page'] = {
            'id': str(page.id),
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
                'id': str(theme.id),
                'name': theme.name,
                'display_name': theme.display_name,
                'description': theme.description,
                # Add other theme properties as needed
            }
        
        return context
    
    def _create_extended_template(self, page_id, page_template, theme_template):
        """Create a template that extends template base with page fragments"""
        from app.models import PageFragment, TemplateFragment
        
        # Get template base fragment
        template_base = None
        if page_template:
            template_base = TemplateFragment.get_active_by_key(
                self.session, page_template.id, 'base'
            )
        
        if not template_base and theme_template:
            template_base = TemplateFragment.get_active_by_key(
                self.session, theme_template.id, 'base'
            )
        
        if not template_base:
            raise ValueError("No base template found")
        
        # Get all active page fragments
        page_fragments = PageFragment.get_all_active_for_page(self.session, page_id)
        
        # Build extended template source
        extends_line = f"template_fragment:{template_base.template_id}:base"
        
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
    
    def _render_page_fragments_only(self, page_id, context):
        """Render only page fragments without base template"""
        from app.models import PageFragment
        import re
        
        # Get all active page fragments
        page_fragments = PageFragment.get_all_active_for_page(self.session, page_id)
        
        # Build content template
        content_parts = []
        for fragment in page_fragments:
            content = fragment.content_source.strip()
            
            # If content has {% block %} declarations, extract the content
            if '{% block content %}' in content:
                # Extract content between block tags
                match = re.search(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            
            content_parts.append(content)
        
        # Combine and render
        content_template_source = "\n".join(content_parts)
        template = self.jinja_env.from_string(content_template_source)
        return template.render(**context)
    
    
    def render_page(self, page_identifier, **kwargs):
        """Alias for render_template for backward compatibility"""
        return self.render_template(page_identifier, **kwargs)

    def render_template(self, page_identifier, fragment_only=None, **data):
        """Main render function with htmx support"""
        #self._logger.info(f"Rendering page: {page_identifier}")
        self._reset_recursion()
        self._context_stack = []  # Clear context stack
        
        try:
            # Load page
            page = self._load_page(page_identifier)
            
            # Push initial page context
            self._push_context('page', str(page.id))
            
            # Determine if we should render fragments only
            if fragment_only is None:
                # Auto-detect from request header
                fragment_only = request.headers.get('HX-Request') == 'true'
            
            # Load page template
            page_template = None
            if page.template_id:
                page_template = self._load_template(page.template_id)
            
            # Load theme template
            theme_template = None
            theme = None
            if page_template and page_template.theme_id:
                theme = self._load_theme(page_template.theme_id)
                # Assume theme has a default template or get from theme.default_template_id
                if hasattr(theme, 'default_template_id') and theme.default_template_id:
                    theme_template = self._load_template(theme.default_template_id)
            
            # Build context
            context = self._build_context(page, page_template, theme, **data)
            context['is_htmx_request'] = fragment_only
            
            if fragment_only:
                # Render only fragments for htmx requests
                rendered_content = self._render_page_fragments_only(str(page.id), context)
            else:
                # Create extended template with auto-extension
                extended_template_source = self._create_extended_template(str(page.id), page_template, theme_template)
                
                # Render the extended template
                template = self.jinja_env.from_string(extended_template_source)
                rendered_content = template.render(**context)
            
            # Increment view count
            page.increment_view_count(self.session)

            # Apply theme's HTML compression settings if theme exists
            if theme and any([theme.consolidate_css, theme.consolidate_js, 
                            theme.minify_css, theme.minify_js, theme.minify_html]):
                from app.classes import HTMLCompressor
                compressor = HTMLCompressor()
                rendered_content = compressor.clean_html(
                    rendered_content,
                    consolidate_css=theme.consolidate_css,
                    consolidate_js=theme.consolidate_js,
                    minify_css=theme.minify_css,
                    minify_js=theme.minify_js,
                    minify_html=theme.minify_html)


            #self._logger.info(f"Successfully rendered page: {page.slug}")
            return rendered_content
            
        except Exception as e:
            self._logger.error(f"Failed to render page {page_identifier}: {e}")
            raise
        finally:
            self._context_stack = []  # Clean up context stack

    def theme_css(self, session, theme_id_or_name=None):
        """
        Generate complete CSS for a theme including variables and custom styles.
        Can be called in templates like {{ theme_css() }}
        
        Args:
            session: SQLAlchemy session
            theme_id_or_name: Theme UUID string, name, or None for default theme
            
        Returns:
            Complete CSS as a string ready for <style> block
        """
        try:
            from app.models import Theme
            from sqlalchemy import or_
            from markupsafe import Markup
            
            # Get the theme
            theme = None
            if theme_id_or_name:
                theme = session.query(Theme).filter(
                    or_(
                        Theme.id == theme_id_or_name,
                        Theme.name == theme_id_or_name
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
                f"--theme-border-color: {theme.border_color};",
                f"--theme-content-area: {theme.content_area_color};",
                f"--theme-sidebar: {theme.sidebar_color};",
                f"--theme-component: {theme.component_color};"
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
                    f"--theme-border-color-dark: {theme.border_color_dark or theme.border_color};",
                    f"--theme-content-area-dark: {theme.content_area_color_dark or theme.content_area_color};",
                    f"--theme-sidebar-dark: {theme.sidebar_color_dark or theme.sidebar_color};",
                    f"--theme-component-dark: {theme.component_color_dark or theme.component_color};"
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
                f"--theme-footer-height: {theme.footer_height};",
                f"--theme-breadcrumb-height: {theme.breadcrumb_height};",
                f"--theme-topbar-height: {theme.topbar_height};"
            ])
            
            # Parse JSON CSS variables if they exist
            if theme.css_variables:
                try:
                    import json
                    # Ensure it's a string before parsing
                    if isinstance(theme.css_variables, str) and theme.css_variables.strip():
                        custom_vars = json.loads(theme.css_variables)
                        # Ensure we got a dict
                        if isinstance(custom_vars, dict):
                            for key, value in custom_vars.items():
                                # Ensure key and value are strings
                                key = str(key)
                                value = str(value)
                                if not key.startswith('--'):
                                    key = f"--{key}"
                                css_vars.append(f"{key}: {value};")
                except Exception as e:
                    # Log but don't fail
                    self._logger.warning(f"Failed to parse theme CSS variables: {e}")
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
                        f"  --theme-content-area: {theme.content_area_color_dark or theme.content_area_color};",
                        f"  --theme-sidebar: {theme.sidebar_color_dark or theme.sidebar_color};",
                        f"  --theme-component: {theme.component_color_dark or theme.component_color};",
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
                        f"    --theme-content-area: {theme.content_area_color_dark or theme.content_area_color};",
                        f"    --theme-sidebar: {theme.sidebar_color_dark or theme.sidebar_color};",
                        f"    --theme-component: {theme.component_color_dark or theme.component_color};",
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
                        f"  --theme-content-area: {theme.content_area_color_dark or theme.content_area_color};",
                        f"  --theme-sidebar: {theme.sidebar_color_dark or theme.sidebar_color};",
                        f"  --theme-component: {theme.component_color_dark or theme.component_color};",
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
                        f"  --theme-content-area: {theme.content_area_color};",
                        f"  --theme-sidebar: {theme.sidebar_color};",
                        f"  --theme-component: {theme.component_color};",
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

    def _render_menu(self, menu_name='ADMIN', user_id=None, **kwargs):
        """
        Render menu directly in templates using {{ render_menu('ADMIN') }}
        """
        from app.classes import MenuBuilder
        from app.models import Template, TemplateFragment
        from markupsafe import Markup
        
        try:
            # Save current context state
            saved_context_stack = self._context_stack.copy()
            saved_recursion_depth = self._recursion_depth
            
            # Get menu structure
            menu_builder = MenuBuilder(self.session)
            menu_structure = menu_builder.get_menu_structure(menu_name, user_id)
            
            if not menu_structure:
                return Markup(f"<!-- Menu '{menu_name}' not found -->")
         

            # Try to find a template for this menu type
            template_name = f"menu_{menu_name.lower()}"
            template = self.session.query(Template).filter_by(name=template_name).first()
            
            # Fallback to generic sidebar_menu template
            if not template:
                template = self.session.query(Template).filter_by(name='sidebar_menu').first()
            if template:
                # Push menu template context
                self._push_context('template', template.id, 'base')
                
                try:
                    # Use the template fragment system with context
                    template_name = f"template_fragment:{template.id}:base"
                    template_obj = self.jinja_env.get_template(template_name)
                    render_context = {
                        'menu': menu_structure,
                        'menu_name': menu_name,
                        'template_id': str(template.id),
                        **kwargs
                    }

                    # option A: use generate (returns a generator of text chunks)
                    html = ''.join(template_obj.generate(**render_context))
                    return Markup(html)

                    
                finally:
                    self._pop_context()
            
            # Fallback to simple rendering
            return Markup(menu_builder.render_menu(menu_structure, **kwargs))
            
        except Exception as e:
            self._logger.error(f"Error rendering menu '{menu_name}': {e}", exc_info=True)
            return Markup(f"<!-- Error rendering menu: {e} -->")
        finally:
            # Restore context state
            self._context_stack = saved_context_stack
            self._recursion_depth = saved_recursion_depth
            
def render_template(page_identifier, **data):
    """Convenience function for rendering templates"""
    
    session = g.session
    try:
        engine = TemplateRenderer(session)
        return engine.render_template(page_identifier, **data)
    finally:
        session.close()