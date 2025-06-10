from pathlib import Path
from collections import defaultdict, deque
import yaml


class ImportDependencyResolver:
    """Resolves import order based on model __depends_on__ attributes"""

    def __init__(self, session, output_manager, model_registry_getter):
        self.session = session
        self.output_manager = output_manager
        self.get_model = model_registry_getter

    def get_model_from_file(self, file_path):
        """Extract model name from YAML file"""
        try:
            with open(file_path, 'r') as f:
                # Skip comment lines
                lines = [line for line in f if not line.strip().startswith('#')]
                content = '\n'.join(lines)

            yaml_data = yaml.safe_load(content)
            if yaml_data:
                # Return first model name found
                return list(yaml_data.keys())[0]
            return None

        except Exception as e:
            self.output_manager.log_error(f"Error reading {file_path}: {e}")
            return None

    def resolve_model_import_order(self, model_names):
        """Resolve import order based on __depends_on__ attributes and nullable foreign keys"""
        # Build dependency graph
        dependency_graph = {}
        available_models = set(model_names)
        missing_dependencies = set()

        for model_name in model_names:
            model_class = self.get_model(model_name)
            if model_class:
                depends_on = getattr(model_class, '__depends_on__', [])
                # Filter dependencies based on availability and nullability
                filtered_deps = []

                for dep in depends_on:
                    if dep in available_models:
                        filtered_deps.append(dep)
                    else:
                        # Check if this dependency is from a nullable foreign key
                        if self._is_dependency_nullable(model_class, dep):
                            self.output_manager.log_debug(f"Skipping nullable dependency: {model_name} -> {dep}")
                        else:
                            missing_dependencies.add(dep)
                            self.output_manager.log_warning(f"Missing required dependency: {model_name} depends on {dep} (no file found)")

                dependency_graph[model_name] = filtered_deps
            else:
                self.output_manager.log_warning(f"Model {model_name} not found")
                dependency_graph[model_name] = []

        # Report missing dependencies
        if missing_dependencies:
            self.output_manager.output_warning(f"Missing required dependencies: {', '.join(sorted(missing_dependencies))}")
            self.output_manager.output_info("These models should already exist in the database")

        # Topological sort
        return self._topological_sort(dependency_graph, model_names)

    def _is_dependency_nullable(self, model_class, dependency_model_name):
        """Check if the foreign key to dependency_model is nullable"""
        try:
            # Get the dependency model class to find its table name
            dep_model_class = self.get_model(dependency_model_name)
            if not dep_model_class:
                return False

            dep_table_name = dep_model_class.__tablename__

            # Look for foreign key columns that reference the dependency table
            for column in model_class.__table__.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        if fk.column.table.name == dep_table_name:
                            # Check if this foreign key column is nullable
                            return column.nullable

            return False

        except Exception as e:
            self.output_manager.log_debug(f"Error checking nullability for {model_class.__name__} -> {dependency_model_name}: {e}")
            return False

    def _topological_sort(self, dependency_graph, target_models):
        """Perform topological sort on dependency graph"""
        # Only work with models we actually have files for
        filtered_graph = {model: deps for model, deps in dependency_graph.items() if model in target_models}

        # Count incoming edges for each model (how many things each model depends on)
        in_degree = {}

        # Initialize in_degree for all target models to 0
        for model in filtered_graph:
            in_degree[model] = len([dep for dep in filtered_graph[model] if dep in filtered_graph])

        # Find models with no dependencies
        queue = deque([model for model in filtered_graph if in_degree[model] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # For each model that depends on current, reduce its dependency count
            for model in filtered_graph:
                if current in filtered_graph[model]:
                    in_degree[model] -= 1
                    if in_degree[model] == 0:
                        queue.append(model)

        # Check for circular dependencies
        if len(result) != len(filtered_graph):
            remaining = set(filtered_graph.keys()) - set(result)
            self.output_manager.output_error(f"Circular dependencies detected among: {remaining}")

            # Show the problematic dependencies
            for model in remaining:
                remaining_deps = [dep for dep in filtered_graph[model] if dep in remaining]
                if remaining_deps:
                    self.output_manager.output_error(f"  {model} depends on: {remaining_deps}")
                else:
                    self.output_manager.output_error(f"  {model} has no remaining dependencies but wasn't processed")

            return []

        return result

    def resolve_import_order(self, directory_path):
        """Resolve import order for all YAML files in directory (recursive)"""
        directory = Path(directory_path)
        if not directory.exists():
            self.output_manager.output_error(f"Directory not found: {directory_path}")
            return []

        # Find all YAML files recursively
        yaml_files = list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))

        if not yaml_files:
            self.output_manager.output_warning(f"No YAML files found in {directory_path}")
            return []

        # Map files to models - FIXED: Use defaultdict to store multiple files per model
        file_to_model = {}
        model_to_files = defaultdict(list)

        for file_path in yaml_files:
            model_name = self.get_model_from_file(file_path)
            if model_name:
                file_to_model[str(file_path)] = model_name
                model_to_files[model_name].append(file_path)

        if not file_to_model:
            self.output_manager.output_error("No valid model files found")
            return []

        # Get unique model names
        model_names = list(set(file_to_model.values()))

        # Resolve order by model dependencies
        ordered_models = self.resolve_model_import_order(model_names)

        if not ordered_models:
            self.output_manager.output_error("Could not resolve import order")
            return []

        # Convert back to file paths - FIXED: Include ALL files for each model
        ordered_files = []
        for model_name in ordered_models:
            if model_name in model_to_files:
                # Sort files within each model for consistent ordering
                model_files = sorted(model_to_files[model_name], key=lambda p: p.name)
                ordered_files.extend(model_files)

        return ordered_files

    def import_directory_ordered(self, directory_path, dry_run=False, update_existing=False):
        """Import all YAML files in dependency order"""
        self.output_manager.log_operation_start("Directory Import", f"Path: {directory_path}")

        try:
            # Resolve import order
            ordered_files = self.resolve_import_order(directory_path)

            if not ordered_files:
                self.output_manager.output_error("No files to import or dependency resolution failed")
                return 1

            # Display import order with relative paths
            self.output_manager.output_info("Import order resolved:")
            for i, file_path in enumerate(ordered_files, 1):
                model_name = self.get_model_from_file(file_path)
                rel_path = file_path.relative_to(Path(directory_path))
                display_name = f"{model_name} ({rel_path})" if model_name else str(rel_path)
                self.output_manager.output_info(f"  {i}. {display_name}")

            if dry_run:
                self.output_manager.output_info("DRY RUN: Would import files in the order shown above")
                return 0

            # Import files in order
            successful = 0
            failed = 0

            for i, file_path in enumerate(ordered_files, 1):
                try:
                    rel_path = file_path.relative_to(Path(directory_path))
                    self.output_manager.output_info(f"Importing {i}/{len(ordered_files)}: {rel_path}")

                    # Use existing importer
                    from .importer import ComponentImporter
                    importer = ComponentImporter(self.session, self.output_manager, self.get_model)

                    result = importer.import_yaml_file(
                        file_path=file_path,
                        dry_run=False,
                        update_existing=update_existing
                    )

                    if result == 0:
                        successful += 1
                        self.output_manager.output_success(f"✓ Imported {rel_path}")
                    else:
                        failed += 1
                        self.output_manager.output_error(f"✗ Failed to import {rel_path}")

                except Exception as e:
                    failed += 1
                    rel_path = file_path.relative_to(Path(directory_path)) if hasattr(file_path, 'relative_to') else file_path.name
                    self.output_manager.log_error(f"Error importing {file_path}: {e}")
                    self.output_manager.output_error(f"✗ Error importing {rel_path}: {e}")

            # Summary
            total = len(ordered_files)
            if failed == 0:
                self.output_manager.output_success(f"Successfully imported all {successful} files")
                self.output_manager.log_operation_end("Directory Import", True, f"{successful}/{total} files")
                return 0
            else:
                self.output_manager.output_warning(f"Imported {successful}/{total} files, {failed} failed")
                self.output_manager.log_operation_end("Directory Import", False, f"{successful}/{total} files")
                return 1

        except Exception as e:
            self.output_manager.log_error(f"Directory import failed: {e}")
            self.output_manager.output_error(f"Directory import failed: {e}")
            self.output_manager.log_operation_end("Directory Import", False, str(e))
            return 1

    def analyze_directory_dependencies(self, directory_path):
        """Analyze and display dependency information for directory (recursive)"""
        directory = Path(directory_path)
        yaml_files = list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))

        if not yaml_files:
            self.output_manager.output_info("No YAML files found")
            return 0

        self.output_manager.output_info(f"Dependency Analysis for {len(yaml_files)} files:")
        print()

        # Analyze each file
        file_info = []
        model_names = []
        all_dependencies = set()

        for file_path in yaml_files:
            model_name = self.get_model_from_file(file_path)
            if model_name:
                model_class = self.get_model(model_name)
                depends_on = getattr(model_class, '__depends_on__', []) if model_class else []

                file_info.append({
                    'file': str(file_path),  # Keep full path for processing
                    'model': model_name,
                    'depends_on': depends_on
                })
        # Get unique model names for dependency analysis
        model_names = list(set(info['model'] for info in file_info))
        all_dependencies.update(depends_on)

        # Display dependencies
        headers = ['File', 'Path', 'Model', 'Depends On']
        rows = []

        for info in file_info:
            deps_str = ', '.join(info['depends_on']) if info['depends_on'] else 'None'
            # Show relative path from base directory
            rel_path = str(Path(info['file']).parent.relative_to(directory)) if Path(info['file']).parent != directory else '.'
            rows.append([Path(info['file']).name, rel_path, info['model'], deps_str])

        self.output_manager.output_table(rows, headers=headers)

        # Check for missing dependencies
        available_models = set(model_names)
        missing_deps = all_dependencies - available_models
        nullable_deps = set()
        required_deps = set()

        # Categorize missing dependencies by nullability
        for model_name in model_names:
            model_class = self.get_model(model_name)
            if model_class:
                depends_on = getattr(model_class, '__depends_on__', [])
                for dep in depends_on:
                    if dep not in available_models:
                        if self._is_dependency_nullable(model_class, dep):
                            nullable_deps.add(dep)
                        else:
                            required_deps.add(dep)

        if nullable_deps or required_deps:
            print()
            if nullable_deps:
                self.output_manager.output_info(f"Optional dependencies (nullable FKs, will be skipped):")
                for dep in sorted(nullable_deps):
                    self.output_manager.output_info(f"  - {dep}")

            if required_deps:
                self.output_manager.output_warning(f"Required dependencies (missing files):")
                for dep in sorted(required_deps):
                    self.output_manager.output_warning(f"  - {dep}")
                self.output_manager.output_info("These models should already exist in the database")

        # Show resolved order
        if model_names:
            ordered_models = self.resolve_model_import_order(model_names)
            if ordered_models:
                print()
                self.output_manager.output_success("Resolved import order:")
                for i, model_name in enumerate(ordered_models, 1):
                    self.output_manager.output_info(f"  {i}. {model_name}")
            else:
                print()
                self.output_manager.output_error("Could not resolve import order - check for circular dependencies")

        return 0