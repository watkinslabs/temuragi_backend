import os
import importlib
import inspect
from collections import defaultdict, deque
from flask import Flask, g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from app.config import config

# Global model registry
_model_registry = {}


class Engines:
    """Holds your engines.  One for config DB, and lazily-created ones for each target DSN."""
    def __init__(self, config_uri):
        # single engine to your Postgres “config server”
        self.config_engine = create_engine(config_uri, pool_size=5, max_overflow=10)
        # session factory for config DB
        self.ConfigSession = sessionmaker(bind=self.config_engine)
        # cache for per-page engines
        self._target_engines = {}

    def get_config_session(self):
        return self.ConfigSession()

    def get_target_engine(self, dsn, **opts):
        # reuse an engine per-DSN (keyed by the full DSN string)
        if dsn not in self._target_engines:
            self._target_engines[dsn] = create_engine(dsn, **opts)
        return self._target_engines[dsn]
    

def get_model(name):
    """Get a model class by name from the registry"""
    return _model_registry.get(name)


def list_models():
    """List all registered model names"""
    return list(_model_registry.keys())


def get_all_models():
    """Get dictionary of all registered models"""
    return _model_registry.copy()


def register_models_for_cli():
    """Register models for CLI usage without full Flask app"""
    # Create engine
    engine = create_engine(config['DATABASE_URI'])

    
    # Discover and import models (populates _model_registry)
    discover_and_import_models()
    
    # Return session for CLI use
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def register_db(app: Flask):
    """Initialize database and register all models with dependency-aware ordering"""
    # Clear registry for fresh start
    global _model_registry
    _model_registry.clear()
    
    # Create database engine and session
    config_engine = create_engine(app.config['DATABASE_URI'])
    app.db_session = scoped_session(sessionmaker(bind=config_engine))
    
    # Discover and import all models with dependency resolution
    discover_and_import_models(app)
    
    # Create all tables
    create_all_tables(app, config_engine)
    
    # Setup session cleanup
    @app.teardown_appcontext
    def cleanup_sessions(exc=None):
        app.db_session.remove()
    
    # Make session available in request context
    @app.before_request
    def setup_request_context():
        if not hasattr(g, 'session'):
            g.session = app.db_session
    
    # Make model registry available on app
    app.models = _model_registry
    app.get_model = get_model


def discover_and_import_models(app=None):
    """Discover all model files and import them with dependency resolution"""
    scan_paths = config['SYSTEM_SCAN_PATHS']
    root_pkg = __package__
    
    # Find all model files across all paths
    all_models = []
    for scan_path in scan_paths:
        models = find_models_in_path(scan_path, root_pkg, app)
        all_models.extend(models)
    
    if not all_models:
        if app:
            app.logger.warning("No model files found")
        return
    
    if app:
        app.logger.info(f"Discovered {len(all_models)} model files")
    
    # Import models with dependency resolution
    import_models_with_dependencies(all_models, app)
    
    # Log registry results
    if app:
        app.logger.info(f"Registered {len(_model_registry)} model classes in registry")


def find_models_in_path(scan_path, root_pkg, app=None):
    """Find all model files in a specific path"""
    # Get application root directory (where the main app module is)
    # Go up from register/database.py to get to app root
    register_dir = os.path.dirname(__file__)  # app/register/
    app_root = os.path.dirname(register_dir)  # app/
    
    # Make scan_path relative to app root
    base_dir = os.path.join(app_root, scan_path)

    if not os.path.exists(base_dir):
        if app:
            app.logger.debug(f"Path not found: {scan_path} (resolved to: {base_dir})")
        return []

    models = []
    pkg_path = scan_path.replace(os.sep, '.')

    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith('_model.py'):  # Changed to *_model.py pattern
                # Build import path
                rel_path = os.path.relpath(root, base_dir)
                path_parts = [] if rel_path == '.' else rel_path.split(os.sep)
                module_name = filename[:-3]  # Remove .py

                # Build import path starting from app root
                import_path = '.'.join(['app', pkg_path] + path_parts + [module_name])
                display_path = '/'.join([scan_path] + path_parts + [filename])

                models.append({
                    'filename': filename,
                    'import_path': import_path,
                    'display': display_path,
                    'module_name': module_name
                })

    return models

def get_model_dependencies(module):
    """Extract dependencies from model classes in a module"""
    dependencies = set()
    
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if hasattr(obj, '__tablename__') and hasattr(obj, '__module__'):
            if obj.__module__ == module.__name__:
                # Check for __depends_on__ attribute
                if hasattr(obj, '__depends_on__'):
                    deps = obj.__depends_on__
                    if isinstance(deps, str):
                        dependencies.add(deps)
                    elif isinstance(deps, (list, tuple)):
                        dependencies.update(deps)
    
    return dependencies


def build_dependency_graph(models, app=None):
    """Build dependency graph for models"""
    # First pass: import all modules and build class-to-module mapping
    module_map = {}
    class_to_module = {}  # Map class names to module names
    dependency_graph = defaultdict(set)
    reverse_graph = defaultdict(set)
    
    if app:
        app.logger.info("Building dependency graph...")
    
    # First pass: build module map and class-to-module mapping
    for model_info in models:
        try:
            module = importlib.import_module(model_info['import_path'])
            module_name = model_info['module_name']
            module_map[module_name] = {
                'module': module,
                'info': model_info
            }
            
            # Find model classes in this module and map them to module name
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (hasattr(obj, '__tablename__') and 
                    hasattr(obj, '__module__') and 
                    obj.__module__ == module.__name__):
                    class_to_module[name] = module_name
            
        except ImportError as e:
            if app:
                app.logger.warning(f"Failed to inspect {model_info['display']}: {e}")
    
    # Second pass: build dependency graph using module names
    for module_name, module_data in module_map.items():
        module = module_data['module']
        
        # Get class dependencies (which are class names)
        class_dependencies = get_model_dependencies(module)
        
        # Convert class dependencies to module dependencies
        module_dependencies = set()
        for class_dep in class_dependencies:
            if class_dep in class_to_module:
                module_dependencies.add(class_to_module[class_dep])
        
        dependency_graph[module_name] = module_dependencies
        
        for dep_module in module_dependencies:
            reverse_graph[dep_module].add(module_name)
        
        if app:
            app.logger.debug(f"  {module_name}: depends on {module_dependencies or 'none'}")
    
    return dependency_graph, reverse_graph, module_map


def topological_sort(dependency_graph):
    """Perform topological sort on dependency graph"""
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
        raise Exception(f"Circular dependency detected in models: {remaining}")
    
    return result


def import_models_with_dependencies(models, app=None):
    """Import models respecting dependency declarations"""
    global _model_registry
    
    try:
        # Build dependency graph
        dependency_graph, reverse_graph, module_map = build_dependency_graph(models, app)
        
        if not dependency_graph:
            if app:
                app.logger.info("No dependencies found, importing all models")
            else:
                print("No dependencies found, importing all models")
            # Fall back to simple import
            for model_info in models:
                import_single_model(model_info, app)
            return
        
        # Sort models by dependencies
        sorted_model_names = topological_sort(dependency_graph)
        
        if app:
            app.logger.info(f"Importing {len(sorted_model_names)} models in dependency order:")
        
        # Import in dependency order
        imported = set()
        for module_name in sorted_model_names:
            if module_name in module_map:
                model_data = module_map[module_name]
                module = model_data['module']
                model_info = model_data['info']
                
                # Register model classes from this module
                register_model_classes_from_module(module, app)
                imported.add(module_name)
                
                if app:
                    app.logger.info(f"  ✓ {model_info['display']}")
        
        # Import any remaining models that weren't in the dependency graph
        for model_info in models:
            module_name = model_info['module_name']
            if module_name not in [m['info']['module_name'] for m in module_map.values()]:
                import_single_model(model_info, app)
        
        if app:
            app.logger.info(f"Successfully imported {len(imported)} models with dependencies")
        
    except Exception as e:
        if app:
            app.logger.error(f"Dependency resolution failed: {e}")
            app.logger.info("Falling back to simple import order")
        else:
            print(f"Error: Dependency resolution failed: {e}")
            print("Falling back to simple import order")
        
        # Fall back to simple import
        for model_info in models:
            import_single_model(model_info, app)


def import_single_model(model_info, app=None):
    """Import a single model file"""
    try:
        module = importlib.import_module(model_info['import_path'])
        register_model_classes_from_module(module, app)
        if app:
            app.logger.debug(f"  ✓ {model_info['display']}")
    except ImportError as e:
        if app:
            app.logger.warning(f"  ✗ Failed to import {model_info['display']}: {e}")
        else:
            print(f"Warning: Failed to import {model_info['display']}: {e}")


def register_model_classes_from_module(module, app=None):
    """Register all SQLAlchemy model classes from a module into the global registry"""
    global _model_registry
    
    # Find all model classes in the module
    tables_found = []
    
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if (hasattr(obj, '__tablename__') and 
            hasattr(obj, '__module__') and 
            obj.__module__ == module.__name__):
            
            # Register by class name
            _model_registry[name] = obj
            tables_found.append(obj.__tablename__)
            
            # Also register by table name for convenience
            if hasattr(obj, '__tablename__'):
                _model_registry[obj.__tablename__] = obj
    
    if tables_found and app:
        app.logger.debug(f"    Registered: {', '.join(tables_found)}")

def preview_model_registry():
    """Preview what's in the model registry - for CLI/debugging"""
    print("📋 Model Registry Contents:")
    print("=" * 60)
    
    if not _model_registry:
        print("  Registry is empty (models not loaded yet)")
        return
    
    # Group by actual model classes vs table aliases
    model_classes = {}
    table_aliases = {}
    
    for name, model_class in _model_registry.items():
        if hasattr(model_class, '__tablename__'):
            if name == model_class.__name__:
                # This is the actual class name
                model_classes[name] = model_class
            elif name == model_class.__tablename__:
                # This is a table name alias
                table_aliases[name] = model_class
    
    print("  Model Classes:")
    for name, model_class in sorted(model_classes.items()):
        table = model_class.__tablename__
        module = model_class.__module__.split('.')[-1]
        deps = getattr(model_class, '__depends_on__', None)
        deps_str = f" (depends: {deps})" if deps else ""
        print(f"    {name:25} -> {table:20} ({module}){deps_str}")
    
    print(f"\n  Table Name Aliases: {len(table_aliases)} available")
    print(f"  Total Registry Size: {len(_model_registry)} entries")
    
    return _model_registry

def create_all_tables(app, engine):
    """Create database tables from all loaded models using existing dependency resolution"""
    try:
        # Find BaseModel
        base_paths = [
            'app.base.model',
            'app._system.base',
            'app.base'
        ]

        BaseModel = None
        for path in base_paths:
            try:
                module = importlib.import_module(path)
                BaseModel = getattr(module, 'BaseModel', None)
                if BaseModel:
                    break
            except ImportError:
                continue

        if not BaseModel:
            raise ImportError("BaseModel not found")

        app.logger.info("Creating database tables using existing dependency resolution...")

        # Check if we have models in registry
        if not _model_registry:
            app.logger.warning("No models in registry, using simple create_all")
            BaseModel.metadata.create_all(engine, checkfirst=True)
            return

        # The models are already imported in the correct dependency order
        # SQLAlchemy's create_all() handles FK dependencies, but we can still 
        # respect the model dependency order if needed
        
        # Get model classes in the order they were registered (which follows dependencies)
        model_classes = []
        seen_tables = set()
        
        for name, model_class in _model_registry.items():
            if (hasattr(model_class, '__tablename__') and
                hasattr(model_class, '__name__') and
                name == model_class.__name__ and  # Only actual class names
                model_class.__tablename__ not in seen_tables):
                model_classes.append(model_class)
                seen_tables.add(model_class.__tablename__)

        app.logger.info(f"Found {len(model_classes)} model classes")

        # Create all tables - SQLAlchemy handles the actual dependency order
        BaseModel.metadata.create_all(engine, checkfirst=True)

        app.logger.info("Database tables created successfully")

        # Log table info
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            app.logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")

    except Exception as e:
        app.logger.error(f"Failed to create tables: {e}")
        raise