from pathlib import Path
from collections import defaultdict, deque
import yaml


class ImportDependencyResolver:
    __depends_on__ = ['ComponentImporter']

    def __init__(self, output_manager, model_registry_getter):
        self.output_manager = output_manager
        self.get_model = model_registry_getter

    def get_model_from_file(self, file_path):
        """Extract model name from YAML file"""
        self.output_manager.log_debug(f"Reading model from file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                raw_content = f.read()
                # Skip comment lines
                lines = [line for line in raw_content.splitlines() if not line.strip().startswith('#')]
                content = '\n'.join(lines)

            # Check if file is empty after removing comments
            if not content.strip():
                error_msg = "File is empty or contains only comments"
                self.output_manager.log_error(f"{file_path}: {error_msg}")
                return None, error_msg

            yaml_data = yaml.safe_load(content)
            if yaml_data:
                if not isinstance(yaml_data, dict):
                    error_msg = f"Invalid YAML structure: expected dict, got {type(yaml_data).__name__}"
                    self.output_manager.log_error(f"{file_path}: {error_msg}")
                    return None, error_msg
                
                # Return first model name found
                model_name = list(yaml_data.keys())[0]
                self.output_manager.log_debug(f"Found model '{model_name}' in {file_path}")
                
                # Validate model name
                if not model_name or not isinstance(model_name, str):
                    error_msg = f"Invalid model name: {model_name}"
                    self.output_manager.log_error(f"{file_path}: {error_msg}")
                    return None, error_msg
                    
                return model_name, None
            else:
                error_msg = "YAML file parsed but contains no data"
                self.output_manager.log_warning(f"{file_path}: {error_msg}")
                return None, error_msg

        except yaml.YAMLError as e:
            error_msg = f"YAML syntax error: {str(e)}"
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                error_msg += f" (line {mark.line + 1}, column {mark.column + 1})"
            self.output_manager.log_error(f"{file_path}: {error_msg}")
            return None, error_msg
        except FileNotFoundError:
            error_msg = "File not found"
            self.output_manager.log_error(f"{file_path}: {error_msg}")
            return None, error_msg
        except PermissionError:
            error_msg = "Permission denied"
            self.output_manager.log_error(f"{file_path}: {error_msg}")
            return None, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"File encoding error: {e}"
            self.output_manager.log_error(f"{file_path}: {error_msg}")
            return None, error_msg
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.output_manager.log_error(f"{file_path}: Unexpected error - {error_msg}")
            return None, error_msg

    def resolve_model_import_order(self, model_names):
        """Resolve import order based on __depends_on__ attributes and nullable foreign keys"""
        self.output_manager.log_info(f"Starting dependency resolution for {len(model_names)} models")
        self.output_manager.log_debug(f"Models to resolve: {sorted(model_names)}")
        
        # Build dependency graph
        dependency_graph = {}
        available_models = set(model_names)
        missing_dependencies = set()
        nullable_dependencies = set()

        for model_name in model_names:
            self.output_manager.log_debug(f"Processing dependencies for model: {model_name}")
            model_class = self.get_model(model_name)
            
            if model_class:
                self.output_manager.log_debug(f"Model class found for {model_name}: {model_class.__name__}")
                depends_on = getattr(model_class, '__depends_on__', [])
                self.output_manager.log_debug(f"{model_name} raw dependencies: {depends_on}")
                
                # Check table name
                if hasattr(model_class, '__tablename__'):
                    self.output_manager.log_debug(f"{model_name} table name: {model_class.__tablename__}")
                
                # Filter dependencies based on availability and nullability
                filtered_deps = []

                for dep in depends_on:
                    if dep in available_models:
                        filtered_deps.append(dep)
                        self.output_manager.log_debug(f"Dependency {dep} is available for {model_name}")
                    else:
                        # Check if this dependency is from a nullable foreign key
                        is_nullable = self._is_dependency_nullable(model_class, dep)
                        if is_nullable:
                            nullable_dependencies.add(f"{model_name}->{dep}")
                            self.output_manager.log_info(f"Skipping nullable dependency: {model_name} -> {dep}")
                        else:
                            missing_dependencies.add(dep)
                            self.output_manager.log_warning(f"Missing REQUIRED dependency: {model_name} -> {dep}")

                dependency_graph[model_name] = filtered_deps
                self.output_manager.log_debug(f"{model_name} filtered dependencies: {filtered_deps}")
            else:
                self.output_manager.log_error(f"Model class NOT FOUND for {model_name}")
                self.output_manager.log_debug(f"Attempted to retrieve model using: get_model('{model_name}')")
                dependency_graph[model_name] = []

        # Log dependency graph summary
        self.output_manager.log_info("Dependency graph built:")
        for model, deps in dependency_graph.items():
            if deps:
                self.output_manager.log_info(f"  {model} -> {deps}")
            else:
                self.output_manager.log_info(f"  {model} -> No dependencies")

        # Report missing dependencies
        if missing_dependencies:
            self.output_manager.output_warning(f"Missing required dependencies: {', '.join(sorted(missing_dependencies))}")
            self.output_manager.output_info("These models should already exist in the database")
            self.output_manager.log_error(f"Total missing required dependencies: {len(missing_dependencies)}")

        if nullable_dependencies:
            self.output_manager.log_info(f"Total nullable dependencies skipped: {len(nullable_dependencies)}")

        # Topological sort
        result = self._topological_sort(dependency_graph, model_names)
        
        if result:
            self.output_manager.log_info(f"Successfully resolved import order for {len(result)} models")
        else:
            self.output_manager.log_error("Failed to resolve import order")
            
        return result

    def _is_dependency_nullable(self, model_class, dependency_model_name):
        """Check if the foreign key to dependency_model is nullable"""
        self.output_manager.log_debug(f"Checking nullability: {model_class.__name__} -> {dependency_model_name}")
        
        try:
            # Get the dependency model class to find its table name
            dep_model_class = self.get_model(dependency_model_name)
            if not dep_model_class:
                self.output_manager.log_debug(f"Dependency model class not found: {dependency_model_name}")
                return False

            dep_table_name = dep_model_class.__tablename__
            self.output_manager.log_debug(f"Dependency table name: {dep_table_name}")

            # Check if model has __table__ attribute
            if not hasattr(model_class, '__table__'):
                self.output_manager.log_warning(f"Model {model_class.__name__} has no __table__ attribute")
                return False

            # Look for foreign key columns that reference the dependency table
            nullable_fks = []
            non_nullable_fks = []
            
            for column in model_class.__table__.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        fk_table = fk.column.table.name
                        if fk_table == dep_table_name:
                            if column.nullable:
                                nullable_fks.append(column.name)
                                self.output_manager.log_debug(f"Found nullable FK: {column.name} -> {fk_table}")
                            else:
                                non_nullable_fks.append(column.name)
                                self.output_manager.log_debug(f"Found non-nullable FK: {column.name} -> {fk_table}")

            if nullable_fks and not non_nullable_fks:
                self.output_manager.log_info(f"All FKs from {model_class.__name__} to {dependency_model_name} are nullable")
                return True
            elif non_nullable_fks:
                self.output_manager.log_debug(f"Found non-nullable FK(s) from {model_class.__name__} to {dependency_model_name}")
                return False
            else:
                self.output_manager.log_debug(f"No foreign keys found from {model_class.__name__} to {dependency_model_name}")
                return False

        except AttributeError as e:
            self.output_manager.log_error(f"AttributeError checking nullability for {model_class.__name__} -> {dependency_model_name}: {e}")
            return False
        except Exception as e:
            self.output_manager.log_error(f"Unexpected error checking nullability for {model_class.__name__} -> {dependency_model_name}: {type(e).__name__}: {e}")
            return False

    def _topological_sort(self, dependency_graph, target_models):
        """Perform topological sort on dependency graph"""
        self.output_manager.log_debug("Starting topological sort")
        
        # Only work with models we actually have files for
        filtered_graph = {model: deps for model, deps in dependency_graph.items() if model in target_models}
        self.output_manager.log_debug(f"Filtered graph contains {len(filtered_graph)} models")

        # Count incoming edges for each model
        in_degree = {}

        # Initialize in_degree for all target models to 0
        for model in filtered_graph:
            in_degree[model] = len([dep for dep in filtered_graph[model] if dep in filtered_graph])
            self.output_manager.log_debug(f"Model {model} has in-degree: {in_degree[model]}")

        # Find models with no dependencies
        queue = deque([model for model in filtered_graph if in_degree[model] == 0])
        self.output_manager.log_debug(f"Initial queue (no dependencies): {list(queue)}")
        
        result = []
        iteration = 0

        while queue:
            iteration += 1
            current = queue.popleft()
            result.append(current)
            self.output_manager.log_debug(f"Iteration {iteration}: Processing {current}")

            # For each model that depends on current, reduce its dependency count
            for model in filtered_graph:
                if current in filtered_graph[model]:
                    in_degree[model] -= 1
                    self.output_manager.log_debug(f"  Reduced in-degree of {model} to {in_degree[model]}")
                    if in_degree[model] == 0:
                        queue.append(model)
                        self.output_manager.log_debug(f"  Added {model} to queue")

        # Check for circular dependencies
        if len(result) != len(filtered_graph):
            remaining = set(filtered_graph.keys()) - set(result)
            self.output_manager.output_error(f"Circular dependencies detected among: {remaining}")
            self.output_manager.log_error(f"Topological sort failed - {len(remaining)} models have circular dependencies")

            # Show the problematic dependencies with more detail
            for model in remaining:
                remaining_deps = [dep for dep in filtered_graph[model] if dep in remaining]
                all_deps = filtered_graph[model]
                if remaining_deps:
                    self.output_manager.output_error(f"  {model} depends on: {remaining_deps} (circular)")
                    self.output_manager.log_error(f"  {model} all dependencies: {all_deps}, circular: {remaining_deps}")
                else:
                    self.output_manager.output_error(f"  {model} has no remaining dependencies but wasn't processed")
                    self.output_manager.log_error(f"  {model} may be part of a circular dependency chain")

            return []

        self.output_manager.log_info(f"Topological sort completed successfully. Order: {result}")
        return result

    def resolve_import_order(self, directory_path):
        """Resolve import order for all YAML files in directory (recursive)"""
        self.output_manager.log_info(f"Resolving import order for directory: {directory_path}")
        
        directory = Path(directory_path)
        if not directory.exists():
            self.output_manager.output_error(f"Directory not found: {directory_path}")
            return []

        # Find all YAML files recursively
        yaml_files = list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))
        self.output_manager.log_info(f"Found {len(yaml_files)} YAML files in {directory_path}")

        if not yaml_files:
            self.output_manager.output_warning(f"No YAML files found in {directory_path}")
            return []

        # Log all found files
        self.output_manager.log_debug("Found files:")
        for f in sorted(yaml_files):
            self.output_manager.log_debug(f"  {f.relative_to(directory)}")

        # Map files to models
        file_to_model = {}
        model_to_files = defaultdict(list)
        failed_files = []
        failure_reasons = {}

        for file_path in yaml_files:
            model_name, error = self.get_model_from_file(file_path)
            if model_name:
                file_to_model[str(file_path)] = model_name
                model_to_files[model_name].append(file_path)
                self.output_manager.log_debug(f"Mapped {file_path.name} -> {model_name}")
            else:
                failed_files.append(file_path)
                failure_reasons[file_path] = error or "Unknown error"
                self.output_manager.log_warning(f"Could not extract model from {file_path}: {error}")

        if failed_files:
            self.output_manager.output_warning(f"Failed to read {len(failed_files)} files:")
            for f in failed_files:
                rel_path = f.relative_to(directory)
                reason = failure_reasons.get(f, "Unknown error")
                self.output_manager.output_warning(f"  - {rel_path}: {reason}")
                
            # Group failures by reason
            reason_groups = defaultdict(list)
            for f, reason in failure_reasons.items():
                reason_groups[reason].append(f.relative_to(directory))
            
            self.output_manager.log_info("Failures grouped by reason:")
            for reason, files in reason_groups.items():
                self.output_manager.log_info(f"  {reason}: {len(files)} files")
                for f in files[:3]:  # Show first 3 examples
                    self.output_manager.log_debug(f"    - {f}")
                if len(files) > 3:
                    self.output_manager.log_debug(f"    ... and {len(files) - 3} more")

        if not file_to_model:
            self.output_manager.output_error("No valid model files found")
            return []

        # Get unique model names
        model_names = list(set(file_to_model.values()))
        self.output_manager.log_info(f"Found {len(model_names)} unique models across {len(file_to_model)} files")

        # Log models with multiple files
        for model, files in model_to_files.items():
            if len(files) > 1:
                self.output_manager.log_info(f"Model {model} has {len(files)} files")

        # Resolve order by model dependencies
        ordered_models = self.resolve_model_import_order(model_names)

        if not ordered_models:
            self.output_manager.output_error("Could not resolve import order")
            return []

        # Convert back to file paths
        ordered_files = []
        for model_name in ordered_models:
            if model_name in model_to_files:
                # Sort files within each model for consistent ordering
                model_files = sorted(model_to_files[model_name], key=lambda p: p.name)
                ordered_files.extend(model_files)
                self.output_manager.log_debug(f"Added {len(model_files)} files for model {model_name}")

        self.output_manager.log_info(f"Final import order: {len(ordered_files)} files")
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
                model_name, _ = self.get_model_from_file(file_path)
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
                    self.output_manager.log_info(f"Starting import of {file_path}")

                    # Use existing importer
                    from .importer import ComponentImporter
                    importer = ComponentImporter(self.output_manager, self.get_model)

                    result = importer.import_yaml_file(
                        file_path=file_path,
                        dry_run=False,
                        update_existing=update_existing
                    )

                    if result == 0:
                        successful += 1
                        self.output_manager.output_success(f"✓ Imported {rel_path}")
                        self.output_manager.log_info(f"Successfully imported {file_path}")
                    else:
                        failed += 1
                        self.output_manager.output_error(f"✗ Failed to import {rel_path}")
                        self.output_manager.log_error(f"Import failed for {file_path} with result code {result}")

                except Exception as e:
                    failed += 1
                    rel_path = file_path.relative_to(Path(directory_path)) if hasattr(file_path, 'relative_to') else file_path.name
                    self.output_manager.log_error(f"Exception importing {file_path}: {type(e).__name__}: {e}")
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
            self.output_manager.log_error(f"Directory import failed: {type(e).__name__}: {e}")
            self.output_manager.output_error(f"Directory import failed: {e}")
            self.output_manager.log_operation_end("Directory Import", False, str(e))
            return 1

    def analyze_directory_dependencies(self, directory_path):
        """Analyze and display dependency information for directory (recursive)"""
        self.output_manager.log_info(f"Analyzing dependencies for directory: {directory_path}")
        
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
        model_not_found = []
        read_failures = []

        for file_path in yaml_files:
            model_name, error = self.get_model_from_file(file_path)
            if model_name:
                model_class = self.get_model(model_name)
                if model_class:
                    depends_on = getattr(model_class, '__depends_on__', [])
                    self.output_manager.log_debug(f"Model {model_name} depends on: {depends_on}")
                else:
                    depends_on = []
                    model_not_found.append(model_name)
                    self.output_manager.log_warning(f"Model class not found for {model_name} from {file_path}")

                file_info.append({
                    'file': str(file_path),
                    'model': model_name,
                    'depends_on': depends_on,
                    'model_found': model_class is not None,
                    'read_error': None
                })
                all_dependencies.update(depends_on)
            else:
                read_failures.append({
                    'file': str(file_path),
                    'error': error or "Unknown error"
                })
                file_info.append({
                    'file': str(file_path),
                    'model': 'ERROR',
                    'depends_on': [],
                    'model_found': False,
                    'read_error': error
                })

        # Report read failures first
        if read_failures:
            self.output_manager.output_error(f"Failed to read {len(read_failures)} files:")
            for failure in read_failures:
                rel_path = Path(failure['file']).relative_to(directory)
                self.output_manager.output_error(f"  - {rel_path}: {failure['error']}")
            print()

        # Report models not found
        if model_not_found:
            self.output_manager.output_warning(f"Model classes not found in registry:")
            for model in sorted(set(model_not_found)):
                self.output_manager.output_warning(f"  - {model}")
            print()

        # Get unique model names for dependency analysis
        model_names = list(set(info['model'] for info in file_info if info['model'] != 'ERROR'))

        # Display dependencies
        headers = ['File', 'Path', 'Model', 'Depends On', 'Status']
        rows = []

        for info in file_info:
            deps_str = ', '.join(info['depends_on']) if info['depends_on'] else 'None'
            rel_path = str(Path(info['file']).parent.relative_to(directory)) if Path(info['file']).parent != directory else '.'
            
            if info['read_error']:
                status = f"✗ {info['read_error']}"
                model_display = 'ERROR'
                deps_str = '-'
            elif info['model_found']:
                status = '✓'
                model_display = info['model']
            else:
                status = '✗ Model not in registry'
                model_display = info['model']
                
            rows.append([Path(info['file']).name, rel_path, model_display, deps_str, status])

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