import os
import importlib
import sys
from app.config import config


def register_blueprints(prefix, path, app):
   """Recursively discover and register blueprints from view.py only, skip 'templates' and 'static' dirs.
   Treat a dir as a module if it has files other than __init__.py.
   Stop recursion once a module is found. Categorization dirs are recursed."""

   base_dir = os.path.join(config['base_dir'], path)
   base_pkg = 'app.' + path.replace(os.sep, '.').strip('.')

   # Add BASE_DIR to sys.path once, so imports work cleanly
   if config['base_dir'] not in sys.path:
       sys.path.insert(0, config['base_dir'])

   for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
       # Skip unwanted dirs
       dirnames[:] = [d for d in dirnames if d not in ('templates', 'static')]

       # Determine if it's a module dir
       module_files = [f for f in filenames if f != '__init__.py']
       if module_files:
           rel_path = os.path.relpath(dirpath, base_dir)
           module_parts = [] if rel_path == '.' else rel_path.split(os.sep)

           # Find all files ending with view.py
           view_files = [f for f in filenames if f.endswith('view.py')]
           
           for view_file in view_files:
               # Remove .py extension to get module name
               module_name = view_file[:-3]
               import_path = '.'.join([base_pkg] + module_parts + [module_name])
               try:
                   view_module = importlib.import_module(import_path)
                   bp = getattr(view_module, 'bp', None)
                   if bp:
                       full_prefix = bp.url_prefix if getattr(view_module, 'no_prefix', False) else f"{prefix}{bp.url_prefix}"
                       app.register_blueprint(bp, url_prefix=full_prefix)
                       app.logger.info(f"Registered blueprint: {bp.name} with URL prefix: {full_prefix}")
               except ImportError as e:
                   app.logger.warning(f"Failed to import {import_path}: {e}")

           # Stop recursion into module dirs
           dirnames[:] = []