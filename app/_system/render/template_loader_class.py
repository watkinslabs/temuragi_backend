import uuid
import logging
import re
from jinja2 import Environment, Undefined, BaseLoader
from jinja2.exceptions import TemplateNotFound
from sqlalchemy.orm import Session
from flask import current_app, has_app_context

from app.classes import  BlockProcessor

class TemplateLoader(BaseLoader):
    """Simple Jinja2 loader that fetches fragments on demand and processes blocks"""

    def __init__(self, session: Session, template_uuid: uuid.UUID, page_uuid: uuid.UUID = None, logger=None):
        self.session = session
        self.template_uuid = template_uuid
        self.page_uuid = page_uuid
        self.logger = logger or self._get_logger()
        self.block_processor = BlockProcessor(session, template_uuid, page_uuid, logger)

    def _get_logger(self):
        """Get logger from Flask app context or create fallback"""
        if has_app_context():
            return current_app.logger
        else:
            # Fallback for CLI usage
            return logging.getLogger('template_loader')

    def get_base_fragment_key(self):
        """Get the fragment_key for the base fragment"""
        try:
            from app.models import TemplateFragment

            base_fragment = self.session.query(TemplateFragment).filter_by(
                template_uuid=self.template_uuid,
                fragment_type='base',
                is_active=True
            ).first()

            if not base_fragment:
                self.logger.error(f"No base fragment found for template {self.template_uuid}")
                raise ValueError(f"No base fragment found for template {self.template_uuid}")

            return base_fragment.fragment_key
        except Exception as e:
            self.logger.error(f"Error getting base fragment: {e}")
            return "base"  # fallback

    def get_source(self, environment, template_name):
        """Load template source from database on demand and process blocks"""
        try:
            from app.models import TemplateFragment

            self.logger.debug(f"Looking for fragment '{template_name}' in template {self.template_uuid}")

            # Query for fragment by fragment_key within this template
            fragment = self.session.query(TemplateFragment).filter_by(
                template_uuid=self.template_uuid,
                fragment_key=template_name,
                is_active=True
            ).first()

            if not fragment:
                # Log available fragments for debugging
                try:
                    all_fragments = self.session.query(TemplateFragment).filter_by(
                        template_uuid=self.template_uuid,
                        is_active=True
                    ).all()
                    available_keys = [f.fragment_key for f in all_fragments]
                    self.logger.warning(f"Fragment '{template_name}' not found! Available: {available_keys}")
                except:
                    self.logger.warning(f"Fragment '{template_name}' not found and couldn't list available fragments")
                raise TemplateNotFound(f"{template_name} (not found in template {self.template_uuid})")

            if not fragment.template_source:
                self.logger.warning(f"Fragment '{template_name}' found but has no source!")
                raise TemplateNotFound(f"{template_name} (no source content)")

            self.logger.debug(f"Successfully found fragment '{template_name}' with {len(fragment.template_source)} chars")

            # Process the template source to convert {% block %} tags
            processed_source = self.block_processor.process_template_source(fragment.template_source)

            # Simple uptodate function - always return False so templates are always fresh
            def uptodate():
                return False

            return processed_source, template_name, uptodate
        
        except Exception as e:
            self.logger.error(f"Error loading template source for '{template_name}': {e}")
            # Return a safe fallback template
            fallback_source = f"<!-- Template fragment '{template_name}' failed to load: {e} -->"
            def uptodate():
                return False
            return fallback_source, template_name, uptodate
