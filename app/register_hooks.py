import os
import importlib
import inspect
from flask import Flask, g , session 
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

from .engines import Engines
from .config import config 
from .utils.route_collector import collect_blueprint_routes
from .utils.logger import register_logger




def register_hooks(path, app):
    """Recursively discover and register hooks from hook.py only, skip "templates" and "static" dirs.
    Classify a directory as a module if it contains any files besides __init__.py; modules may contain any files.
    For module dirs: if hook.py exists, import and register its register_* functions, then stop recursion.
    Categorization dirs (only __init__.py or empty) are recursed into without error."""

    base_dir = os.path.join(os.path.dirname(__file__), path)
    os.makedirs(base_dir, exist_ok=True)

    root_pkg = __package__
    pkg_root = path.replace(os.sep, '.')

    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
        # Skip unwanted dirs
        dirnames[:] = [d for d in dirnames]

        # Determine if this is a module: any files besides __init__.py
        module_files = [f for f in filenames if f != '__init__.py']
        if module_files:
            # This is a module directory
            rel = os.path.relpath(dirpath, base_dir)
            parts = [] if rel == '.' else rel.split(os.sep)
            hook_path = os.path.join(dirpath, 'hook.py')
            if 'hook.py' in filenames:
                import_path = '.'.join(filter(None, [root_pkg, pkg_root] + parts + ['hook']))
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
                    app.logger.warning(f"Could not import hook at {import_path}... {e}")

            # Stop recursion into module directories
            dirnames[:] = []
        # else: categorization dir -> continue recursion

