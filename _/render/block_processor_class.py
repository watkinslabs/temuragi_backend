import re
import logging
import uuid
from sqlalchemy.orm import Session


class BlockProcessor:
    """Processes template source to convert {% block %} syntax to database-backed blocks"""

    def __init__(self, session: Session, template_uuid: uuid.UUID, page_uuid: uuid.UUID = None, logger=None):
        self.session = session
        self.template_uuid = template_uuid
        self.page_uuid = page_uuid
        self.logger = logger or logging.getLogger('block_processor')
        
        # Pre-compile regex patterns for better performance
        self.block_pattern = re.compile(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', re.DOTALL)
        self.simple_block_pattern = re.compile(r'{%\s*block\s+(\w+)\s*%}')

    def _escape_content_for_template(self, content):
        """Safely escape content for inclusion in Jinja2 template"""
        if not content:
            return '""'
        
        # Just escape the damn quotes and newlines
        escaped = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        return f'"{escaped}"'

    def _create_safe_replacement(self, block_name, default_content=None):
        """Create a safe render_block replacement that handles quotes properly"""
        if not default_content:
            return f'{{{{ render_block("{block_name}") }}}}'
        
        safe_content = self._escape_content_for_template(default_content)
        return f'{{{{ render_block("{block_name}", {safe_content}) }}}}'



    def process_template_source(self, template_source):
        """Convert {% block %} tags to render_block() calls with proper quote handling"""
        try:
            self.logger.debug(f"Processing template source with {len(template_source)} characters")
            self.logger.debug(f"Template source preview: {template_source[:200]}...")

            def replace_block(match):
                block_name = match.group(1)
                default_content = match.group(2).strip()

                self.logger.debug(f"Found block '{block_name}' with default content: {default_content[:100]}...")

                replacement = self._create_safe_replacement(block_name, default_content)
                self.logger.debug(f"Replacing block '{block_name}' with: {replacement}")
                return replacement

            # Replace all block tags
            processed = self.block_pattern.sub(replace_block, template_source)

            # Handle simple {% block name %} without content (self-closing style)
            def replace_simple_block(match):
                block_name = match.group(1)
                self.logger.debug(f"Found simple block '{block_name}'")
                return f'{{{{ render_block("{block_name}") }}}}'

            # Only replace simple blocks that don't already have endblock
            lines = processed.split('\n')
            result_lines = []

            for line in lines:
                # Check if this line has a simple block that's not already processed
                if '{% block ' in line and 'render_block(' not in line and '{% endblock %}' not in line:
                    self.logger.debug(f"Processing simple block in line: {line.strip()}")
                    line = self.simple_block_pattern.sub(replace_simple_block, line)
                result_lines.append(line)

            processed = '\n'.join(result_lines)

            if processed != template_source:
                block_count = len(re.findall(r'render_block\(', processed))
                self.logger.info(f"Processed {block_count} block tags")
                self.logger.debug(f"Processed template preview: {processed[:200]}...")
            else:
                self.logger.warning("No blocks found to process")

            return processed

        except Exception as e:
            self.logger.error(f"Error processing template blocks: {e}")
            return template_source  # Return original on error