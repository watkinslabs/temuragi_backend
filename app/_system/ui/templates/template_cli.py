#!/usr/bin/env python3
"""
Template CLI - Create and manage themes, page templates, and pages
Creates template system components from YAML configuration files
"""

import sys
import argparse
import yaml
import os
from pathlib import Path

# Add app path
sys.path.append('/web/temuragi')
from app.base_cli import BaseCLI

class TemplateCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="template",
            log_file="logs/template_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting template CLI initialization")

        try:
            # Get models from registry
            self.menu_model = self.get_model('Menu')
            self.page_model = self.get_model('Page')
            self.page_template_content_model = self.get_model('PageTemplateContent')
            self.page_template_model = self.get_model('PageTemplate')
            self.theme_model = self.get_model('Theme')
            
            if not all([self.theme_model, self.page_template_model, self.page_model]):
                self.log_error("Required template models not found in registry")
                raise Exception("Required template models not found in registry")

            self.log_info("Template models loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize template CLI: {e}")
            raise

    def lookup_uuid_by_name(self, model_class, name):
        """Generic function to lookup UUID by name"""
        self.log_debug(f"Looking up UUID for {model_class.__name__} with name: {name}")
        
        obj = self.session.query(model_class).filter_by(name=name).first()
        if not obj:
            self.log_error(f"{model_class.__name__} with name '{name}' not found")
            raise Exception(f"{model_class.__name__} with name '{name}' not found")
        
        self.log_debug(f"Found {model_class.__name__} '{name}' with UUID: {obj.uuid}")
        return obj.uuid

    def list_themes(self):
        """List all themes"""
        self.log_info("Listing themes")

        try:
            themes = self.session.query(self.theme_model).order_by(self.theme_model.name).all()
            
            if not themes:
                self.output_warning("No themes found")
                return 0
            
            headers = ["Name", "Display Name", "Framework", "Mode", "UUID"]
            rows = []
            
            for theme in themes:
                rows.append([
                    theme.name,
                    getattr(theme, 'display_name', ''),
                    getattr(theme, 'css_framework', ''),
                    getattr(theme, 'mode', ''),
                    str(theme.uuid)
                ])
            
            self.output_info("Available Themes:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing themes: {e}")
            self.output_error(f"Error listing themes: {e}")
            return 1

    def list_page_templates(self):
        """List all page templates"""
        self.log_info("Listing page templates")

        try:
            templates = self.session.query(self.page_template_model).order_by(self.page_template_model.name).all()
            
            if not templates:
                self.output_warning("No page templates found")
                return 0
            
            headers = ["Name", "Display Name", "Layout", "Sidebar", "Mode", "UUID"]
            rows = []
            
            for template in templates:
                rows.append([
                    template.name,
                    getattr(template, 'display_name', ''),
                    getattr(template, 'layout_type', ''),
                    "Yes" if getattr(template, 'sidebar_enabled', False) else "No",
                    getattr(template, 'mode', ''),
                    str(template.uuid)
                ])
            
            self.output_info("Available Page Templates:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing page templates: {e}")
            self.output_error(f"Error listing page templates: {e}")
            return 1
    
    def list_pages(self):
        """List all pages"""
        self.log_info("Listing pages")

        try:
            pages = self.session.query(self.page_model).order_by(self.page_model.name).all()
            
            if not pages:
                self.output_warning("No pages found")
                return 0
            
            headers = ["Name", "Title", "Route", "Template", "Mode", "UUID"]
            rows = []
            
            for page in pages:
                template_name = ''
                if hasattr(page, 'page_template') and page.page_template:
                    template_name = page.page_template.name
                
                rows.append([
                    page.name,
                    getattr(page, 'title', ''),
                    getattr(page, 'route', ''),
                    template_name,
                    getattr(page, 'mode', ''),
                    str(page.uuid)
                ])
            
            self.output_info("Available Pages:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing pages: {e}")
            self.output_error(f"Error listing pages: {e}")
            return 1
    
    def create_full_stack(self, config_dir):
        """Create full stack from directory of YAML files with multi-file support"""
        self.log_info(f"Creating full stack from directory: {config_dir}")

        try:
            config_path = Path(config_dir)

            if not config_path.exists():
                self.output_error(f"Configuration directory '{config_dir}' not found")
                return 1

            # File patterns in dependency order
            file_pattern_groups = [
                (['theme.yaml', 'theme_*.yaml'], 'theme'),
                (['page_template.yaml', 'page_template_*.yaml'], 'page_template'),
                (['page_content.yaml', 'page_content_*.yaml'], 'page_content'),
                (['page.yaml'], 'page')
            ]

            created_uuids = {}
            total_processed = 0
            total_created = 0

            for patterns, component_type in file_pattern_groups:
                matching_files = []
                for pattern in patterns:
                    found_files = list(config_path.glob(pattern))
                    if component_type == 'page':
                        found_files = [f for f in found_files
                            if not f.name.startswith('page_content_')
                            and not f.name.startswith('page_template_')]
                    matching_files.extend(found_files)

                matching_files = sorted(set(matching_files))

                if not matching_files:
                    pattern_list = "', '".join(patterns)
                    self.output_warning(f"No files found matching patterns: '{pattern_list}'")
                    continue

                self.output_info(f"Processing {len(matching_files)} {component_type} file(s)...")

                component_uuids = []
                component_created = 0

                for file_path in matching_files:
                    self.output_info(f"  Processing {file_path.name}...")
                    total_processed += 1

                    try:
                        uuid_val = None

                        if component_type == 'theme':
                            with open(file_path, 'r') as f:
                                theme_data = yaml.safe_load(f)
                            existing = self.session.query(self.theme_model).filter_by(name=theme_data['name']).first()
                            was_created = existing is None
                            uuid_val = self.create_theme_from_yaml(file_path, allow_update=True)

                        elif component_type == 'page_template':
                            with open(file_path, 'r') as f:
                                template_data = yaml.safe_load(f)
                            existing = self.session.query(self.page_template_model).filter_by(name=template_data['name']).first()
                            was_created = existing is None
                            uuid_val = self.create_page_template_from_yaml(file_path, allow_update=True)

                        elif component_type == 'page_content':

                            # NO pre-check — delegate version handling to create_page_content_from_yaml
                            uuid_val = self.create_page_content_from_yaml(file_path, allow_update=True)
                            # optional: if you refactor create_page_content_from_yaml to return (uuid, was_created), handle that here

                            was_created = True  # treat all processed as created for now (safe)

                        elif component_type == 'page':
                            with open(file_path, 'r') as f:
                                page_data = yaml.safe_load(f)
                            existing = self.session.query(self.page_model).filter_by(name=page_data['name']).first()
                            was_created = existing is None
                            uuid_val = self.create_page_from_yaml(file_path, allow_update=True)

                        if uuid_val:
                            component_uuids.append(uuid_val)
                            if was_created:
                                component_created += 1
                                total_created += 1
                                self.output_success(f"    ✓ CREATED {file_path.name} (UUID: {uuid_val})")
                            else:
                                self.output_success(f"    ✓ UPDATED {file_path.name} (UUID: {uuid_val})")
                        else:
                            self.output_warning(f"    ? {file_path.name} returned no UUID")

                    except Exception as e:
                        self.output_error(f"    ✗ Failed to process {file_path.name}: {e}")
                        self.log_error(f"Error processing {file_path}: {e}")
                        continue

                # Store UUIDs for this component type
                if component_uuids:
                    if len(component_uuids) == 1:
                        created_uuids[component_type] = component_uuids[0]
                    else:
                        created_uuids[component_type] = component_uuids

                    self.output_info(f"  {component_type}: {component_created} created, {len(component_uuids) - component_created} updated")

            # Summary
            self.output_success("Stack creation complete!")
            self.output_info(f"Total files processed: {total_processed}")
            self.output_info(f"Total new items created: {total_created}")
            self.output_info(f"Total items updated: {total_processed - total_created}")

            if created_uuids:
                self.output_info("\nComponent Summary:")
                for component, uuid_vals in created_uuids.items():
                    if isinstance(uuid_vals, list):
                        self.output_info(f"   {component}: {len(uuid_vals)} items")
                        for i, uuid_val in enumerate(uuid_vals, 1):
                            self.output_info(f"     {i}. {uuid_val}")
                    else:
                        self.output_info(f"   {component}: {uuid_vals}")

            return 0

        except Exception as e:
            self.log_error(f"Error creating full stack: {e}")
            self.output_error(f"Error creating full stack: {e}")
            return 1

    def create_page_content_from_yaml(self, yaml_file, allow_update=False):
        """Create page template content from YAML file with correct version handling"""
        self.log_info(f"Creating page content from YAML file: {yaml_file}")

        try:
            if not self.page_template_content_model:
                self.output_warning("PageTemplateContent model not available")
                return None

            with open(yaml_file, 'r') as f:
                content_data = yaml.safe_load(f)

            # Lookup page template UUID
            if 'page_template_name' in content_data:
                content_data['page_template_uuid'] = self.lookup_uuid_by_name(
                    self.page_template_model, content_data.pop('page_template_name')
                )

            page_template_uuid = content_data['page_template_uuid']
            template_file_path = content_data['template_file_path']

            # If version_number not provided, get next version number
            if 'version_number' not in content_data:
                version_number = self.page_template_content_model.get_next_version_number(
                    self.session, page_template_uuid, template_file_path
                )
                content_data['version_number'] = version_number
            else:
                version_number = content_data['version_number']

            # DEBUG - show actual lookup being performed
            self.output_info(f"DEBUG: Looking for existing with:")
            self.output_info(f"DEBUG:   page_template_uuid = '{page_template_uuid}'")
            self.output_info(f"DEBUG:   template_file_path = '{template_file_path}'")
            self.output_info(f"DEBUG:   version_number = '{version_number}'")

            # Check if content already exists
            existing = self.session.query(self.page_template_content_model).filter_by(
                page_template_uuid=page_template_uuid,
                template_file_path=template_file_path,
                version_number=version_number
            ).first()

            if existing:
                self.output_info(f"DEBUG: FOUND EXISTING RECORD (UUID: {existing.uuid})")
                if allow_update:
                    self.output_warning(f"Page template content {template_file_path} v{version_number} already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Page template content {template_file_path} v{version_number} already exists (UUID: {existing.uuid})")
                    raise Exception(f"Page template content {template_file_path} v{version_number} already exists")

            # Set defaults for new fields
            if 'content_type' not in content_data:
                content_data['content_type'] = 'text/html'

            if 'is_active' not in content_data:
                content_data['is_active'] = False

            if 'cache_duration' not in content_data:
                content_data['cache_duration'] = 3600

            # Handle template source and hash
            if 'template_source' in content_data:
                import hashlib
                template_source = content_data['template_source']
                if 'template_hash' not in content_data:
                    content_data['template_hash'] = hashlib.sha256(template_source.encode('utf-8')).hexdigest()

            # Create new page template content
            self.output_info(f"DEBUG: Creating new page template content: {template_file_path} v{version_number}")
            content = self.page_template_content_model(**content_data)
            self.session.add(content)
            self.session.flush()  # get UUID before commit

            new_uuid = content.uuid
            self.output_info(f"DEBUG: New content created with UUID: {new_uuid}")

            # If active, deactivate other versions of same file
            if content.is_active:
                self.output_info(f"DEBUG: Deactivating other versions of file {template_file_path}")
                deactivated_count = self.session.query(self.page_template_content_model)\
                    .filter_by(page_template_uuid=page_template_uuid,
                            template_file_path=template_file_path)\
                    .filter(self.page_template_content_model.uuid != content.uuid)\
                    .update({'is_active': False})
                self.output_info(f"DEBUG: Deactivated {deactivated_count} other versions of {template_file_path}")

            self.session.commit()

            version_display = content.get_display_version()
            self.output_success(f"Created page template content: {content.template_file_path} {version_display} (UUID: {content.uuid})")
            return content.uuid

        except Exception as e:
            self.log_error(f"Error creating page content from YAML: {e}")
            self.output_error(f"Error creating page content: {e}")
            self.session.rollback()
            raise


    def list_page_content(self):
        """List all page template content with filename and version info"""
        self.log_info("Listing page template content")

        try:
            if not self.page_template_content_model:
                self.output_warning("PageTemplateContent model not available")
                return 1

            contents = self.session.query(self.page_template_content_model)\
                                 .order_by(self.page_template_content_model.template_file_path,
                                          self.page_template_content_model.version_number.desc())\
                                 .all()
            
            if not contents:
                self.output_warning("No page template content found")
                return 0
            
            headers = ["Template File", "Version", "Active", "Content Type", "Template", "UUID"]
            rows = []
            
            for content in contents:
                template_name = ''
                if hasattr(content, 'page_template') and content.page_template:
                    template_name = content.page_template.name
                
                rows.append([
                    content.template_file_path,
                    content.get_display_version(),
                    "Yes" if content.is_active else "No",
                    content.content_type,
                    template_name,
                    str(content.uuid)
                ])
            
            self.output_info("Available Page Template Content:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing page content: {e}")
            self.output_error(f"Error listing page content: {e}")
            return 1

    def create_theme_from_yaml(self, yaml_file, allow_update=False):
        """Create a theme from YAML file"""
        self.log_info(f"Creating theme from YAML file: {yaml_file}")

        try:
            with open(yaml_file, 'r') as f:
                theme_data = yaml.safe_load(f)
            
            # Check if theme already exists
            existing = self.session.query(self.theme_model).filter_by(name=theme_data['name']).first()
            if existing:
                if allow_update:
                    self.output_warning(f"Theme '{theme_data['name']}' already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Theme '{theme_data['name']}' already exists (UUID: {existing.uuid})")
                    raise Exception(f"Theme '{theme_data['name']}' already exists")
            
            # Create theme
            theme = self.theme_model(**theme_data)
            self.session.add(theme)
            self.session.commit()
            
            self.output_success(f"Created theme: {theme.name} (UUID: {theme.uuid})")
            return theme.uuid

        except Exception as e:
            self.log_error(f"Error creating theme from YAML: {e}")
            self.output_error(f"Error creating theme: {e}")
            self.session.rollback()
            raise

    def create_page_template_from_yaml(self, yaml_file, allow_update=False):
        """Create a page template from YAML file"""
        self.log_info(f"Creating page template from YAML file: {yaml_file}")

        try:
            with open(yaml_file, 'r') as f:
                template_data = yaml.safe_load(f)
            
            # Lookup foreign key UUIDs
            if 'theme_name' in template_data:
                template_data['theme_uuid'] = self.lookup_uuid_by_name(
                    self.theme_model, template_data.pop('theme_name')
                )
            
            if 'menu_name' in template_data:
                template_data['menu_type_uuid'] = self.lookup_uuid_by_name(
                    self.menu_model, template_data.pop('menu_name')
                )
            
            # Check if template already exists
            existing = self.session.query(self.page_template_model).filter_by(name=template_data['name']).first()
            if existing:
                if allow_update:
                    self.output_warning(f"Page template '{template_data['name']}' already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Page template '{template_data['name']}' already exists (UUID: {existing.uuid})")
                    raise Exception(f"Page template '{template_data['name']}' already exists")
            
            # Create page template
            page_template = self.page_template_model(**template_data)
            self.session.add(page_template)
            self.session.commit()
            
            self.output_success(f"Created page template: {page_template.name} (UUID: {page_template.uuid})")
            return page_template.uuid

        except Exception as e:
            self.log_error(f"Error creating page template from YAML: {e}")
            self.output_error(f"Error creating page template: {e}")
            self.session.rollback()
            raise

    def create_page_from_yaml(self, yaml_file, allow_update=False):
        """Create a page from YAML file"""
        self.log_info(f"Creating page from YAML file: {yaml_file}")

        try:
            with open(yaml_file, 'r') as f:
                page_data = yaml.safe_load(f)
            
            # Lookup page template UUID
            if 'page_template_name' in page_data:
                page_data['page_template_uuid'] = self.lookup_uuid_by_name(
                    self.page_template_model, page_data.pop('page_template_name')
                )
            
            # Check if page already exists
            existing = self.session.query(self.page_model).filter_by(name=page_data['name']).first()
            if existing:
                if allow_update:
                    self.output_warning(f"Page '{page_data['name']}' already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Page '{page_data['name']}' already exists (UUID: {existing.uuid})")
                    raise Exception(f"Page '{page_data['name']}' already exists")
            
            # Create page
            page = self.page_model(**page_data)
            self.session.add(page)
            self.session.commit()
            
            self.output_success(f"Created page: {page.name} (UUID: {page.uuid})")
            return page.uuid

        except Exception as e:
            self.log_error(f"Error creating page from YAML: {e}")
            self.output_error(f"Error creating page: {e}")
            self.session.rollback()
            raise

    def update_templates(self, config_dir):
        """Update template directory by creating page-template-content files for template files found"""
        self.log_info(f"Updating templates in directory: {config_dir}")

        try:
            config_path = Path(config_dir)

            if not config_path.exists():
                self.output_error(f"Configuration directory '{config_dir}' not found")
                return 1

            files_created = []

            # Find existing page template YAML files to get UUIDs
            page_template_files = []
            page_template_files.extend(config_path.glob('page_template.yaml'))
            page_template_files.extend(config_path.glob('page_template_*.yaml'))

            if not page_template_files:
                self.output_warning("No page template YAML files found - cannot create content files")
                return 1

            # Extract UUIDs and names from page template files
            template_info = {}
            for template_file in page_template_files:
                try:
                    with open(template_file, 'r') as f:
                        template_data = yaml.safe_load(f)
                        template_name = template_data.get('name')
                        template_uuid = template_data.get('uuid')

                        if template_name and template_uuid:
                            template_info[template_name] = template_uuid
                            self.output_info(f"Found template '{template_name}' with UUID: {template_uuid}")
                        else:
                            self.output_warning(f"Template file {template_file.name} missing name or uuid")

                except Exception as e:
                    self.output_error(f"Error reading template file {template_file.name}: {e}")
                    continue

            if not template_info:
                self.output_error("No valid page template files with name/uuid found")
                return 1

            # Find all template files in templates/ subdirectory
            templates_dir = config_path / "templates"
            if not templates_dir.exists():
                self.output_warning("No templates/ directory found")
                return 0

            # Content type mapping based on file extensions
            content_type_map = {
                '.html': 'text/html',
                '.htm': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.txt': 'text/plain',
                '.xml': 'text/xml',
                '.json': 'application/json',
                '.jinja': 'text/html',
                '.j2': 'text/html'
            }

            # Find all template files recursively
            template_extensions = list(content_type_map.keys())
            template_files = []
            for ext in template_extensions:
                template_files.extend(templates_dir.rglob(f"*{ext}"))

            if not template_files:
                self.output_warning(f"No template files found in templates/ directory with extensions: {', '.join(template_extensions)}")
                return 0

            self.output_info(f"Found {len(template_files)} template file(s)")

            # For each template file, create a page-template-content file if it doesn't exist
            for template_file in template_files:
                # Generate relative path from templates directory
                relative_path = template_file.relative_to(config_path)

                # Generate content filename based on template path
                safe_filename = str(relative_path).replace('/', '_').replace('.', '_')
                content_filename = f"page_content_{safe_filename}.yaml"
                content_file = config_path / content_filename

                if content_file.exists():
                    self.output_info(f"Skipping {content_filename} - already exists")
                    continue

                # Determine which page template to use (for now, use the first one)
                # In the future, could be smarter about matching template names
                template_name = list(template_info.keys())[0]
                template_uuid = template_info[template_name]

                if not self.page_template_content_model:
                    self.output_warning("PageTemplateContent model not available")
                    continue

                # Determine content type from file extension
                file_extension = template_file.suffix.lower()
                content_type = content_type_map.get(file_extension, 'text/plain')

                # Read the template file content
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_source = f.read()
                except Exception as e:
                    self.log_warning(f"Could not read template file {template_file}: {e}")
                    template_source = f"# Could not read template source from {relative_path}"

                # Calculate template hash for change detection
                import hashlib
                template_hash = hashlib.sha256(template_source.encode('utf-8')).hexdigest()

                # Get next version number for this template
                next_version = self.page_template_content_model.get_next_version_number(
                    self.session, template_uuid, str(relative_path)
                )

                # Create dummy page content object with all necessary fields
                content_dummy = self.page_template_content_model()
                content_dummy.page_template_uuid = template_uuid
                content_dummy.template_file_path = str(relative_path)
                content_dummy.content_type = content_type

                # Use new versioning system
                content_dummy.version_number = next_version
                content_dummy.version_label = None  # No label for initial template
                content_dummy.is_active = True  # Template versions default to active

                content_dummy.cache_duration = 3600
                content_dummy.template_hash = template_hash
                content_dummy.template_source = template_source  # Always store content
                content_dummy.change_description = f"Initial template version for {relative_path}"

                # Set compiled file path
                compiled_path = str(relative_path).replace(file_extension, '.pyc')
                content_dummy.compiled_file_path = f"compiled_templates/{compiled_path}"

                # Set relationship attribute
                content_dummy.page_template_name = template_name

                content_mappings = {
                    'page_template_uuid': 'name'
                }

                self.exporter.export_model_object(
                    content_dummy,
                    content_file,
                    content_mappings,
                    header_title=f"Page Template Content for {relative_path}",
                    header_description=f"Auto-generated for template: {relative_path}, linked to page template: {template_name}",
                    template_mode=True
                )

                files_created.append(str(content_file))
                self.output_success(f"Created: {content_filename}")

            if files_created:
                self.output_success(f"Created {len(files_created)} page content file(s)")
                self.output_info("Files created:")
                for file_path in files_created:
                    self.output_info(f"   {Path(file_path).name}")
            else:
                self.output_info("No new page content files needed")

            return 0

        except Exception as e:
            self.log_error(f"Error updating templates: {e}")
            self.output_error(f"Error updating templates: {e}")
            return 1

    def generate_yaml_templates(self, output_dir):
        """Generate example YAML template files using ComponentExporter"""
        self.log_info(f"Generating YAML templates in: {output_dir}")

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            files_created = []

            # Create dummy theme object
            theme_dummy = self.theme_model()
            theme_dummy.name = 'my-custom-theme'
            theme_dummy.display_name = 'My Custom Theme'
            theme_dummy.description = 'A custom theme for my application'
            theme_dummy.uuid = 'EXAMPLE-THEME-UUID-REPLACE-ME'

            # Set other likely fields with example values
            if hasattr(theme_dummy, 'css_framework'):
                theme_dummy.css_framework = 'bootstrap'
            if hasattr(theme_dummy, 'mode'):
                theme_dummy.mode = 'light'
            if hasattr(theme_dummy, 'version'):
                theme_dummy.version = '1.0.0'

            theme_file = output_path / "theme.yaml"
            self.exporter.export_model_object(
                theme_dummy,
                theme_file,
                header_title="Example Theme Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(theme_file))

            # Create dummy page template object
            template_dummy = self.page_template_model()
            template_dummy.name = 'my-page-template'
            template_dummy.display_name = 'My Page Template'
            template_dummy.description = 'Custom page template for my application'
            template_dummy.uuid = 'EXAMPLE-PAGE-TEMPLATE-UUID-REPLACE-ME'
            template_dummy.theme_uuid = 'EXAMPLE-THEME-UUID-REPLACE-ME'

            # Set other likely fields
            if hasattr(template_dummy, 'layout_type'):
                template_dummy.layout_type = 'sidebar-left'
            if hasattr(template_dummy, 'sidebar_enabled'):
                template_dummy.sidebar_enabled = True
            if hasattr(template_dummy, 'template_file'):
                template_dummy.template_file = 'templates/custom/my_template.html'
            if hasattr(template_dummy, 'menu_type_uuid'):
                template_dummy.menu_type_uuid = 'EXAMPLE-MENU-UUID-REPLACE-ME'

            # Set relationship attributes directly on the model
            template_dummy.theme_name = 'my-custom-theme'
            template_dummy.menu_type_name = 'MAIN'

            foreign_key_mappings = {
                'theme_uuid': 'name',
                'menu_type_uuid': 'name'
            }

            template_file = output_path / "page_template.yaml"
            self.exporter.export_model_object(
                template_dummy,
                template_file,
                foreign_key_mappings,
                header_title="Example Page Template Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(template_file))

            # Create dummy page template content if model exists
            if self.page_template_content_model:
                content_dummy = self.page_template_content_model()
                content_dummy.page_template_uuid = 'EXAMPLE-PAGE-TEMPLATE-UUID-REPLACE-ME'
                content_dummy.template_file_path = 'templates/custom/my_template.html'
                content_dummy.compiled_file_path = 'compiled_templates/custom/my_template.pyc'
                content_dummy.uuid = 'EXAMPLE-PAGE-CONTENT-UUID-REPLACE-ME'

                # Set new versioning fields
                content_dummy.version_number = 1
                content_dummy.version_label = None
                content_dummy.is_active = True

                # Set content type and template source
                content_dummy.content_type = 'text/html'
                content_dummy.template_source = 'See templates/custom/my_template.html'
                content_dummy.cache_duration = 3600
                content_dummy.change_description = 'Initial template version'

                # Calculate hash for example content
                import hashlib
                content_dummy.template_hash = hashlib.sha256(
                    content_dummy.template_source.encode('utf-8')
                ).hexdigest()

                # Set relationship attribute directly
                content_dummy.page_template_name = 'my-page-template'

                content_mappings = {
                    'page_template_uuid': 'name'
                }

                content_file = output_path / "page_content.yaml"
                self.exporter.export_model_object(
                    content_dummy,
                    content_file,
                    content_mappings,
                    header_title="Example Page Template Content Configuration",
                    header_description="Edit values and replace UUIDs before importing"
                )
                files_created.append(str(content_file))

            # Create dummy page object
            page_dummy = self.page_model()
            page_dummy.name = 'my-custom-page'
            page_dummy.title = 'My Custom Page'
            page_dummy.description = 'A custom page in my application'
            page_dummy.route = '/my-page'
            page_dummy.page_template_uuid = 'EXAMPLE-PAGE-TEMPLATE-UUID-REPLACE-ME'
            page_dummy.uuid = 'EXAMPLE-PAGE-UUID-REPLACE-ME'

            # Set other likely fields
            if hasattr(page_dummy, 'page_body'):
                page_dummy.page_body = '<p>Custom page content goes here</p>'
            if hasattr(page_dummy, 'meta_description'):
                page_dummy.meta_description = 'SEO description for my custom page'
            if hasattr(page_dummy, 'is_published'):
                page_dummy.is_published = True

            # Set relationship attribute directly
            page_dummy.page_template_name = 'my-page-template'

            page_mappings = {
                'page_template_uuid': 'name'
            }

            page_file = output_path / "page.yaml"
            self.exporter.export_model_object(
                page_dummy,
                page_file,
                page_mappings,
                header_title="Example Page Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(page_file))

            # Create template directory and sample file
            template_dir = output_path / "templates" / "custom"
            template_dir.mkdir(parents=True, exist_ok=True)

            sample_template = """{% extends "base-layout" %}

{% block title %}{{ page.title }} - {{ super() }}{% endblock %}

{% block page_content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1>{{ page.title or 'Custom Page' }}</h1>
            {% if page.description %}
            <p class="lead">{{ page.description }}</p>
            {% endif %}
            {{ page.page_body|safe if page.page_body else '<p>No content specified.</p>' }}
        </div>
    </div>
</div>
{% endblock %}
"""

            template_html_file = template_dir / "my_template.html"
            with open(template_html_file, 'w') as f:
                f.write(sample_template)
            files_created.append(str(template_html_file))

            self.output_success(f"Generated template files in: {output_path}")
            self.output_info("Files created:")
            for file_path in files_created:
                self.output_info(f"   {file_path}")

            return files_created

        except Exception as e:
            self.log_error(f"Error generating YAML templates: {e}")
            self.output_error(f"Error generating YAML templates: {e}")
            return 1

    def export_theme_by_uuid(self, theme_uuid, output_dir):
        """Export a specific theme by UUID"""
        self.log_info(f"Exporting theme by UUID: {theme_uuid}")
        
        # Find the theme
        theme = self.session.query(self.theme_model).filter_by(uuid=theme_uuid).first()
        if not theme:
            self.output_error(f"Theme with UUID {theme_uuid} not found")
            return 1
        
        # Generate output file path
        filename = f"theme_{theme.name}.yaml"
        output_file = Path(output_dir) / filename
        
        return self.exporter.export_model_object(
            theme, 
            output_file,
            header_title=f"Theme '{theme.name}'"
        )

    def export_page_template_by_uuid(self, template_uuid, output_dir):
        """Export a specific page template by UUID"""
        self.log_info(f"Exporting page template by UUID: {template_uuid}")
        
        # Find the page template
        template = self.session.query(self.page_template_model).filter_by(uuid=template_uuid).first()
        if not template:
            self.output_error(f"Page template with UUID {template_uuid} not found")
            return 1
        
        # Define foreign key mappings for page templates
        foreign_key_mappings = {
            'theme_uuid': 'name',
            'menu_type_uuid': 'name'
        }
        
        # Generate output file path
        filename = f"page_template_{template.name}.yaml"
        output_file = Path(output_dir) / filename
        
        return self.exporter.export_model_object(
            template,
            output_file,
            foreign_key_mappings,
            header_title=f"Page Template '{template.name}'"
        )

    def export_page_by_uuid(self, page_uuid, output_dir):
        """Export a specific page by UUID"""
        self.log_info(f"Exporting page by UUID: {page_uuid}")
        
        # Find the page
        page = self.session.query(self.page_model).filter_by(uuid=page_uuid).first()
        if not page:
            self.output_error(f"Page with UUID {page_uuid} not found")
            return 1
        
        # Define foreign key mappings for pages
        foreign_key_mappings = {
            'page_template_uuid': 'name'
        }
        
        # Generate output file path
        filename = f"page_{page.name}.yaml"
        output_file = Path(output_dir) / filename
        
        return self.exporter.export_model_object(
            page,
            output_file,
            foreign_key_mappings,
            header_title=f"Page '{page.name}'"
        )

    def export_page_content_by_uuid(self, content_uuid, output_dir):
        """Export specific page template content by UUID"""
        self.log_info(f"Exporting page content by UUID: {content_uuid}")
        
        if not self.page_template_content_model:
            self.output_warning("PageTemplateContent model not available")
            return 1
        
        # Find the page content
        content = self.session.query(self.page_template_content_model).filter_by(uuid=content_uuid).first()
        if not content:
            self.output_error(f"Page template content with UUID {content_uuid} not found")
            return 1
        
        # Define foreign key mappings for page content
        foreign_key_mappings = {
            'page_template_uuid': 'name'
        }
        
        # Generate output file path
        safe_filename = content.template_file_path.replace('/', '_').replace('.', '_')
        filename = f"page_content_{safe_filename}.yaml"
        output_file = Path(output_dir) / filename
        
        return self.exporter.export_model_object(
            content,
            output_file,
            foreign_key_mappings,
            header_title="Page Template Content",
            header_description=f"Template: {content.template_file_path}"
        )


    def update_templates(self, config_dir):
        """Update template directory by creating page-template-content files for template files found"""
        self.log_info(f"Updating templates in directory: {config_dir}")

        try:
            config_path = Path(config_dir)

            if not config_path.exists():
                self.output_error(f"Configuration directory '{config_dir}' not found")
                return 1

            files_created = []

            # Find existing page template YAML files to get UUIDs
            page_template_files = []
            page_template_files.extend(config_path.glob('page_template.yaml'))
            page_template_files.extend(config_path.glob('page_template_*.yaml'))

            if not page_template_files:
                self.output_warning("No page template YAML files found - cannot create content files")
                return 1

            # Extract UUIDs and names from page template files
            template_info = {}
            for template_file in page_template_files:
                try:
                    with open(template_file, 'r') as f:
                        template_data = yaml.safe_load(f)
                        template_name = template_data.get('name')
                        template_uuid = template_data.get('uuid')

                        if template_name and template_uuid:
                            template_info[template_name] = template_uuid
                            self.output_info(f"Found template '{template_name}' with UUID: {template_uuid}")
                        else:
                            self.output_warning(f"Template file {template_file.name} missing name or uuid")

                except Exception as e:
                    self.output_error(f"Error reading template file {template_file.name}: {e}")
                    continue

            if not template_info:
                self.output_error("No valid page template files with name/uuid found")
                return 1

            # Find all template files in templates/ subdirectory
            templates_dir = config_path / "templates"
            if not templates_dir.exists():
                self.output_warning("No templates/ directory found")
                return 0

            # Content type mapping based on file extensions
            content_type_map = {
                '.html': 'text/html',
                '.htm': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.txt': 'text/plain',
                '.xml': 'text/xml',
                '.json': 'application/json',
                '.jinja': 'text/html',
                '.j2': 'text/html'
            }

            # Find all template files recursively
            template_extensions = list(content_type_map.keys())
            template_files = []
            for ext in template_extensions:
                template_files.extend(templates_dir.rglob(f"*{ext}"))

            if not template_files:
                self.output_warning(f"No template files found in templates/ directory with extensions: {', '.join(template_extensions)}")
                return 0

            self.output_info(f"Found {len(template_files)} template file(s)")

            # For each template file, create a page-template-content file if it doesn't exist
            for template_file in template_files:
                # Generate relative path from templates directory
                relative_path = template_file.relative_to(config_path)
                # Generate content filename based on template path
                safe_filename = str(relative_path).replace('/', '_').replace('.', '_')
                content_filename = f"page_content_{safe_filename}.yaml"
                content_file = config_path / content_filename

                if content_file.exists():
                    self.output_info(f"Skipping {content_filename} - already exists")
                    continue

                # Determine which page template to use (for now, use the first one)
                # In the future, could be smarter about matching template names
                template_name = list(template_info.keys())[0]
                template_uuid = template_info[template_name]

                if not self.page_template_content_model:
                    self.output_warning("PageTemplateContent model not available")
                    continue

                # Determine content type from file extension
                file_extension = template_file.suffix.lower()
                content_type = content_type_map.get(file_extension, 'text/plain')

                # Read the template file content
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_source = f.read()
                except Exception as e:
                    self.log_warning(f"Could not read template file {template_file}: {e}")
                    template_source = f"# Could not read template source from {relative_path}"

                # Calculate template hash for change detection
                import hashlib
                template_hash = hashlib.sha256(template_source.encode('utf-8')).hexdigest()

                # Get next version number for this template
                next_version = self.page_template_content_model.get_next_version_number(
                    self.session, template_uuid,  str(relative_path)
                )

                # Create dummy page content object with all necessary fields
                content_dummy = self.page_template_content_model()
                content_dummy.page_template_uuid = template_uuid
                content_dummy.template_file_path = str(relative_path)
                content_dummy.content_type = content_type

                # Use new versioning system
                content_dummy.version_number = next_version
                content_dummy.version_label = None  # No label for initial template
                content_dummy.is_active = True  # Template versions default to active

                content_dummy.cache_duration = 3600
                content_dummy.template_hash = template_hash
                content_dummy.template_source = template_source  # Always store content
                content_dummy.change_description = f"Initial template version for {relative_path}"

                # Set compiled file path
                compiled_path = str(relative_path).replace(file_extension, '.pyc')
                content_dummy.compiled_file_path = f"compiled_templates/{compiled_path}"

                # Set relationship attribute
                content_dummy.page_template_name = template_name

                content_mappings = {
                    'page_template_uuid': 'name'
                }

                self.exporter.export_model_object(
                    content_dummy,
                    content_file,
                    content_mappings,
                    header_title=f"Page Template Content for {relative_path}",
                    header_description=f"Auto-generated for template: {relative_path}, linked to page template: {template_name}",
                    template_mode=True
                )

                files_created.append(str(content_file))
                self.output_success(f"Created: {content_filename}")

            if files_created:
                self.output_success(f"Created {len(files_created)} page content file(s)")
                self.output_info("Files created:")
                for file_path in files_created:
                    self.output_info(f"   {Path(file_path).name}")
            else:
                self.output_info("No new page content files needed")

            return 0

        except Exception as e:
            self.log_error(f"Error updating templates: {e}")
            self.output_error(f"Error updating templates: {e}")
            return 1

    def generate_yaml_templates(self, output_dir):
        """Generate example YAML template files using ComponentExporter"""
        self.log_info(f"Generating YAML templates in: {output_dir}")

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            files_created = []

            # Create dummy theme object
            theme_dummy = self.theme_model()
            theme_dummy.name = 'my-custom-theme'
            theme_dummy.display_name = 'My Custom Theme'
            theme_dummy.description = 'A custom theme for my application'
            theme_dummy.uuid = 'EXAMPLE-THEME-UUID-REPLACE-ME'

            # Set other likely fields with example values
            if hasattr(theme_dummy, 'css_framework'):
                theme_dummy.css_framework = 'bootstrap'
            if hasattr(theme_dummy, 'mode'):
                theme_dummy.mode = 'light'
            if hasattr(theme_dummy, 'version'):
                theme_dummy.version = '1.0.0'

            theme_file = output_path / "theme.yaml"
            self.exporter.export_model_object(
                theme_dummy,
                theme_file,
                header_title="Example Theme Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(theme_file))

            # Create dummy page template object
            template_dummy = self.page_template_model()
            template_dummy.name = 'my-page-template'
            template_dummy.display_name = 'My Page Template'
            template_dummy.description = 'Custom page template for my application'
            template_dummy.uuid = 'EXAMPLE-PAGE-TEMPLATE-UUID-REPLACE-ME'
            template_dummy.theme_uuid = 'EXAMPLE-THEME-UUID-REPLACE-ME'

            # Set other likely fields
            if hasattr(template_dummy, 'layout_type'):
                template_dummy.layout_type = 'sidebar-left'
            if hasattr(template_dummy, 'sidebar_enabled'):
                template_dummy.sidebar_enabled = True
            if hasattr(template_dummy, 'template_file'):
                template_dummy.template_file = 'templates/custom/my_template.html'
            if hasattr(template_dummy, 'menu_type_uuid'):
                template_dummy.menu_type_uuid = 'EXAMPLE-MENU-UUID-REPLACE-ME'

            # Set relationship attributes directly on the model
            template_dummy.theme_name = 'my-custom-theme'
            template_dummy.menu_type_name = 'MAIN'

            foreign_key_mappings = {
                'theme_uuid': 'name',
                'menu_type_uuid': 'name'
            }

            template_file = output_path / "page_template.yaml"
            self.exporter.export_model_object(
                template_dummy,
                template_file,
                foreign_key_mappings,
                header_title="Example Page Template Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(template_file))

            # Create dummy page template content if model exists
            if self.page_template_content_model:
                content_dummy = self.page_template_content_model()
                content_dummy.page_template_uuid = 'EXAMPLE-PAGE-TEMPLATE-UUID-REPLACE-ME'
                content_dummy.template_file_path = 'templates/custom/my_template.html'
                content_dummy.compiled_file_path = 'compiled_templates/custom/my_template.pyc'
                content_dummy.uuid = 'EXAMPLE-PAGE-CONTENT-UUID-REPLACE-ME'

                # Set new versioning fields
                content_dummy.version_number = 1
                content_dummy.version_label = None
                content_dummy.is_active = True

                # Set content type and template source
                content_dummy.content_type = 'text/html'
                content_dummy.template_source = 'See templates/custom/my_template.html'
                content_dummy.cache_duration = 3600
                content_dummy.change_description = 'Initial template version'

                # Calculate hash for example content
                import hashlib
                content_dummy.template_hash = hashlib.sha256(
                    content_dummy.template_source.encode('utf-8')
                ).hexdigest()

                # Set relationship attribute directly
                content_dummy.page_template_name = 'my-page-template'

                content_mappings = {
                    'page_template_uuid': 'name'
                }

                content_file = output_path / "page_content.yaml"
                self.exporter.export_model_object(
                    content_dummy,
                    content_file,
                    content_mappings,
                    header_title="Example Page Template Content Configuration",
                    header_description="Edit values and replace UUIDs before importing"
                )
                files_created.append(str(content_file))

            # Create dummy page object
            page_dummy = self.page_model()
            page_dummy.name = 'my-custom-page'
            page_dummy.title = 'My Custom Page'
            page_dummy.description = 'A custom page in my application'
            page_dummy.route = '/my-page'
            page_dummy.page_template_uuid = 'EXAMPLE-PAGE-TEMPLATE-UUID-REPLACE-ME'
            page_dummy.uuid = 'EXAMPLE-PAGE-UUID-REPLACE-ME'

            # Set other likely fields
            if hasattr(page_dummy, 'page_body'):
                page_dummy.page_body = '<p>Custom page content goes here</p>'
            if hasattr(page_dummy, 'meta_description'):
                page_dummy.meta_description = 'SEO description for my custom page'
            if hasattr(page_dummy, 'is_published'):
                page_dummy.is_published = True

            # Set relationship attribute directly
            page_dummy.page_template_name = 'my-page-template'

            page_mappings = {
                'page_template_uuid': 'name'
            }

            page_file = output_path / "page.yaml"
            self.exporter.export_model_object(
                page_dummy,
                page_file,
                page_mappings,
                header_title="Example Page Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(page_file))

            # Create template directory and sample file
            template_dir = output_path / "templates" / "custom"
            template_dir.mkdir(parents=True, exist_ok=True)

            sample_template = """{% extends "base-layout" %}

{% block title %}{{ page.title }} - {{ super() }}{% endblock %}

{% block page_content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1>{{ page.title or 'Custom Page' }}</h1>
            {% if page.description %}
            <p class="lead">{{ page.description }}</p>
            {% endif %}
            {{ page.page_body|safe if page.page_body else '<p>No content specified.</p>' }}
        </div>
    </div>
</div>
{% endblock %}
"""

            template_html_file = template_dir / "my_template.html"
            with open(template_html_file, 'w') as f:
                f.write(sample_template)
            files_created.append(str(template_html_file))

            self.output_success(f"Generated template files in: {output_path}")
            self.output_info("Files created:")
            for file_path in files_created:
                self.output_info(f"   {file_path}")

            return files_created

        except Exception as e:
            self.log_error(f"Error generating YAML templates: {e}")
            self.output_error(f"Error generating YAML templates: {e}")
            return 1
    
    def close(self):
        """Clean up database session"""
        self.log_debug("Closing template CLI")
        super().close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Create and manage template system components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""" """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (debug level)')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format (default from config)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create commands
    create_parser = subparsers.add_parser('create', help='Create components from YAML (fails if exists)')
    create_parser.add_argument('component', choices=['theme', 'page_template', 'page_content', 'page', 'stack'],
                              help='Component type to create')
    create_parser.add_argument('file_or_dir', help='YAML file or directory path')

    # List commands
    list_parser = subparsers.add_parser('list', help='List components')
    list_parser.add_argument('component', choices=['themes', 'templates','content', 'pages'],
                            help='Component type to list')

    # Export commands with subparsers
    export_parser = subparsers.add_parser('export', help='Export individual components by UUID')
    export_subparsers = export_parser.add_subparsers(dest='export_component', help='Component type to export')
    
    # Export theme
    export_theme_parser = export_subparsers.add_parser('theme', help='Export theme by UUID')
    export_theme_parser.add_argument('uuid', help='UUID of theme to export')
    export_theme_parser.add_argument('output_dir', help='Directory to write exported YAML file')
    
    # Export page template  
    export_template_parser = export_subparsers.add_parser('page_template', help='Export page template by UUID')
    export_template_parser.add_argument('uuid', help='UUID of page template to export')
    export_template_parser.add_argument('output_dir', help='Directory to write exported YAML file')
    
    # Export page
    export_page_parser = export_subparsers.add_parser('page', help='Export page by UUID')
    export_page_parser.add_argument('uuid', help='UUID of page to export')
    export_page_parser.add_argument('output_dir', help='Directory to write exported YAML file')
    
    # Export page content
    export_content_parser = export_subparsers.add_parser('page_content', help='Export page template content by UUID')
    export_content_parser.add_argument('uuid', help='UUID of page template content to export')
    export_content_parser.add_argument('output_dir', help='Directory to write exported YAML file')

    # Generate commands
    generate_parser = subparsers.add_parser('generate', help='Generate template files')
    generate_parser.add_argument('component', choices=['templates'], 
                                help='templates - Generate example YAML configuration files for all template components')
    generate_parser.add_argument('output_dir', help='Directory where template files will be created')

    # Help command
    help_parser = subparsers.add_parser('help-detail', help='Show detailed help and workflows')

    # Update commands
    update_parser = subparsers.add_parser('update', help='Update template directories')
    update_parser.add_argument('component', choices=['templates'], 
                              help='templates - Create page-template-content files for HTML templates found in directory')
    update_parser.add_argument('config_dir', help='Directory containing YAML files and templates/ subdirectory')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = TemplateCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute commands
    try:
        if args.command == 'create':
            if args.component == 'theme':
                cli.create_theme_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'page_template':
                cli.create_page_template_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'page_content':
                cli.create_page_content_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'page':
                cli.create_page_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'stack':
                return cli.create_full_stack(args.file_or_dir)

        elif args.command == 'list':
            if args.component == 'themes':
                return cli.list_themes()
            elif args.component == 'templates':
                return cli.list_page_templates()
            elif args.component == 'content':
                return cli.list_page_content()
            elif args.component == 'pages':
                return cli.list_pages()

        elif args.command == 'export':
            if args.export_component == 'theme':
                return cli.export_theme_by_uuid(args.uuid, args.output_dir)
            elif args.export_component == 'page_template':
                return cli.export_page_template_by_uuid(args.uuid, args.output_dir)
            elif args.export_component == 'page':
                return cli.export_page_by_uuid(args.uuid, args.output_dir)
            elif args.export_component == 'page_content':
                return cli.export_page_content_by_uuid(args.uuid, args.output_dir)
            else:
                export_parser.print_help()
                return 1

        elif args.command == 'generate':
            if args.component == 'templates':
                return cli.generate_yaml_templates(args.output_dir)

        elif args.command == 'help-detail':
            print("""
Template CLI - Detailed Help and Workflows

BASIC EXAMPLES:
  tmcli create stack ./config/        # Create full stack from directory
  tmcli list themes                   # List all themes
  tmcli generate templates ./output/  # Generate example files
  tmcli update templates ./myproject/ # Create page-content files for HTML templates

ALL COMMANDS:
  tmcli create theme theme.yaml              # Create theme from YAML (fails if exists)
  tmcli create page_template pt.yaml         # Create page template from YAML (fails if exists)
  tmcli create page_content pc.yaml          # Create page content from YAML (fails if exists)
  tmcli create page page.yaml                # Create page from YAML (fails if exists)
  tmcli create stack ./config/               # Create full stack from directory (updates existing)
  tmcli list themes                          # List all themes
  tmcli list page-templates                  # List all page templates
  tmcli list pages                           # List all pages
  tmcli export theme <uuid> ./backup/        # Export specific theme by UUID
  tmcli export page_template <uuid> ./backup/ # Export specific page template by UUID  
  tmcli export page <uuid> ./backup/         # Export specific page by UUID
  tmcli export page_content <uuid> ./backup/ # Export specific page content by UUID
  tmcli generate templates ./output/         # Generate example YAML files and sample template
  tmcli update templates ./myproject/        # Create page-content files for HTML templates found

CREATE VS STACK BEHAVIOR:
  - 'create' commands will FAIL if a component with the same name already exists
  - 'create stack' will UPDATE/reuse existing components if they already exist

EXPORT COMMAND DETAILS:
  The 'export components' command finds all components that depend on a specific 
  component UUID and exports them as YAML configuration files. This is useful for:
  
  - Backing up components that use a specific theme or template
  - Migrating components between environments
  - Creating deployment packages
  - Understanding component dependencies
  
  Supported dependency chains:
    Theme UUID        → finds page templates using theme → finds pages using those templates
    Page Template UUID → finds pages using that template
    Menu UUID         → finds page templates using menu → finds pages using those templates
  
  Exported files are named: component_<name>.yaml
  
  Each exported file includes:
    - Complete component configuration as YAML
    - Header comments with dependency information
    - Source component UUID and target component UUID
    - Foreign key references converted to readable names (e.g., page_template_name)
  
  Example workflows:
    1. Find theme UUID: tmcli list themes
    2. Export all dependent components: tmcli export theme <theme_uuid> ./backup/
    3. Edit exported files if needed
    4. Import to new environment: tmcli create stack ./backup/

GENERATE COMMAND DETAILS:
  The 'generate templates' command creates a complete set of example configuration
  files that demonstrate how to define themes, page templates, content, and pages.
  
  Generated files:
    - theme.yaml           : Theme configuration with CSS framework settings
    - page_template.yaml   : Page template with layout and sidebar options
    - page_content.yaml    : Template content linking to HTML template files
    - page.yaml           : Page definition with routing and metadata
    - templates/custom/my_template.html : Sample Jinja2 template file
  
  All files include realistic examples and comments to help you get started.
  After generation, edit the files with your specific values and use 'create stack'
  to build your complete template system.

UPDATE COMMAND DETAILS:
  The 'update templates' command analyzes an existing template directory and creates
  page-template-content YAML files for any HTML template files found in the templates/
  subdirectory. This is useful for:
  
  - Adding content files after placing new HTML templates
  - Automatically linking HTML templates to existing page templates
  - Completing partially configured template directories
  
  The command:
    1. Scans for existing page_template*.yaml files and extracts their UUIDs
    2. Finds all .html files in the templates/ subdirectory (recursively)
    3. Creates page_content_*.yaml files for each HTML template (if not existing)
    4. Uses actual page template UUIDs from existing YAML files
    5. Includes the HTML template source content in the YAML
  
  COMPLETE WORKFLOW:
    1. Generate initial files: tmcli generate templates ./myproject/
    2. Edit page_template.yaml with real UUIDs and names
    3. Add HTML templates to ./myproject/templates/
    4. Run: tmcli update templates ./myproject/
    5. Import complete stack: tmcli create stack ./myproject/
            """)
            return 0

        elif args.command == 'update':
            if args.component == 'templates':
                return cli.update_templates(args.config_dir)

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error during command execution: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up session
        if cli:
            cli.close()

    return 0