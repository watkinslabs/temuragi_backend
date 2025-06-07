#!/usr/bin/env python3
"""
Template CLI - Create and manage themes, templates, and pages
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
            self.menu_model = self.get_model('Menu')
            self.page_model = self.get_model('Page')
            self.page_fragments_model = self.get_model('PageFragments')  # NEW
            self.template_fragments_model = self.get_model('TemplateFragments')
            self.template_model = self.get_model('Template')
            self.theme_model = self.get_model('Theme')
            
            if not all([self.theme_model, self.template_model, self.page_model]):
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

    def list_templates(self):
        """List all templates"""
        self.log_info("Listing templates")

        try:
            templates = self.session.query(self.template_model).order_by(self.template_model.name).all()
            
            if not templates:
                self.output_warning("No templates found")
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
            
            self.output_info("Available Templates:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing templates: {e}")
            self.output_error(f"Error listing templates: {e}")
            return 1
 
    def list_template_fragments(self):
        """List all template fragments with filename and version info"""
        self.log_info("Listing template fragments")

        try:
            if not self.template_fragments_model:
                self.output_warning("TemplateFragments model not available")
                return 1

            fragments = self.session.query(self.template_fragments_model)\
                                .order_by(self.template_fragments_model.template_file_path,
                                        self.template_fragments_model.version_number.desc())\
                                .all()
            
            if not fragments:
                self.output_warning("No template fragments found")
                return 0
            
            headers = ["Template File", "Version", "Active", "Content Type", "Template", "UUID"]
            rows = []
            
            for fragment in fragments:
                template_name = ''
                if hasattr(fragment, 'template') and fragment.template:
                    template_name = fragment.template.name
                
                rows.append([
                    fragment.template_file_path,
                    fragment.get_display_version(),
                    "Yes" if fragment.is_active else "No",
                    fragment.content_type,
                    template_name,
                    str(fragment.uuid)
                ])
            
            self.output_info("Available Template Fragments:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing template fragments: {e}")
            self.output_error(f"Error listing template fragments: {e}")
            return 1

    def list_page_fragments(self):
        """List all page fragments with fragment key and version info"""
        self.log_info("Listing page fragments")

        try:
            if not self.page_fragments_model:
                self.output_warning("PageFragments model not available")
                return 1

            fragments = self.session.query(self.page_fragments_model)\
                                .order_by(self.page_fragments_model.fragment_key,
                                        self.page_fragments_model.version_number.desc())\
                                .all()
            
            if not fragments:
                self.output_warning("No page fragments found")
                return 0
            
            headers = ["Fragment Key", "Version", "Active", "Content Type", "Page", "UUID"]
            rows = []
            
            for fragment in fragments:
                page_name = ''
                if hasattr(fragment, 'page') and fragment.page:
                    page_name = fragment.page.name
                
                rows.append([
                    fragment.fragment_key,
                    fragment.get_display_version(),
                    "Yes" if fragment.is_active else "No",
                    fragment.content_type,
                    page_name,
                    str(fragment.uuid)
                ])
            
            self.output_info("Available Page Fragments:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing page fragments: {e}")
            self.output_error(f"Error listing page fragments: {e}")
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
                if hasattr(page, 'template') and page.template:  # UPDATED
                    template_name = page.template.name
                
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
                (['template.yaml', 'template_*.yaml'], 'template'),
                (['template_fragment.yaml', 'template_fragment_*.yaml'], 'template_fragment'),
                (['page.yaml'], 'page'),
                (['page_fragment.yaml', 'page_fragment_*.yaml'], 'page_fragment'),  # NEW
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
                            if not f.name.startswith('page_fragment_')]
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

                        elif component_type == 'template':
                            with open(file_path, 'r') as f:
                                template_data = yaml.safe_load(f)
                            existing = self.session.query(self.template_model).filter_by(name=template_data['name']).first()
                            was_created = existing is None
                            uuid_val = self.create_template_from_yaml(file_path, allow_update=True)

                        elif component_type == 'template_fragment':
                            uuid_val = self.create_template_fragment_from_yaml(file_path, allow_update=True)
                            was_created = True  # treat all processed as created for now (safe)

                        elif component_type == 'page':
                            with open(file_path, 'r') as f:
                                page_data = yaml.safe_load(f)
                            existing = self.session.query(self.page_model).filter_by(name=page_data['name']).first()
                            was_created = existing is None
                            uuid_val = self.create_page_from_yaml(file_path, allow_update=True)

                        elif component_type == 'page_fragment':  # NEW
                            uuid_val = self.create_page_fragment_from_yaml(file_path, allow_update=True)
                            was_created = True  # treat all processed as created for now (safe)

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

    def create_template_from_yaml(self, yaml_file, allow_update=False):
        """Create a template from YAML file"""
        self.log_info(f"Creating template from YAML file: {yaml_file}")

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
            existing = self.session.query(self.template_model).filter_by(name=template_data['name']).first()
            if existing:
                if allow_update:
                    self.output_warning(f"Template '{template_data['name']}' already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Template '{template_data['name']}' already exists (UUID: {existing.uuid})")
                    raise Exception(f"Template '{template_data['name']}' already exists")
            
            # Create template
            template = self.template_model(**template_data)
            self.session.add(template)
            self.session.commit()
            
            self.output_success(f"Created template: {template.name} (UUID: {template.uuid})")
            return template.uuid

        except Exception as e:
            self.log_error(f"Error creating template from YAML: {e}")
            self.output_error(f"Error creating template: {e}")
            self.session.rollback()
            raise

    def create_template_fragment_from_yaml(self, yaml_file, allow_update=False):
        """Create template fragment from YAML file with correct version handling"""
        self.log_info(f"Creating template fragment from YAML file: {yaml_file}")

        try:
            if not self.template_fragments_model:
                self.output_warning("TemplateFragments model not available")
                return None

            with open(yaml_file, 'r') as f:
                content_data = yaml.safe_load(f)

            # Set defaults for new fields
            if 'content_type' not in content_data:
                content_data['content_type'] = 'text/html'
            if 'is_active' not in content_data:
                content_data['is_active'] = False
            if 'cache_duration' not in content_data:
                content_data['cache_duration'] = 3600

            # Lookup template UUID
            if 'template_name' in content_data:
                content_data['template_uuid'] = self.lookup_uuid_by_name(
                    self.template_model, content_data.pop('template_name')
                )

            template_uuid = content_data['template_uuid']
            template_file_path = content_data['template_file_path']

            # If version_number not provided, get next version number
            if 'version_number' not in content_data:
                version_number = self.template_fragments_model.get_next_version_number(
                    self.session, template_uuid, template_file_path
                )
                content_data['version_number'] = version_number
            else:
                version_number = content_data['version_number']

            # Check if content already exists
            existing = self.session.query(self.template_fragments_model).filter_by(
                template_uuid=template_uuid,
                template_file_path=template_file_path,
                version_number=version_number
            ).first()

            if existing:
                if allow_update:
                    self.output_warning(f"Template fragment {template_file_path} v{version_number} already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Template fragment {template_file_path} v{version_number} already exists (UUID: {existing.uuid})")
                    raise Exception(f"Template fragment {template_file_path} v{version_number} already exists")

            # Handle template source and hash
            if 'template_source' in content_data:
                import hashlib
                template_source = content_data['template_source']
                if 'template_hash' not in content_data:
                    content_data['template_hash'] = hashlib.sha256(template_source.encode('utf-8')).hexdigest()

            # Create new template fragment
            fragment = self.template_fragments_model(**content_data)
            self.session.add(fragment)
            self.session.flush()

            # If active, deactivate other versions of same file
            if fragment.is_active:
                deactivated_count = self.session.query(self.template_fragments_model)\
                    .filter_by(template_uuid=template_uuid,
                              template_file_path=template_file_path)\
                    .filter(self.template_fragments_model.uuid != fragment.uuid)\
                    .update({'is_active': False})

            self.session.commit()

            version_display = fragment.get_display_version()
            self.output_success(f"Created template fragment: {fragment.template_file_path} {version_display} (UUID: {fragment.uuid})")
            return fragment.uuid

        except Exception as e:
            self.log_error(f"Error creating template fragment from YAML: {e}")
            self.output_error(f"Error creating template fragment: {e}")
            self.session.rollback()
            raise

    def create_page_fragment_from_yaml(self, yaml_file, allow_update=False):
        """Create page fragment from YAML file with correct version handling"""
        self.log_info(f"Creating page fragment from YAML file: {yaml_file}")

        try:
            if not self.page_fragments_model:
                self.output_warning("PageFragments model not available")
                return None

            with open(yaml_file, 'r') as f:
                content_data = yaml.safe_load(f)

            # Set defaults for new fields
            if 'content_type' not in content_data:
                content_data['content_type'] = 'text/html'
            if 'is_active' not in content_data:
                content_data['is_active'] = False
            if 'cache_duration' not in content_data:
                content_data['cache_duration'] = 3600

            # Lookup page UUID
            if 'page_name' in content_data:
                content_data['page_uuid'] = self.lookup_uuid_by_name(
                    self.page_model, content_data.pop('page_name')
                )

            page_uuid = content_data['page_uuid']
            fragment_key = content_data['fragment_key']

            # If version_number not provided, get next version number
            if 'version_number' not in content_data:
                version_number = self.page_fragments_model.get_next_version_number(
                    self.session, page_uuid, fragment_key
                )
                content_data['version_number'] = version_number
            else:
                version_number = content_data['version_number']

            # Check if content already exists
            existing = self.session.query(self.page_fragments_model).filter_by(
                page_uuid=page_uuid,
                fragment_key=fragment_key,
                version_number=version_number
            ).first()

            if existing:
                if allow_update:
                    self.output_warning(f"Page fragment {fragment_key} v{version_number} already exists (UUID: {existing.uuid})")
                    return existing.uuid
                else:
                    self.output_error(f"Page fragment {fragment_key} v{version_number} already exists (UUID: {existing.uuid})")
                    raise Exception(f"Page fragment {fragment_key} v{version_number} already exists")

            # Handle content source and hash
            if 'content_source' in content_data:
                import hashlib
                content_source = content_data['content_source']
                if 'content_hash' not in content_data:
                    content_data['content_hash'] = hashlib.sha256(content_source.encode('utf-8')).hexdigest()

            # Create new page fragment
            fragment = self.page_fragments_model(**content_data)
            self.session.add(fragment)
            self.session.flush()

            # If active, deactivate other versions of same fragment_key
            if fragment.is_active:
                deactivated_count = self.session.query(self.page_fragments_model)\
                    .filter_by(page_uuid=page_uuid,
                              fragment_key=fragment_key)\
                    .filter(self.page_fragments_model.uuid != fragment.uuid)\
                    .update({'is_active': False})

            self.session.commit()

            version_display = fragment.get_display_version()
            self.output_success(f"Created page fragment: {fragment.fragment_key} {version_display} (UUID: {fragment.uuid})")
            return fragment.uuid

        except Exception as e:
            self.log_error(f"Error creating page fragment from YAML: {e}")
            self.output_error(f"Error creating page fragment: {e}")
            self.session.rollback()
            raise

    def create_page_from_yaml(self, yaml_file, allow_update=False):
        """Create a page from YAML file"""
        self.log_info(f"Creating page from YAML file: {yaml_file}")

        try:
            with open(yaml_file, 'r') as f:
                page_data = yaml.safe_load(f)
            
            # Lookup template UUID
            if 'template_name' in page_data:
                page_data['template_uuid'] = self.lookup_uuid_by_name(
                    self.template_model, page_data.pop('template_name')
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
        """Update template directory by creating template-fragment files for template files found"""
        self.log_info(f"Updating templates in directory: {config_dir}")

        try:
            config_path = Path(config_dir)

            if not config_path.exists():
                self.output_error(f"Configuration directory '{config_dir}' not found")
                return 1

            files_created = []

            # Find existing template YAML files to get UUIDs
            template_files = []
            template_files.extend(config_path.glob('template.yaml'))
            template_files.extend(config_path.glob('template_*.yaml'))

            if not template_files:
                self.output_warning("No template YAML files found - cannot create fragment files")
                return 1

            # Extract UUIDs and names from template files
            template_info = {}
            for template_file in template_files:
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
                self.output_error("No valid template files with name/uuid found")
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
            html_template_files = []
            for ext in template_extensions:
                html_template_files.extend(templates_dir.rglob(f"*{ext}"))

            if not html_template_files:
                self.output_warning(f"No template files found in templates/ directory with extensions: {', '.join(template_extensions)}")
                return 0

            self.output_info(f"Found {len(html_template_files)} template file(s)")

            # For each template file, create a template-fragment file if it doesn't exist
            for html_template_file in html_template_files:
                # Generate relative path from config directory
                relative_path = html_template_file.relative_to(config_path)

                # Generate fragment filename based on template path
                safe_filename = str(relative_path).replace('/', '_').replace('.', '_')
                fragment_filename = f"template_fragment_{safe_filename}.yaml"
                fragment_file = config_path / fragment_filename

                if fragment_file.exists():
                    self.output_info(f"Skipping {fragment_filename} - already exists")
                    continue

                # Determine which template to use (for now, use the first one)
                template_name = list(template_info.keys())[0]
                template_uuid = template_info[template_name]

                if not self.template_fragments_model:
                    self.output_warning("TemplateFragments model not available")
                    continue

                # Determine content type from file extension
                file_extension = html_template_file.suffix.lower()
                content_type = content_type_map.get(file_extension, 'text/plain')

                # Read the template file content
                try:
                    with open(html_template_file, 'r', encoding='utf-8') as f:
                        template_source = f.read()
                except Exception as e:
                    self.log_warning(f"Could not read template file {html_template_file}: {e}")
                    template_source = f"# Could not read template source from {relative_path}"

                # Calculate template hash for change detection
                import hashlib
                template_hash = hashlib.sha256(template_source.encode('utf-8')).hexdigest()

                # Get next version number for this template
                next_version = self.template_fragments_model.get_next_version_number(
                    self.session, template_uuid, str(relative_path)
                )

                # Create dummy template fragment object with all necessary fields
                fragment_dummy = self.template_fragments_model()
                fragment_dummy.template_uuid = template_uuid
                fragment_dummy.template_file_path = str(relative_path)
                fragment_dummy.content_type = content_type

                # Use versioning system
                fragment_dummy.version_number = next_version
                fragment_dummy.version_label = None  # No label for initial template
                fragment_dummy.is_active = True  # Template versions default to active

                fragment_dummy.cache_duration = 3600
                fragment_dummy.template_hash = template_hash
                fragment_dummy.template_source = template_source  # Always store content
                fragment_dummy.change_description = f"Initial template version for {relative_path}"

                # Set compiled file path
                compiled_path = str(relative_path).replace(file_extension, '.pyc')
                fragment_dummy.compiled_file_path = f"compiled_templates/{compiled_path}"

                # Set relationship attribute
                fragment_dummy.template_name = template_name

                fragment_mappings = {
                    'template_uuid': 'name'
                }

                self.exporter.export_model_object(
                    fragment_dummy,
                    fragment_file,
                    fragment_mappings,
                    header_title=f"Template Fragment for {relative_path}",
                    header_description=f"Auto-generated for template: {relative_path}, linked to template: {template_name}",
                    template_mode=True
                )

                files_created.append(str(fragment_file))
                self.output_success(f"Created: {fragment_filename}")

            if files_created:
                self.output_success(f"Created {len(files_created)} template fragment file(s)")
                self.output_info("Files created:")
                for file_path in files_created:
                    self.output_info(f"   {Path(file_path).name}")
            else:
                self.output_info("No new template fragment files needed")

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

            # Create dummy template object
            template_dummy = self.template_model()
            template_dummy.name = 'my-template'
            template_dummy.display_name = 'My Template'
            template_dummy.description = 'Custom template for my application'
            template_dummy.uuid = 'EXAMPLE-TEMPLATE-UUID-REPLACE-ME'
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

            template_file = output_path / "template.yaml"
            self.exporter.export_model_object(
                template_dummy,
                template_file,
                foreign_key_mappings,
                header_title="Example Template Configuration",
                header_description="Edit values and replace UUIDs before importing"
            )
            files_created.append(str(template_file))

            # Create dummy template fragment if model exists
            if self.template_fragments_model:
                fragment_dummy = self.template_fragments_model()
                fragment_dummy.template_uuid = 'EXAMPLE-TEMPLATE-UUID-REPLACE-ME'
                fragment_dummy.template_file_path = 'templates/custom/my_template.html'
                fragment_dummy.compiled_file_path = 'compiled_templates/custom/my_template.pyc'
                fragment_dummy.uuid = 'EXAMPLE-TEMPLATE-FRAGMENT-UUID-REPLACE-ME'

                # Set versioning fields
                fragment_dummy.version_number = 1
                fragment_dummy.version_label = None
                fragment_dummy.is_active = True

                # Set content type and template source
                fragment_dummy.content_type = 'text/html'
                fragment_dummy.template_source = 'See templates/custom/my_template.html'
                fragment_dummy.cache_duration = 3600
                fragment_dummy.change_description = 'Initial template version'

                # Calculate hash for example content
                import hashlib
                fragment_dummy.template_hash = hashlib.sha256(
                    fragment_dummy.template_source.encode('utf-8')
                ).hexdigest()

                # Set relationship attribute directly
                fragment_dummy.template_name = 'my-template'

                fragment_mappings = {
                    'template_uuid': 'name'
                }

                fragment_file = output_path / "template_fragment.yaml"
                self.exporter.export_model_object(
                    fragment_dummy,
                    fragment_file,
                    fragment_mappings,
                    header_title="Example Template Fragment Configuration",
                    header_description="Edit values and replace UUIDs before importing"
                )
                files_created.append(str(fragment_file))

            # Create dummy page object
            page_dummy = self.page_model()
            page_dummy.name = 'my-custom-page'
            page_dummy.title = 'My Custom Page'
            page_dummy.description = 'A custom page in my application'
            page_dummy.route = '/my-page'
            page_dummy.template_uuid = 'EXAMPLE-TEMPLATE-UUID-REPLACE-ME'  # UPDATED
            page_dummy.uuid = 'EXAMPLE-PAGE-UUID-REPLACE-ME'

            # Set other likely fields
            if hasattr(page_dummy, 'meta_description'):
                page_dummy.meta_description = 'SEO description for my custom page'
            if hasattr(page_dummy, 'published'):
                page_dummy.published = True

            # Set relationship attribute directly
            page_dummy.template_name = 'my-template'

            page_mappings = {
                'template_uuid': 'name'  # UPDATED
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

            # Create dummy page fragment if model exists
            if self.page_fragments_model:
                page_fragment_dummy = self.page_fragments_model()
                page_fragment_dummy.page_uuid = 'EXAMPLE-PAGE-UUID-REPLACE-ME'
                page_fragment_dummy.fragment_key = 'main_content'
                page_fragment_dummy.uuid = 'EXAMPLE-PAGE-FRAGMENT-UUID-REPLACE-ME'

                # Set versioning fields
                page_fragment_dummy.version_number = 1
                page_fragment_dummy.version_label = None
                page_fragment_dummy.is_active = True

                # Set content type and source
                page_fragment_dummy.content_type = 'text/html'
                page_fragment_dummy.content_source = '<p>Main page content goes here</p>'
                page_fragment_dummy.cache_duration = 3600
                page_fragment_dummy.change_description = 'Initial page content'

                # Calculate hash for example content
                import hashlib
                page_fragment_dummy.content_hash = hashlib.sha256(
                    page_fragment_dummy.content_source.encode('utf-8')
                ).hexdigest()

                # Set relationship attribute directly
                page_fragment_dummy.page_name = 'my-custom-page'

                page_fragment_mappings = {
                    'page_uuid': 'name'
                }

                page_fragment_file = output_path / "page_fragment.yaml"
                self.exporter.export_model_object(
                    page_fragment_dummy,
                    page_fragment_file,
                    page_fragment_mappings,
                    header_title="Example Page Fragment Configuration",
                    header_description="Edit values and replace UUIDs before importing"
                )
                files_created.append(str(page_fragment_file))

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
            {# Page fragments will be rendered here #}
            {% for fragment in page.page_fragments if fragment.is_active %}
            <div class="page-fragment" data-fragment="{{ fragment.fragment_key }}">
                {{ fragment.content_source|safe }}
            </div>
            {% endfor %}
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

    def export_theme_by_uuid(self, theme_uuid, output_path):
        """Export a specific theme by UUID"""
        self.log_info(f"Exporting theme by UUID: {theme_uuid}")
        
        # Find the theme
        theme = self.session.query(self.theme_model).filter_by(uuid=theme_uuid).first()
        if not theme:
            self.output_error(f"Theme with UUID {theme_uuid} not found")
            return 1
        
        # Determine if output_path is a file or directory
        output_path_obj = Path(output_path)
        if output_path_obj.suffix in ['.yaml', '.yml']:
            # It's a filename
            output_file = output_path_obj
        else:
            # It's a directory, generate filename
            filename = f"theme_{theme.name}.yaml"
            output_file = output_path_obj / filename
        
        return self.exporter.export_model_object(
            theme, 
            output_file,
            header_title=f"Theme '{theme.name}'"
        )

    def export_template_by_uuid(self, template_uuid, output_path):  
        """Export a specific template by UUID"""
        self.log_info(f"Exporting template by UUID: {template_uuid}")
        
        template = self.session.query(self.template_model).filter_by(uuid=template_uuid).first()
        if not template:
            self.output_error(f"Template with UUID {template_uuid} not found")
            return 1
        
        # Define foreign key mappings for templates
        foreign_key_mappings = {
            'theme_uuid': 'name',
            'menu_type_uuid': 'name'
        }
        
        # Determine output file
        output_path_obj = Path(output_path)
        if output_path_obj.suffix in ['.yaml', '.yml']:
            output_file = output_path_obj
        else:
            filename = f"template_{template.name}.yaml"
            output_file = output_path_obj / filename
        
        return self.exporter.export_model_object(
            template,
            output_file,
            foreign_key_mappings,
            header_title=f"Template '{template.name}'"
        )

    def export_template_fragment_by_uuid(self, fragment_uuid, output_path):  
        """Export specific template fragment by UUID"""
        self.log_info(f"Exporting template fragment by UUID: {fragment_uuid}")
        
        if not self.template_fragments_model:
            self.output_warning("TemplateFragments model not available")
            return 1
        
        fragment = self.session.query(self.template_fragments_model).filter_by(uuid=fragment_uuid).first()
        if not fragment:
            self.output_error(f"Template fragment with UUID {fragment_uuid} not found")
            return 1
        
        foreign_key_mappings = {
            'template_uuid': 'name'
        }
        
        output_path_obj = Path(output_path)
        if output_path_obj.suffix in ['.yaml', '.yml']:
            output_file = output_path_obj
        else:
            safe_filename = fragment.template_file_path.replace('/', '_').replace('.', '_')
            filename = f"template_fragment_{safe_filename}.yaml"
            output_file = output_path_obj / filename
        
        return self.exporter.export_model_object(
            fragment,
            output_file,
            foreign_key_mappings,
            header_title="Template Fragment",
            header_description=f"Template: {fragment.template_file_path}"
        )

    def export_page_fragment_by_uuid(self, fragment_uuid, output_path):  
        """Export specific page fragment by UUID"""
        self.log_info(f"Exporting page fragment by UUID: {fragment_uuid}")
        
        if not self.page_fragments_model:
            self.output_warning("PageFragments model not available")
            return 1
        
        fragment = self.session.query(self.page_fragments_model).filter_by(uuid=fragment_uuid).first()
        if not fragment:
            self.output_error(f"Page fragment with UUID {fragment_uuid} not found")
            return 1
        
        foreign_key_mappings = {
            'page_uuid': 'name'
        }
        
        output_path_obj = Path(output_path)
        if output_path_obj.suffix in ['.yaml', '.yml']:
            output_file = output_path_obj
        else:
            safe_fragment_key = fragment.fragment_key.replace('/', '_').replace('.', '_')
            filename = f"page_fragment_{safe_fragment_key}.yaml"
            output_file = output_path_obj / filename
        
        return self.exporter.export_model_object(
            fragment,
            output_file,
            foreign_key_mappings,
            header_title="Page Fragment",
            header_description=f"Fragment: {fragment.fragment_key}"
        )

    def export_page_by_uuid(self, page_uuid, output_path):
        """Export a specific page by UUID"""
        self.log_info(f"Exporting page by UUID: {page_uuid}")
        
        # Find the page
        page = self.session.query(self.page_model).filter_by(uuid=page_uuid).first()
        if not page:
            self.output_error(f"Page with UUID {page_uuid} not found")
            return 1
        
        # Define foreign key mappings for pages
        foreign_key_mappings = {
            'template_uuid': 'name'  # UPDATED
        }
        
        # Determine if output_path is a file or directory
        output_path_obj = Path(output_path)
        if output_path_obj.suffix in ['.yaml', '.yml']:
            # It's a filename
            output_file = output_path_obj
        else:
            # It's a directory, generate filename
            filename = f"page_{page.name}.yaml"
            output_file = output_path_obj / filename
        
        return self.exporter.export_model_object(
            page,
            output_file,
            foreign_key_mappings,
            header_title=f"Page '{page.name}'"
        )

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
    create_parser.add_argument('component', choices=['theme', 'template', 'template_fragment', 'page', 'page_fragment', 'stack'],
                              help='Component type to create')
    create_parser.add_argument('file_or_dir', help='YAML file or directory path')

    # List commands
    list_parser = subparsers.add_parser('list', help='List components')
    list_parser.add_argument('component', choices=['themes', 'templates', 'fragments', 'pages', 'page_fragments'],
                            help='Component type to list')

    # Export commands with subparsers
    export_parser = subparsers.add_parser('export', help='Export individual components by UUID')
    export_subparsers = export_parser.add_subparsers(dest='export_component', help='Component type to export')
    
    # Export theme
    export_theme_parser = export_subparsers.add_parser('theme', help='Export theme by UUID')
    export_theme_parser.add_argument('uuid', help='UUID of theme to export')
    export_theme_parser.add_argument('output_path', help='Output filename (with .yaml/.yml extension) or directory')
    
    # Export template  
    export_template_parser = export_subparsers.add_parser('template', help='Export template by UUID')
    export_template_parser.add_argument('uuid', help='UUID of template to export')
    export_template_parser.add_argument('output_path', help='Output filename (with .yaml/.yml extension) or directory')
    
    # Export page
    export_page_parser = export_subparsers.add_parser('page', help='Export page by UUID')
    export_page_parser.add_argument('uuid', help='UUID of page to export')
    export_page_parser.add_argument('output_path', help='Output filename (with .yaml/.yml extension) or directory')
    
    # Export template fragment
    export_fragment_parser = export_subparsers.add_parser('template_fragment', help='Export template fragment by UUID')
    export_fragment_parser.add_argument('uuid', help='UUID of template fragment to export')
    export_fragment_parser.add_argument('output_path', help='Output filename (with .yaml/.yml extension) or directory')

    # Export page fragment
    export_page_fragment_parser = export_subparsers.add_parser('page_fragment', help='Export page fragment by UUID')
    export_page_fragment_parser.add_argument('uuid', help='UUID of page fragment to export')
    export_page_fragment_parser.add_argument('output_path', help='Output filename (with .yaml/.yml extension) or directory')

    # Generate commands
    generate_parser = subparsers.add_parser('generate', help='Generate template files')
    generate_parser.add_argument('component', choices=['templates'], 
                                help='templates - Generate example YAML configuration files for all template components')
    generate_parser.add_argument('output_dir', help='Directory where template files will be created')

    # Update commands
    update_parser = subparsers.add_parser('update', help='Update template directories')
    update_parser.add_argument('component', choices=['templates'], 
                              help='templates - Create template-fragment files for HTML templates found in directory')
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
            elif args.component == 'template':
                cli.create_template_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'template_fragment':
                cli.create_template_fragment_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'page':
                cli.create_page_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'page_fragment':
                cli.create_page_fragment_from_yaml(args.file_or_dir)
                return 0
            elif args.component == 'stack':
                return cli.create_full_stack(args.file_or_dir)

        elif args.command == 'list':
            if args.component == 'themes':
                return cli.list_themes()
            elif args.component == 'templates':
                return cli.list_templates()
            elif args.component == 'fragments':
                return cli.list_template_fragments()
            elif args.component == 'pages':
                return cli.list_pages()
            elif args.component == 'page_fragments':
                return cli.list_page_fragments()

        elif args.command == 'export':
            if args.export_component == 'theme':
                return cli.export_theme_by_uuid(args.uuid, args.output_path)
            elif args.export_component == 'template':
                return cli.export_template_by_uuid(args.uuid, args.output_path)
            elif args.export_component == 'page':
                return cli.export_page_by_uuid(args.uuid, args.output_path)
            elif args.export_component == 'template_fragment':
                return cli.export_template_fragment_by_uuid(args.uuid, args.output_path)
            elif args.export_component == 'page_fragment':
                return cli.export_page_fragment_by_uuid(args.uuid, args.output_path)
            else:
                export_parser.print_help()
                return 1

        elif args.command == 'generate':
            if args.component == 'templates':
                return cli.generate_yaml_templates(args.output_dir)

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

if __name__ == '__main__':
    sys.exit(main())