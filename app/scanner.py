# app/_system/utils/module_scanner.py
import os
import importlib

class ModuleScanner:
   """Scans directories for Python modules matching specific patterns"""
   
   def __init__(self, base_paths=None, file_suffix="_class.py", ignore_dirs=None, ignore_files=None, logger=None):
       """
       Initialize scanner
       
       Args:
           base_paths: List of paths to scan (relative to app root)
           file_suffix: File pattern to match (e.g. "_class.py", "_model.py")
           ignore_dirs: List of directory names to skip (e.g. ["__pycache__", ".git", "tests"])
           ignore_files: List of filenames to skip (e.g. ["__init__.py", "test_*.py"])
           logger: Optional logger instance
       """
       self.base_paths = base_paths or []
       self.file_suffix = file_suffix
       self.ignore_dirs = set(ignore_dirs or ["__pycache__", ".git", ".pytest_cache"])
       self.ignore_files = set(ignore_files or [])
       self.logger = logger
       self._app_root = self._find_app_root()
       
   def _find_app_root(self):
       """Find the app root directory"""
       # Start from this file's location
       current = os.path.dirname(__file__)  # app/_system/utils/     
       # Go up to find 'app' directory
       while os.path.basename(current) != 'app' and current != '/':
           current = os.path.dirname(current)
       return current
       
   def _log(self, level, message):
       """Log message if logger available"""
       if self.logger:
           getattr(self.logger, level)(message)
           
   def scan(self, paths=None):
       """
       Scan for modules matching the pattern
       
       Args:
           paths: Override default paths for this scan
           
       Returns:
           List of dicts with module info
       """
       scan_paths = paths or self.base_paths
       all_modules = []
       
       for scan_path in scan_paths:
           modules = self._scan_path(scan_path)
           all_modules.extend(modules)
           
       self._log("info", f"Found {len(all_modules)} modules matching pattern '{self.file_suffix}'")
       return all_modules
       
   def _should_ignore_file(self, filename):
       """Check if file should be ignored based on ignore patterns"""
       # Check exact matches
       if filename in self.ignore_files:
           return True
           
       # Check wildcard patterns
       import fnmatch
       for pattern in self.ignore_files:
           if '*' in pattern or '?' in pattern:
               if fnmatch.fnmatch(filename, pattern):
                   return True
                   
       return False
       
   def _scan_path(self, scan_path):
       """Scan a single path for matching modules"""
       base_dir = os.path.join(self._app_root, scan_path)
       
       if not os.path.exists(base_dir):
           self._log("debug", f"Path not found: {scan_path}")
           return []
           
       modules = []
       pkg_path = scan_path.replace(os.sep, '.')
       
       for root, dirs, files in os.walk(base_dir):
           # Filter out ignored directories
           dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
           
           for filename in files:
               # Skip ignored files
               if self._should_ignore_file(filename):
                   continue
                   
               if filename.endswith(self.file_suffix):
                   # Build import path
                   rel_path = os.path.relpath(root, base_dir)
                   path_parts = [] if rel_path == '.' else rel_path.split(os.sep)
                   module_name = filename[:-3]  # Remove .py
                   
                   # Build import path starting from app root
                   import_path = '.'.join(['app', pkg_path] + path_parts + [module_name])
                   display_path = '/'.join([scan_path] + path_parts + [filename])
                   
                   modules.append({
                       'filename': filename,
                       'import_path': import_path,
                       'display': display_path,
                       'module_name': module_name
                   })
                   
       self._log("debug", f"Scanned {scan_path}: found {len(modules)} modules")
       return modules