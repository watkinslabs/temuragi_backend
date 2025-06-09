import os
import importlib

def register_blueprints(prefix ,path, app):
    """Recursively discover and register blueprints from view.py only, skip "templates" and "static" dirs,
    abort if unexpected files present in categorization dirs. Once a module is found (view.py present), do not recurse further.

    Module dirs are identified by view.py (they may contain any files).
    Categorization dirs (used only for grouping) must contain only subdirectories and __init__.py."""
    base_dir = os.path.join(os.path.dirname(__file__), path)
    os.makedirs(base_dir, exist_ok=True)

    # Determine root package from this module's package context
    root_pkg = __package__  

    # Convert path to package notation, e.g. 'modules/sub' -> 'modules.sub'
    pkg_root = path.replace(os.sep, '.')

    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
        dirnames[:] = [d for d in dirnames ]

        if 'view.py' in filenames:
            # Compute subpackage path relative to base_dir
            rel = os.path.relpath(dirpath, base_dir)
            parts = [] if rel == '.' else rel.split(os.sep)
            # Build full import path without relying on __main__
            import_path = '.'.join(filter(None, [root_pkg, pkg_root] + parts + ['view']))
            try:
                view_module = importlib.import_module(import_path)
                bp = getattr(view_module, 'bp', None)
                if bp:
                    
                    full_prefix = bp.url_prefix if getattr(view_module, 'no_prefix', False) else f"{prefix}{bp.url_prefix}"
                    app.register_blueprint(bp, url_prefix=full_prefix)
                    app.logger.info(f"Registered blueprint: {bp.name} with URL prefix: {full_prefix}")
            except ImportError as e:
                app.logger.warning(f"Could not import view at {import_path}... {e}")

            dirnames[:] = []
            continue

        if '__init__.py' in filenames:
            extras = [f for f in filenames if f != '__init__.py']
            if extras:
                raise RuntimeError(f"Unexpected files {extras} in grouping directory {dirpath}")
            continue

        # continue recursion for non-package, non-module dirs
        
