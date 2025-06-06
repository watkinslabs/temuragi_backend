from jinja2 import BaseLoader, TemplateNotFound, Environment
from jinja2.loaders import BaseLoader
from sqlalchemy.orm import sessionmaker

from app.models import PageTemplate,PageTemplateContent

class DatabaseTemplateLoader(BaseLoader):
    """
    Custom Jinja2 loader that loads templates from the database.
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def get_source(self, environment, template):
        """
        Load template source from database.
        
        Args:
            environment: Jinja2 environment
            template: Template name to load
            
        Returns:
            tuple: (source, filename, uptodate_func)
        """
        session = self.session_factory()
        try:
            # First try to find by PageTemplate name
            page_template = session.query(PageTemplate).filter_by(name=template).first()
            
            if page_template:
                # Get active content for this template
                content = session.query(PageTemplateContent).filter_by(
                    page_template_uuid=page_template.uuid,
                    is_active=True
                ).first()
                
                if content:
                    def uptodate():
                        # Check if template is still current
                        current_session = self.session_factory()
                        try:
                            current_content = current_session.query(PageTemplateContent).filter_by(
                                uuid=content.uuid
                            ).first()
                            return current_content and current_content.updated_at == content.updated_at
                        finally:
                            current_session.close()
                    
                    return content.template_content, template, uptodate
            
            # If not found by PageTemplate name, try direct PageTemplateContent lookup
            # This allows templates to reference each other by template name
            direct_content = session.query(PageTemplateContent).join(PageTemplate).filter(
                PageTemplate.name == template,
                PageTemplateContent.is_active == True
            ).first()
            
            if direct_content:
                def uptodate():
                    current_session = self.session_factory()
                    try:
                        current_content = current_session.query(PageTemplateContent).filter_by(
                            uuid=direct_content.uuid
                        ).first()
                        return current_content and current_content.updated_at == direct_content.updated_at
                    finally:
                        current_session.close()
                
                return direct_content.template_content, template, uptodate
            
            raise TemplateNotFound(template)
            
        finally:
            session.close()


def create_database_jinja_environment(session_factory):
    """
    Create a Jinja2 environment with database template loader.
    
    Args:
        session_factory: SQLAlchemy session factory
        
    Returns:
        Environment: Configured Jinja2 environment
    """
    loader = DatabaseTemplateLoader(session_factory)
    env = Environment(loader=loader)
    
    # Add custom filters if needed
    def safe_get(obj, attr, default=''):
        """Safe attribute getter for templates"""
        try:
            return getattr(obj, attr, default)
        except (AttributeError, TypeError):
            return default
    
    env.filters['safe_get'] = safe_get
    
    return env


def render_page_template(session, page_name, **context):
    """
    Render a page template with the given context.
    
    Args:
        session: SQLAlchemy session
        page_name: Name of the page to render
        **context: Additional context variables
        
    Returns:
        str: Rendered HTML content
    """
    # Get page data
    theme, template, page = get_page_data_for_template(session, page_name)
    
    if not all([theme, template, page]):
        raise TemplateNotFound(f"Page '{page_name}' not found or incomplete")
    
    # Create session factory for the loader
    session_factory = sessionmaker(bind=session.bind)
    
    # Create Jinja environment with database loader
    env = create_database_jinja_environment(session_factory)
    
    # Prepare context
    render_context = {
        'theme': theme,
        'template': template,
        'page': page,
        **context
    }
    
    # Get the template content
    template_content = session.query(PageTemplateContent).filter_by(
        page_template_uuid=template.uuid,
        is_active=True
    ).first()
    
    if not template_content:
        raise TemplateNotFound(f"No active content found for template '{template.name}'")
    
    # Load and render the template
    jinja_template = env.get_template(template.name)
    return jinja_template.render(**render_context)


def render_template_by_name(session, template_name, **context):
    """
    Render a template directly by its name.
    
    Args:
        session: SQLAlchemy session
        template_name: Name of the template to render
        **context: Context variables
        
    Returns:
        str: Rendered HTML content
    """
    # Create session factory for the loader
    session_factory = sessionmaker(bind=session.bind)
    
    # Create Jinja environment with database loader
    env = create_database_jinja_environment(session_factory)
    
    # Load and render the template
    jinja_template = env.get_template(template_name)
    return jinja_template.render(**context)


# Flask integration helper
def setup_flask_database_templates(app, session_factory):
    """
    Setup Flask to use database templates.
    
    Args:
        app: Flask application
        session_factory: SQLAlchemy session factory
    """
    # Create custom Jinja environment
    env = create_database_jinja_environment(session_factory)
    
    # Replace Flask's Jinja environment
    app.jinja_env = env
    
    # Add Flask-specific globals and filters
    app.jinja_env.globals.update(
        url_for=app.url_for,
        get_flashed_messages=app.get_flashed_messages,
        config=app.config,
        request=app.request,
        session=app.session,
        g=app.g
    )