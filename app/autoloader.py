#!/usr/bin/env python3
"""
Auto-loader for classes with dependency resolution
Integrates with the existing class registry system
"""

import ast
import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque


class DependencyWalker(ast.NodeVisitor):
    """AST visitor to extract class dependencies"""

    def __init__(self):
        self.current_class = None
        self.dependencies = {}  # {class_name: [dependencies]}
        self.class_locations = {}  # {class_name: (file, line)}
        self.current_file = None

    def visit_ClassDef(self, node):
        """Visit class definitions"""
        old_class = self.current_class
        self.current_class = node.name
        
        # Record class location
        self.class_locations[node.name] = (self.current_file, node.lineno)
        
        # Look for __depends_on__ in the class body
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '__depends_on__':
                        # Extract dependency list
                        deps = self._extract_list(item.value)
                        if deps:
                            self.dependencies[node.name] = deps
        
        # Continue visiting nested nodes
        self.generic_visit(node)
        self.current_class = old_class

    def _extract_list(self, node):
        """Extract list of strings from AST node"""
        if isinstance(node, ast.List):
            deps = []
            for elem in node.elts:
                if isinstance(elem, ast.Constant) and isinstance(elem.value, str):
                    deps.append(elem.value)
            return deps
        return None


class ClassAutoLoader:
    """Auto-loader that discovers and loads classes in dependency order"""

    def __init__(self, base_directories: List[str] = None, patterns: List[str] = None, base_dir: str = None):
        # Import config to get BASE_DIR if not provided
        if base_dir is None:
            from ..config import config
            base_dir = config.get('BASE_DIR', os.path.dirname(os.path.dirname(__file__)))
        
        self.base_dir = Path(base_dir)
        
        # Default to single directory if not specified
        if base_directories is None:
            base_directories = ["_system"]
        if patterns is None:
            patterns = ["*_class.py"]

        # Ensure lists
        if isinstance(base_directories, str):
            base_directories = [base_directories]
        if isinstance(patterns, str):
            patterns = [patterns]

        # Convert to absolute paths relative to BASE_DIR
        self.base_directories = []
        for d in base_directories:
            full_path = self.base_dir / d
            self.base_directories.append(full_path)
        
        self.patterns = patterns
        self.all_dependencies = {}
        self.all_locations = {}
        self.loaded_classes = {}  # {class_name: class_object}
        

    def discover_classes(self):
        """Discover all classes and their dependencies"""
        self.all_dependencies.clear()
        self.all_locations.clear()

        for base_dir in self.base_directories:
            if not base_dir.exists():
                continue

            for pattern in self.patterns:
                matches = list(base_dir.rglob(pattern))
                
                for py_file in matches:
                    if '__pycache__' not in str(py_file):
                        self._analyze_file(py_file)


    def _analyze_file(self, filepath: Path):
        """Analyze a single Python file for classes and dependencies"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))
            
            # Create a new walker for each file
            walker = DependencyWalker()
            walker.current_file = str(filepath)
            walker.visit(tree)

            # Merge results
            self.all_dependencies.update(walker.dependencies)
            self.all_locations.update(walker.class_locations)

        except Exception as e:
            print(f"  ERROR analyzing {filepath}: {e}")
            import traceback
            traceback.print_exc()

    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort on dependencies to determine load order
        Returns list of class names in order they should be loaded
        """
        
        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        all_classes = set(self.all_locations.keys())
        
        
        # Initialize all classes with 0 in-degree
        for class_name in all_classes:
            in_degree[class_name] = 0

        # Build graph and count in-degrees
        for class_name, deps in self.all_dependencies.items():
            for dep in deps:
                if dep in all_classes:  # Only count dependencies we can resolve
                    graph[dep].append(class_name)
                    in_degree[class_name] += 1
                else:
                    print(f"  WARNING: {class_name} depends on {dep} which is not found")

        # Kahn's algorithm for topological sort
        queue = deque([node for node in all_classes if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree for neighbors
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(all_classes):
            # Find which classes are in cycles
            remaining = all_classes - set(result)
            raise RuntimeError(f"Circular dependencies detected involving classes: {remaining}")

        return result

    def _load_class(self, class_name: str) -> Optional[type]:
        """Load a single class from its file"""
        
        if class_name in self.loaded_classes:
            return self.loaded_classes[class_name]

        if class_name not in self.all_locations:
            raise ValueError(f"Class {class_name} not found in discovered classes")

        filepath, line_no = self.all_locations[class_name]

        try:
            # Convert file path to module path relative to BASE_DIR's parent
            # e.g., /path/to/app/_system/template_class.py -> app._system.template_class
            abs_filepath = Path(filepath).absolute()
            base_parent = self.base_dir.parent.absolute()
            
            # Try to make path relative to base_dir's parent
            try:
                rel_path = abs_filepath.relative_to(base_parent)
            except ValueError:
                # If that fails, try relative to current directory
                rel_path = abs_filepath.relative_to(Path.cwd())
            
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            module_name = '.'.join(module_parts)

            # Load module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load module from {filepath}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        # Extract class
            if hasattr(module, class_name):
                class_obj = getattr(module, class_name)
                self.loaded_classes[class_name] = class_obj
                
                # CRITICAL: Immediately inject into app.classes AND app.models
                import app.classes
                import app.models
                
                # Make it available RIGHT NOW for subsequent imports
                setattr(app.classes, class_name, class_obj)
                setattr(app.models, class_name, class_obj)
                
                # Also update the registry if we have access to it
                if hasattr(app.classes, '_class_registry'):
                    app.classes._class_registry[class_name] = class_obj
                
                return class_obj
            else:
                raise AttributeError(f"Class {class_name} not found in module {module_name}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Failed to load class {class_name} from {filepath}: {e}")

    # In app/autoloader.py, add these methods to ClassAutoLoader:

    def print_dependency_tree(self):
        """Print a visual representation of the dependency tree"""
        print("\n" + "="*80)
        print("DEPENDENCY TREE")
        print("="*80)
        
        # First, show raw dependencies
        print("\nRAW DEPENDENCIES:")
        for class_name, deps in sorted(self.all_dependencies.items()):
            print(f"  {class_name} -> {deps}")
        
        # Show classes with no dependencies
        all_classes = set(self.all_locations.keys())
        classes_with_deps = set(self.all_dependencies.keys())
        no_deps = all_classes - classes_with_deps
        if no_deps:
            print(f"\nNO DEPENDENCIES: {sorted(no_deps)}")
        
        # Show the computed load order
        print("\nCOMPUTED LOAD ORDER:")
        try:
            load_order = self._topological_sort()
            for i, class_name in enumerate(load_order, 1):
                deps = self.all_dependencies.get(class_name, [])
                print(f"  {i:3d}. {class_name}")
                if deps:
                    print(f"       depends on: {deps}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print("="*80 + "\n")

    def _topological_sort_with_debug(self) -> List[str]:
        """
        Topological sort with detailed debugging
        """
        
        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        all_classes = set(self.all_locations.keys())
        
        # Initialize all classes with 0 in-degree
        for class_name in all_classes:
            in_degree[class_name] = 0
        
        for class_name, deps in self.all_dependencies.items():
            for dep in deps:
                if dep in all_classes:
                    graph[dep].append(class_name)
                    in_degree[class_name] += 1
        
        
        # Kahn's algorithm
        queue = deque([node for node in all_classes if in_degree[node] == 0])
        
        result = []
        step = 1
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Reduce in-degree for classes that depend on this one
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            
            step += 1
        
        # Check for cycles
        if len(result) != len(all_classes):
            remaining = all_classes - set(result)
            print(f"\nERROR: Circular dependencies detected!")
            print(f"Unloadable classes: {remaining}")
            
            # Show why they're stuck
            for class_name in remaining:
                deps = self.all_dependencies.get(class_name, [])
                waiting_for = [d for d in deps if d in remaining]
                print(f"  {class_name} is waiting for: {waiting_for}")
        
        return result

    def load_all_classes(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load all discovered classes in dependency order into the provided registry
        """
        # Discover all classes
        self.discover_classes()
        
        # Print the dependency tree
        #self.print_dependency_tree()
        
        # Get load order with debug
        load_order = self._topological_sort_with_debug()
        
        # Load classes in order
        loaded_count = 0
        failed_loads = []
        
        for i, class_name in enumerate(load_order, 1):
            try:
                deps = self.all_dependencies.get(class_name, [])
                
                class_obj = self._load_class(class_name)
                if class_obj:
                    registry[class_name] = class_obj
                    
                    # Inject immediately
                    import app.classes
                    import app.models
                    setattr(app.classes, class_name, class_obj)
                    setattr(app.models, class_name, class_obj)
                    
                    loaded_count += 1
            except Exception as e:
                print(f"   ✗ FAILED: {e}")
                failed_loads.append((class_name, str(e)))
        
        if failed_loads:
            print("\nFAILED LOADS:")
            for name, error in failed_loads:
                print(f"  - {name}: {error}")
        print("="*80 + "\n")
        
        return registry

    def get_load_order(self) -> List[str]:
        """Get the load order without actually loading classes"""
        self.discover_classes()
        return self._topological_sort()

    def get_dependency_info(self) -> Dict[str, Any]:
        """Get detailed dependency information"""
        self.discover_classes()

        return {
            "dependencies": self.all_dependencies,
            "locations": self.all_locations,
            "load_order": self.get_load_order(),
            "total_classes": len(self.all_locations)
        }


# Convenience function for integration
def auto_load_classes(registry: Dict[str, Any],
                     base_directories: List[str] = None,
                     patterns: List[str] = None,
                     base_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to auto-load classes into a registry

    Args:
        registry: The registry dict to populate
        base_directories: List of directories to scan for classes
        patterns: List of file patterns to match
        base_dir: Base directory to resolve paths from (defaults to config['BASE_DIR'])

    Returns:
        The populated registry
    """
    loader = ClassAutoLoader(base_directories, patterns, base_dir)
    return loader.load_all_classes(registry)


# Example integration for app/register/classes.py:
# from app._system.class_auto_loader import auto_load_classes
# _class_registry = {}
# auto_load_classes(_class_registry)