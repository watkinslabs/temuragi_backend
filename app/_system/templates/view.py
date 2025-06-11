from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from uuid import UUID
import logging
from typing import Optional

from app.classes import TemplateRenderer


bp = Blueprint('theme', __name__, url_prefix='/theme')
logger = logging.getLogger(__name__)


#def get_service():
#    """Get template engine service with current session"""
#    from .template_service import TemplateService
#    return TemplateService(get_db_session(), logger)

#    db_session = g.session


@bp.route('/')
def test_page():
        session = g.session
        
        renderer = TemplateRenderer(session)
        #service = get_service()
        #stats = service.get_dashboard_stats()
        
        from app.models import Page
        page = session.query(Page).filter_by(slug='test').first()


        rendered_content = renderer.render_page(page.uuid)
        return rendered_content
        
