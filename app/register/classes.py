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
   
   print("DEBUG: Registering classes for CLI usage...")
   
   # Discover and import classes (populates _class_registry)
   discover_and_import(None, "_class.py") 
   
   # Make classes available for import in CLI
   import app.classes as classes_module
   for name, cls in _class_registry.items():
       if not name.islower():  # skip aliases
           setattr(classes_module, name, cls)
           if hasattr(classes_module, '__all__') and name not in classes_module.__all__:
               classes_module.__all__.append(name)
   
   print(f"DEBUG: CLI registration complete. Registry contains {len(_class_registry)} classes")
   return _class_registry


def register_classes(app: Flask):
   """Initialize and register all classes with dependency-aware ordering"""

   # Clear registry for fresh start
   global _class_registry
   print(f"Class registry size before clear: {len(_class_registry)}")
   _class_registry.clear()

   # Discover and import all classes with dependency resolution
   discover_and_import(app, "_class.py")

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

# app/register/classes.py - updated discover_and_import function
def discover_and_import(app=None, file_pattern=".py"):
    """Discover all class files and import them with dependency resolution"""
    from app.scanner import ModuleScanner
    from app.resolver import ClassDependencyResolver
    
    # Get logger for CLI mode
    logger = None
    if not app:
        import logging
        logger = logging.getLogger('cli_class')
    
    # Debug header
    if app:
        app.logger.debug("=" * 60)
        app.logger.debug(f"Starting class discovery (pattern: {file_pattern})")
        app.logger.debug("=" * 60)
    elif logger:
        logger.debug("=" * 60)
        logger.debug(f"Starting class discovery (pattern: {file_pattern})")
        logger.debug("=" * 60)
    else:
        print("=" * 60)
        print(f"DEBUG: Starting class discovery (pattern: {file_pattern})")
        print("=" * 60)
    
    # Create scanner for _class.py files
    scanner = ModuleScanner(
        base_paths=config['SYSTEM_SCAN_PATHS'],
        file_suffix=file_pattern,
        logger=app.logger if app else logger,
        ignore_dirs=['register'],
        ignore_files=['view.py']
    )
    
    # Debug: Show scan paths
    if app:
        app.logger.debug(f"Scan paths: {config['SYSTEM_SCAN_PATHS']}")
        app.logger.debug(f"Ignoring directories: ['register']")
    elif logger:
        logger.debug(f"Scan paths: {config['SYSTEM_SCAN_PATHS']}")
        logger.debug(f"Ignoring directories: ['register']")
    else:
        print(f"DEBUG: Scan paths: {config['SYSTEM_SCAN_PATHS']}")
        print(f"DEBUG: Ignoring directories: ['register']")
    
    # Scan for all class modules
    all_modules = scanner.scan()
    
    if not all_modules:
        if app:
            app.logger.warning("No class files found")
        elif logger:
            logger.warning("No class files found")
        else:
            print("WARNING: No class files found")
        return
    
    if app:
        app.logger.info(f"Discovered {len(all_modules)} class files")
        app.logger.debug("Discovered modules:")
        for mod in all_modules:
            app.logger.debug(f"  - {mod['display']} -> {mod['import_path']}")
    elif logger:
        logger.info(f"Discovered {len(all_modules)} class files")
        logger.debug("Discovered modules:")
        for mod in all_modules:
            logger.debug(f"  - {mod['display']} -> {mod['import_path']}")
    else:
        print(f"INFO: Discovered {len(all_modules)} class files")
        print("DEBUG: Discovered modules:")
        for mod in all_modules:
            print(f"  - {mod['display']} -> {mod['import_path']}")
    
    # Create resolver with appropriate logger
    resolver = ClassDependencyResolver(logger=app.logger if app else logger)
    
    # Enable debug mode for detailed output
    resolver.enable_debug()
    
    # Track registration stats
    registration_stats = {
        'attempted': 0,
        'successful': 0,
        'failed': []
    }
    
    # Define callback to register classes as they're processed
    def register_callback(class_name, class_obj, module, info):
        registration_stats['attempted'] += 1
        try:
            _class_registry[class_name] = class_obj
            registration_stats['successful'] += 1
            if app:
                app.logger.info(f"  ✓ Registered class: {class_name} from {info['display']}")
            elif logger:
                logger.info(f"  ✓ Registered class: {class_name} from {info['display']}")
            else:
                print(f"  ✓ Registered class: {class_name} from {info['display']}")
        except Exception as e:
            registration_stats['failed'].append((class_name, str(e)))
            if app:
                app.logger.error(f"  ✗ Failed to register {class_name}: {e}")
            elif logger:
                logger.error(f"  ✗ Failed to register {class_name}: {e}")
            else:
                print(f"  ✗ Failed to register {class_name}: {e}")
    
    try:
        # Resolve and register in dependency order
        if app:
            app.logger.debug("\nResolving class dependencies...")
        elif logger:
            logger.debug("\nResolving class dependencies...")
        else:
            print("\nDEBUG: Resolving class dependencies...")
            
        resolver.resolve_class_dependencies(all_modules, callback=register_callback)
        
        # Summary
        if app:
            app.logger.info("=" * 60)
            app.logger.info(f"Registration Summary:")
            app.logger.info(f"  Total modules scanned: {len(all_modules)}")
            app.logger.info(f"  Classes attempted: {registration_stats['attempted']}")
            app.logger.info(f"  Classes registered: {registration_stats['successful']}")
            app.logger.info(f"  Classes failed: {len(registration_stats['failed'])}")
            if registration_stats['failed']:
                app.logger.error("Failed registrations:")
                for class_name, error in registration_stats['failed']:
                    app.logger.error(f"  - {class_name}: {error}")
            app.logger.info(f"  Final registry size: {len(_class_registry)}")
            app.logger.info("=" * 60)
        elif logger:
            logger.info("=" * 60)
            logger.info(f"Registration Summary:")
            logger.info(f"  Total modules scanned: {len(all_modules)}")
            logger.info(f"  Classes attempted: {registration_stats['attempted']}")
            logger.info(f"  Classes registered: {registration_stats['successful']}")
            logger.info(f"  Classes failed: {len(registration_stats['failed'])}")
            if registration_stats['failed']:
                logger.error("Failed registrations:")
                for class_name, error in registration_stats['failed']:
                    logger.error(f"  - {class_name}: {error}")
            logger.info(f"  Final registry size: {len(_class_registry)}")
            logger.info("=" * 60)
        else:
            print("=" * 60)
            print(f"Registration Summary:")
            print(f"  Total modules scanned: {len(all_modules)}")
            print(f"  Classes attempted: {registration_stats['attempted']}")
            print(f"  Classes registered: {registration_stats['successful']}")
            print(f"  Classes failed: {len(registration_stats['failed'])}")
            if registration_stats['failed']:
                print("Failed registrations:")
                for class_name, error in registration_stats['failed']:
                    print(f"  - {class_name}: {error}")
            print(f"  Final registry size: {len(_class_registry)}")
            print("=" * 60)
            
    except Exception as e:
        if app:
            app.logger.error(f"Failed to resolve class dependencies: {e}")
        elif logger:
            logger.error(f"Failed to resolve class dependencies: {e}")
        else:
            print(f"ERROR: Failed to resolve class dependencies: {e}")
        raise