import os
import importlib
import inspect
import sys
from app.config import config


def register_hooks(path, app):
    """Recursively discover and register hooks from hook.py only, skip 'templates' and 'static' dirs.
    Treat a dir as a module if it has files other than __init__.py.
    Stop recursion once a module is found. Categorization dirs are recursed."""

    base_dir = os.path.join(config['BASE_DIR'], path)
    base_pkg = 'app.' + path.replace(os.sep, '.').strip('.')

    # Add BASE_DIR to sys.path once, so imports work cleanly
    if config['BASE_DIR'] not in sys.path:
        sys.path.insert(0, config['BASE_DIR'])

    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
        # Skip unwanted dirs
        dirnames[:] = [d for d in dirnames if d not in ('templates', 'static')]

        # Determine if it's a module dir
        module_files = [f for f in filenames if f != '__init__.py']
        if module_files:
            rel_path = os.path.relpath(dirpath, base_dir)
            module_parts = [] if rel_path == '.' else rel_path.split(os.sep)

            if 'hook.py' in filenames:
                import_path = '.'.join([base_pkg] + module_parts + ['hook'])
                try:
                    hook_module = importlib.import_module(import_path)
                    for name, func in inspect.getmembers(hook_module, inspect.isfunction):
                        if name.startswith('register_'):
                            try:
                                func(app)
                                app.logger.info(f"Registered hook {name} from {import_path}")
                            except Exception as exc:
                                app.logger.error(f"Error in {name} from {import_path}: {exc}")
                except ImportError as e:
                    app.logger.warning(f"Failed to import {import_path}: {e}")

            # Stop recursion into module dirs
            dirnames[:] = []