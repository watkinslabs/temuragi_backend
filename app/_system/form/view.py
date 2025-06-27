from flask import Blueprint, render_template_string, g, abort, request
from app.classes import TemplateRenderer
import logging

# Create blueprint with m/ prefix
bp = Blueprint('forms', __name__, url_prefix='/f')

# Set up logging
logger = logging.getLogger(__name__)




@bp.route('<slug>/list', methods=['GET', 'POST'])
def render_dynamic_list(slug):
    """
    Dynamically render any page based on the URL slug.
    Handles both GET and POST requests for forms.
    """
    try:
        # Get database session from Flask g context
        session = g.session
        slug="f/"+slug.lower()+"/list"
        logger.info(f"Rendering page with slug: {slug}")
        
        print(f"Successfully rendered page: {slug}")
        
        # Create template renderer
        renderer = TemplateRenderer(session)
        rendered_content = renderer.render_page(slug)

        
        logger.info(f"Successfully rendered page: {slug}")
        return rendered_content
        
    except Exception as e:
        logger.error(f"Error rendering page '{slug}': {str(e)}", exc_info=True)
        
        # In production, you might want to show a generic error page
        # For development, show detailed error
        if g.get('debug', False):
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error - Page Not Found</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .error-container {{
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #d32f2f;
                        margin-bottom: 20px;
                    }}
                    .error-details {{
                        background: #f5f5f5;
                        padding: 15px;
                        border-radius: 4px;
                        margin-top: 20px;
                        font-family: monospace;
                        font-size: 14px;
                        overflow-x: auto;
                    }}
                    .back-link {{
                        margin-top: 20px;
                        display: inline-block;4
                        color: #1976d2;
                        text-decoration: none;
                    }}
                    .back-link:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1>Error Rendering Page</h1>
                    <p><strong>Requested URL:</strong> /m/{slug}</p>
                    <p><strong>Error Type:</strong> {type(e).__name__}</p>
                    <p><strong>Error Message:</strong> {str(e)}</p>
                    <div class="error-details">
                        <pre>{repr(e)}</pre>
                    </div>
                    <a href="/" class="back-link">← Back to Home</a>
                </div>
            </body>
            </html>
            """
        else:
            # Production error page
            abort(500, description="Internal server error")


@bp.route('<slug>/manage', methods=['POST'])
def render_dynamic_manage(slug):
    """
    Dynamically render any page based on the URL slug.
    Handles both GET and POST requests for forms.
    """
    try:
        # Get database session from Flask g context
        session = g.session
        slug="f/"+slug.lower()+"/manage"
        logger.info(f"Rendering page with slug: {slug}")
        try:
            data = request.get_json()
        except:
            data=None
            pass
        
        
        # Create template renderer
        renderer = TemplateRenderer(session)
        if data:
            rendered_content = renderer.render_page(slug,id=data['id'])
        else:

            rendered_content = renderer.render_page(slug)

        
        logger.info(f"Successfully rendered page: {slug}")
        return rendered_content
        
    except Exception as e:
        logger.error(f"Error rendering page '{slug}': {str(e)}", exc_info=True)
        
        # In production, you might want to show a generic error page
        # For development, show detailed error
        if g.get('debug', False):
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error - Page Not Found</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .error-container {{
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #d32f2f;
                        margin-bottom: 20px;
                    }}
                    .error-details {{
                        background: #f5f5f5;
                        padding: 15px;
                        border-radius: 4px;
                        margin-top: 20px;
                        font-family: monospace;
                        font-size: 14px;
                        overflow-x: auto;
                    }}
                    .back-link {{
                        margin-top: 20px;
                        display: inline-block;4
                        color: #1976d2;
                        text-decoration: none;
                    }}
                    .back-link:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1>Error Rendering Page</h1>
                    <p><strong>Requested URL:</strong> /m/{slug}</p>
                    <p><strong>Error Type:</strong> {type(e).__name__}</p>
                    <p><strong>Error Message:</strong> {str(e)}</p>
                    <div class="error-details">
                        <pre>{repr(e)}</pre>
                    </div>
                    <a href="/" class="back-link">← Back to Home</a>
                </div>
            </body>
            </html>
            """
        else:
            # Production error page
            abort(500, description="Internal server error")
