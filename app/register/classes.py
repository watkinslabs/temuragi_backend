# app/register/classes.py
import os
import importlib
import inspect
from collections import defaultdict, deque
from flask import Flask, g

from app.config import config

# Global class registry
_class_registry = {}


def get_class(name):
    """Get a class by name from the registry"""
    return _class_registry.get(name)


def list_classes():
    """List all registered class names"""
    return list(_class_registry.keys())


def get_all_classes():
    """Get dictionary of all registered classes"""
    return _class_registry.copy()


def register_classes_for_cli():
    """Register classes for CLI usage without full Flask app"""
    # Clear registry for fresh start in CLI
    global _class_registry
    _class_registry.clear()
    
    # Discover and import classes (populates _class_registry)
    discover_and_import_classes(app=None)  # No app context in CLI
    
    # Make classes available for import in CLI
    import app.classes as classes_module
    for name, cls in _class_registry.items():
        if not name.islower():  # skip aliases
            setattr(classes_module, name, cls)
            if hasattr(classes_module, '__all__') and name not in classes_module.__all__:
                classes_module.__all__.append(name)
    
    return _class_registry


def register_classes(app: Flask):
    """Initialize and register all classes with dependency-aware ordering"""

    # Clear registry for fresh start
    global _class_registry
    print(f"Class registry size before clear: {len(_class_registry)}")
    _class_registry.clear()

    # Discover and import all classes with dependency resolution
    discover_and_import_classes(app)

    # Make class registry available on app
    app.classes = _class_registry
    app.get_class = get_class

    # Make classes available in app.classes module if it exists
    try:
        import app.classes as classes_module
        for name, cls in _class_registry.items():
            if not name.islower():
                setattr(classes_module, name, cls)
                if hasattr(classes_module, '__all__') and name not in classes_module.__all__:
                    classes_module.__all__.append(name)
    except ImportError:
        # app.classes module doesn't exist, that's fine
        pass


def discover_and_import_classes(app=None):
    """Discover all class files and import them with dependency resolution"""
    scan_paths = config['SYSTEM_SCAN_PATHS']

    # Find all class files across all paths
    all_classes = []
    for scan_path in scan_paths:
        classes = find_classes_in_path(scan_path, app)
        all_classes.extend(classes)

    if not all_classes:
        if app:
            app.logger.warning("No class files found")
        return

    if app:
        app.logger.info(f"Discovered {len(all_classes)} class files")

    # Import classes with dependency resolution
    import_classes_with_dependencies(all_classes, app)

    # Log registry results
    if app:
        app.logger.info(f"Registered {len(_class_registry)} classes in registry")


def find_classes_in_path(scan_path, app=None):
    """Find all class files in a specific path"""
    # Get application root directory
    register_dir = os.path.dirname(__file__)  # app/register/
    app_root = os.path.dirname(register_dir)  # app/

    # Make scan_path relative to app root
    base_dir = os.path.join(app_root, scan_path)

    if not os.path.exists(base_dir):
        if app:
            app.logger.debug(f"Path not found: {scan_path} (resolved to: {base_dir})")
        return []

    classes = []
    pkg_path = scan_path.replace(os.sep, '.')

    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith('_class.py'):  # Look for *_class.py pattern
                # Build import path
                rel_path = os.path.relpath(root, base_dir)
                path_parts = [] if rel_path == '.' else rel_path.split(os.sep)
                module_name = filename[:-3]  # Remove .py

                # Build import path starting from app root
                import_path = '.'.join(['app', pkg_path] + path_parts + [module_name])
                display_path = '/'.join([scan_path] + path_parts + [filename])

                classes.append({
                    'filename': filename,
                    'import_path': import_path,
                    'display': display_path,
                    'module_name': module_name
                })

    return classes


def get_class_dependencies(module):
    """Extract dependencies from classes in a module"""
    dependencies = set()

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if hasattr(obj, '__module__') and obj.__module__ == module.__name__:
            # Check for __depends_on__ attribute
            if hasattr(obj, '__depends_on__'):
                deps = obj.__depends_on__
                if isinstance(deps, str):
                    dependencies.add(deps)
                elif isinstance(deps, (list, tuple)):
                    dependencies.update(deps)

    return dependencies


def build_class_dependency_graph(classes, app=None):
    """Build dependency graph for classes"""
    module_map = {}
    class_to_module = {}  # Map class names to module names
    dependency_graph = defaultdict(set)

    if app:
        app.logger.info("Building class dependency graph...")

    # First pass: build module map and class-to-module mapping
    for class_info in classes:
        try:
            module = importlib.import_module(class_info['import_path'])
            module_name = class_info['module_name']
            module_map[module_name] = {
                'module': module,
                'info': class_info
            }

            # Find classes in this module and map them to module name
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (hasattr(obj, '__module__') and
                    obj.__module__ == module.__name__):
                    class_to_module[name] = module_name

        except ImportError as e:
            if app:
                app.logger.warning(f"Failed to inspect {class_info['display']}: {e}")

    # Second pass: build dependency graph using module names
    for module_name, module_data in module_map.items():
        module = module_data['module']

        # Get class dependencies (which are class names)
        class_dependencies = get_class_dependencies(module)

        # Convert class dependencies to module dependencies
        module_dependencies = set()
        for class_dep in class_dependencies:
            if class_dep in class_to_module:
                module_dependencies.add(class_to_module[class_dep])

        dependency_graph[module_name] = module_dependencies

    return dependency_graph, module_map


def topological_sort_classes(dependency_graph):
    """Perform topological sort on class dependency graph"""
    # Kahn's algorithm
    in_degree = defaultdict(int)
    all_nodes = set()

    # Calculate in-degrees
    for node, deps in dependency_graph.items():
        all_nodes.add(node)
        for dep in deps:
            all_nodes.add(dep)
            in_degree[node] += 1

    # Start with nodes that have no dependencies
    queue = deque([node for node in all_nodes if in_degree[node] == 0])
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)

        # Update in-degrees for dependent nodes
        for dependent in all_nodes:
            if node in dependency_graph.get(dependent, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    # Check for circular dependencies
    if len(result) != len(all_nodes):
        remaining = all_nodes - set(result)
        raise Exception(f"Circular dependency detected in classes: {remaining}")

    return result


def import_classes_with_dependencies(classes, app=None):
    """Import classes respecting dependency declarations"""
    global _class_registry

    processed_modules = set()  # Track what we've already processed

    try:
        # Build dependency graph
        dependency_graph, module_map = build_class_dependency_graph(classes, app)

        if not dependency_graph:
            if app:
                app.logger.info("No dependencies found, importing all classes")
            else:
                print("No dependencies found, importing all classes")
            # Fall back to simple import
            for class_info in classes:
                if class_info['import_path'] not in processed_modules:
                    import_single_class_module(class_info, app)
                    processed_modules.add(class_info['import_path'])
            return

        # Sort classes by dependencies
        sorted_module_names = topological_sort_classes(dependency_graph)

        if app:
            app.logger.info(f"Importing {len(sorted_module_names)} class modules in dependency order:")

        # Import in dependency order
        imported = set()
        for module_name in sorted_module_names:
            if module_name in module_map:
                module_data = module_map[module_name]
                module = module_data['module']
                class_info = module_data['info']

                # Only process if we haven't already
                if class_info['import_path'] not in processed_modules:
                    # Register classes from this module
                    register_classes_from_module(module, app)
                    imported.add(module_name)
                    processed_modules.add(class_info['import_path'])

                    if app:
                        app.logger.info(f"  ✓ {class_info['display']}")

        # Import any remaining classes that weren't in the dependency graph
        for class_info in classes:
            module_name = class_info['module_name']
            if (module_name not in [m['info']['module_name'] for m in module_map.values()] and
                class_info['import_path'] not in processed_modules):
                import_single_class_module(class_info, app)
                processed_modules.add(class_info['import_path'])

        if app:
            app.logger.info(f"Successfully imported {len(imported)} class modules with dependencies")

    except Exception as e:
        if app:
            app.logger.error(f"Class dependency resolution failed: {e}")
            app.logger.info("Falling back to simple import order")
        else:
            print(f"Error: Class dependency resolution failed: {e}")
            print("Falling back to simple import order")

        # Fall back to simple import
        for class_info in classes:
            if class_info['import_path'] not in processed_modules:
                import_single_class_module(class_info, app)
                processed_modules.add(class_info['import_path'])


def import_single_class_module(class_info, app=None):
    """Import a single class file"""
    try:
        module = importlib.import_module(class_info['import_path'])
        register_classes_from_module(module, app)
        if app:
            app.logger.debug(f"  ✓ {class_info['display']}")
    except ImportError as e:
        if app:
            app.logger.warning(f"  ✗ Failed to import {class_info['display']}: {e}")
        else:
            print(f"Warning: Failed to import {class_info['display']}: {e}")


def register_classes_from_module(module, app=None):
    """Register all classes from a module into the global registry"""
    global _class_registry

    # Find all classes in the module
    classes_found = []

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if (hasattr(obj, '__module__') and
            obj.__module__ == module.__name__):

            # Register by class name
            _class_registry[name] = obj
            classes_found.append(name)

    if classes_found and app:
        app.logger.debug(f"    Registered classes: {', '.join(classes_found)}")


def preview_class_registry():
    """Preview what's in the class registry - for CLI/debugging"""
    print("📋 Class Registry Contents:")
    print("=" * 60)

    if not _class_registry:
        print("  Registry is empty (classes not loaded yet)")
        return

    # Group by module
    by_module = defaultdict(list)
    for name, cls in _class_registry.items():
        module_name = cls.__module__.split('.')[-1]
        by_module[module_name].append((name, cls))

    for module_name, class_list in sorted(by_module.items()):
        print(f"  {module_name}:")
        for name, cls in sorted(class_list):
            deps = getattr(cls, '__depends_on__', None)
            deps_str = f" (depends: {deps})" if deps else ""
            print(f"    {name:25} -> {cls.__name__}{deps_str}")

    print(f"\n  Total Registry Size: {len(_class_registry)} classes")

    return _class_registry