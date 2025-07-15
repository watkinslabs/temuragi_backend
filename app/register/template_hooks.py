import os
import importlib
import inspect
import sys
from app.config import config


def register_hooks(path, app):
    """Recursively discover and register hooks from hook.py and *_hook.py files, skip 'templates' and 'static' dirs.
    Stop recursion once files are found in a directory."""

    base_dir = os.path.join(config.base_dir, path)
    base_pkg = 'app.' + path.replace(os.sep, '.').strip('.')

    # Add BASE_DIR to sys.path once, so imports work cleanly
    if config.base_dir not in sys.path:
        sys.path.insert(0, config.base_dir)

    # Collect all hook modules first
    hook_modules = []
    
    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
        # Skip unwanted dirs
        dirnames[:] = [d for d in dirnames if d not in ('templates', 'static')]

        # If directory has any files, process hooks and stop recursion
        if filenames:
            rel_path = os.path.relpath(dirpath, base_dir)
            module_parts = [] if rel_path == '.' else rel_path.split(os.sep)

            # Find all hook files (hook.py and *_hook.py)
            hook_files = [f for f in filenames if f == 'hook.py' or f.endswith('_hook.py')]
            
            for hook_file in hook_files:
                # Remove .py extension to get module name
                hook_module_name = hook_file[:-3]
                import_path = '.'.join([base_pkg] + module_parts + [hook_module_name])
                hook_modules.append(import_path)
                app.logger.info(f"----------Found hook module: {import_path}")

            # Stop recursion into dirs with files
            dirnames[:] = []
    
    app.logger.info(f"Total hook modules found: {len(hook_modules)}")
    
    # Now load hooks with dependency resolution
    loaded_hooks = set()
    pending_hooks = hook_modules.copy()
    max_iterations = len(pending_hooks) * 2  # Prevent infinite loops
    iteration = 0
    
    while pending_hooks and iteration < max_iterations:
        iteration += 1
        progress_made = False
        app.logger.info(f"Dependency resolution iteration {iteration}, pending hooks: {len(pending_hooks)}")
        
        for import_path in pending_hooks[:]:  # Copy list to allow modification during iteration
            try:
                hook_module = importlib.import_module(import_path)
                
                # Check dependencies
                depends_on = getattr(hook_module, '__depends_on__', [])
                dependencies_met = True
                
                for dep in depends_on:
                    if dep not in app.extensions:
                        dependencies_met = False
                        app.logger.debug(f"Hook {import_path} waiting for extension: {dep}")
                        break
                
                if not dependencies_met:
                    continue  # Skip this hook for now
                
                # Dependencies met, register all hooks in this module
                app.logger.info(f"Loading hook module: {import_path} (dependencies: {depends_on})")
                hook_registered = False
                for name, func in inspect.getmembers(hook_module, inspect.isfunction):
                    if name.startswith('register_'):
                        try:
                            func(app)
                            app.logger.info(f"Registered hook {name} from {import_path}")
                            hook_registered = True
                        except Exception as exc:
                            app.logger.error(f"Error in {name} from {import_path}: {exc}")
                
                if hook_registered:
                    loaded_hooks.add(import_path)
                    pending_hooks.remove(import_path)
                    progress_made = True
                    
            except ImportError as e:
                app.logger.warning(f"Failed to import {import_path}: {e}")
                pending_hooks.remove(import_path)
                progress_made = True
        
        # If no progress was made, we have unmet dependencies
        if not progress_made and pending_hooks:
            app.logger.warning("No progress made in dependency resolution")
            for import_path in pending_hooks:
                try:
                    hook_module = importlib.import_module(import_path)
                    depends_on = getattr(hook_module, '__depends_on__', [])
                    missing_deps = [dep for dep in depends_on if dep not in app.extensions]
                    if missing_deps:
                        app.logger.warning(f"Hook {import_path} has unmet dependencies: {missing_deps}")
                except:
                    pass
            break
    
    # Final summary
    app.logger.info(f"Hook registration complete. Loaded: {len(loaded_hooks)}, Failed: {len(pending_hooks)}")
    if pending_hooks:
        app.logger.warning(f"Failed to load hooks: {pending_hooks}")