# app/_system/utils/dependency_resolver.py
import importlib
import inspect
from collections import defaultdict, deque


class DependencyResolver:
    """
    Resolves dependencies between modules or classes using topological sorting.
    Can be used for models, classes, or any other objects with __depends_on__ attributes.
    """
    
    def __init__(self, logger=None):
        """Initialize resolver with optional logger"""
        self.logger = logger
        self._debug_mode = False
        
    def enable_debug(self):
        """Enable detailed debug output"""
        self._debug_mode = True
        
    def _log(self, level, message):
        """Log message if logger available, otherwise print"""
        if self.logger:
            getattr(self.logger, level)(message)
        elif level in ('error', 'warning') or self._debug_mode:
            print(f"{level.upper()}: {message}")
            
    def build_dependency_graph(self, items, item_type="item"):
        """
        Build dependency graph from list of items.
        Each item should be a dict with at least 'import_path' key.
        Returns: (dependency_graph, reverse_graph, item_map)
        """
        item_map = {}
        class_to_item = {}  # Map class names to item names
        dependency_graph = defaultdict(set)
        reverse_graph = defaultdict(set)
        
        self._log("info", f"Building dependency graph for {len(items)} {item_type}s...")
        
        # First pass: build item map and class-to-item mapping
        for item_info in items:
            try:
                module = importlib.import_module(item_info['import_path'])
                item_name = item_info.get('module_name', item_info['import_path'].split('.')[-1])
                item_map[item_name] = {
                    'module': module,
                    'info': item_info
                }
                
                # Find classes in this module and map them to item name
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (hasattr(obj, '__module__') and 
                        obj.__module__ == module.__name__):
                        class_to_item[name] = item_name
                
            except ImportError as e:
                self._log("warning", f"Failed to inspect {item_info.get('display', item_info['import_path'])}: {e}")
        
        # Second pass: build dependency graph
        for item_name, item_data in item_map.items():
            module = item_data['module']
            
            # Get dependencies
            dependencies = self._extract_dependencies(module)
            
            # Convert class dependencies to item dependencies
            item_dependencies = set()
            for class_dep in dependencies:
                if class_dep in class_to_item:
                    item_dependencies.add(class_to_item[class_dep])
            
            dependency_graph[item_name] = item_dependencies
            
            for dep_item in item_dependencies:
                reverse_graph[dep_item].add(item_name)
            
            if self._debug_mode and item_dependencies:
                self._log("debug", f"  {item_name}: depends on {item_dependencies}")
        
        return dependency_graph, reverse_graph, item_map
    
    def _extract_dependencies(self, module):
        """Extract dependencies from classes in a module"""
        dependencies = set()
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (hasattr(obj, '__module__') and 
                obj.__module__ == module.__name__):
                
                # Check for __depends_on__ attribute
                if hasattr(obj, '__depends_on__'):
                    deps = obj.__depends_on__
                    if isinstance(deps, str):
                        dependencies.add(deps)
                    elif isinstance(deps, (list, tuple)):
                        dependencies.update(deps)
        
        return dependencies
    
    def topological_sort(self, dependency_graph):
        """
        Perform topological sort on dependency graph using Kahn's algorithm.
        Returns sorted list of nodes.
        Raises exception if circular dependency detected.
        """
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
            self._analyze_circular_dependencies(dependency_graph, remaining)
            raise Exception(f"Circular dependency detected: {', '.join(sorted(remaining))}")
        
        return result
    
    def _analyze_circular_dependencies(self, dependency_graph, involved_nodes):
        """Analyze and report circular dependencies in detail"""
        self._log("error", "=" * 60)
        self._log("error", "CIRCULAR DEPENDENCY DETECTED!")
        self._log("error", "=" * 60)
        
        # Find all cycles
        cycles = self._find_all_cycles(dependency_graph, involved_nodes)
        
        self._log("error", f"Found {len(cycles)} circular dependency chain(s):")
        
        for i, cycle in enumerate(cycles, 1):
            self._log("error", f"\nCycle {i}:")
            for j in range(len(cycle)):
                current = cycle[j]
                next_node = cycle[(j + 1) % len(cycle)]
                self._log("error", f"  {current} -> {next_node}")
        
        self._log("error", f"\nNodes involved in circular dependencies: {', '.join(sorted(involved_nodes))}")
        
        # Suggest resolution
        self._log("info", "\nTo resolve circular dependencies:")
        self._log("info", "1. Review the __depends_on__ attributes in the listed items")
        self._log("info", "2. Consider if all dependencies are necessary")
        self._log("info", "3. Look for dependencies that can be delayed (lazy loading)")
        self._log("info", "4. Consider extracting shared functionality to a base class")
    
    def _find_all_cycles(self, graph, nodes_to_check):
        """Find all cycles in the given nodes using DFS"""
        cycles = []
        
        def dfs(node, path, visited):
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in nodes_to_check:
                    dfs(neighbor, path[:], visited.copy())
        
        for node in nodes_to_check:
            dfs(node, [], set())
        
        # Deduplicate cycles
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            min_idx = cycle.index(min(cycle))
            normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(list(normalized))
        
        return unique_cycles
    
    def resolve_dependencies(self, items, item_type="item", callback=None):
        """
        Main method to resolve dependencies and return items in correct order.
        
        Args:
            items: List of dicts with 'import_path' and optionally 'module_name'
            item_type: Type name for logging (e.g., "model", "class")
            callback: Optional function to call for each item after sorting
            
        Returns:
            List of items in dependency order
        """
        if not items:
            self._log("warning", f"No {item_type}s to resolve")
            return []
        
        try:
            # Build dependency graph
            dependency_graph, reverse_graph, item_map = self.build_dependency_graph(items, item_type)
            
            if not dependency_graph:
                self._log("info", f"No dependencies found, returning {item_type}s in original order")
                return items
            
            # Sort by dependencies
            sorted_item_names = self.topological_sort(dependency_graph)
            
            self._log("info", f"Resolved {len(sorted_item_names)} {item_type}s in dependency order")
            
            # Build sorted result
            sorted_items = []
            for item_name in sorted_item_names:
                if item_name in item_map:
                    item_data = item_map[item_name]
                    sorted_items.append(item_data['info'])
                    
                    if callback:
                        callback(item_data['module'], item_data['info'])
            
            return sorted_items
            
        except Exception as e:
            self._log("error", f"Dependency resolution failed: {e}")
            raise


class ClassDependencyResolver(DependencyResolver):
    """Specialized resolver for class dependencies"""
    
    def build_class_dependency_graph(self, items):
        """
        Build dependency graph for individual classes (not modules).
        Returns dict of {class_name: {'class': cls, 'module': module, 'info': item_info, 'dependencies': [deps]}}
        """
        all_classes = {}
        
        self._log("info", "Building class dependency graph...")
        
        # Discover all classes in all modules
        for item_info in items:
            try:
                module = importlib.import_module(item_info['import_path'])
                
                # Find all classes in this module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (hasattr(obj, '__module__') and
                        obj.__module__ == module.__name__):
                        
                        # Get dependencies
                        deps = getattr(obj, '__depends_on__', [])
                        if isinstance(deps, str):
                            deps = [deps]
                        elif not isinstance(deps, (list, tuple)):
                            deps = []
                        
                        all_classes[name] = {
                            'class': obj,
                            'module': module,
                            'info': item_info,
                            'dependencies': deps
                        }
                
            except ImportError as e:
                self._log("warning", f"Failed to inspect {item_info.get('display', item_info['import_path'])}: {e}")
        
        return all_classes
    
    def topological_sort_classes(self, all_classes):
        """Sort classes by dependencies using Kahn's algorithm"""
        # Build adjacency list and in-degree count
        graph = defaultdict(set)
        in_degree = defaultdict(int)
        
        # Initialize all nodes
        for class_name in all_classes:
            if class_name not in in_degree:
                in_degree[class_name] = 0
        
        # Build graph
        for class_name, class_data in all_classes.items():
            for dep in class_data['dependencies']:
                if dep in all_classes:  # Only count dependencies we can resolve
                    graph[dep].add(class_name)
                    in_degree[class_name] += 1
        
        # Find all nodes with no dependencies
        queue = deque([node for node in all_classes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Decrease in-degree for all dependents
            for dependent in graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for circular dependencies
        if len(result) != len(all_classes):
            remaining = set(all_classes.keys()) - set(result)
            # Create simple graph for analysis
            simple_graph = {}
            for class_name in remaining:
                simple_graph[class_name] = set(all_classes[class_name]['dependencies']) & remaining
            self._analyze_circular_dependencies(simple_graph, remaining)
            raise Exception(f"Circular dependency detected: {', '.join(sorted(remaining))}")
        
        return result
    
    def resolve_class_dependencies(self, items, callback=None):
        """
        Resolve dependencies for classes specifically.
        
        Args:
            items: List of module info dicts
            callback: Optional function(class_name, class_obj, module, info) to call for each class
            
        Returns:
            Ordered list of (class_name, class_data) tuples
        """
        if not items:
            self._log("warning", "No items to resolve")
            return []
        
        try:
            # Build class-level dependency graph
            all_classes = self.build_class_dependency_graph(items)
            
            if not all_classes:
                self._log("warning", "No classes found to import")
                return []
            
            # Sort classes by dependencies
            sorted_class_names = self.topological_sort_classes(all_classes)
            
            self._log("info", f"Importing {len(sorted_class_names)} classes in dependency order:")
            
            if self._debug_mode:
                # Log the order for debugging
                for i, name in enumerate(sorted_class_names):
                    deps = all_classes[name]['dependencies']
                    deps_str = f" (depends on: {', '.join(deps)})" if deps else " (no dependencies)"
                    self._log("debug", f"  {i+1}. {name}{deps_str}")
            
            # Build result
            result = []
            for class_name in sorted_class_names:
                class_data = all_classes[class_name]
                result.append((class_name, class_data))
                
                if callback:
                    callback(class_name, class_data['class'], class_data['module'], class_data['info'])
            
            return result
            
        except Exception as e:
            self._log("error", f"Class dependency resolution failed: {e}")
            raise
