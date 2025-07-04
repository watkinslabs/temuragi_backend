#!/usr/bin/env python3
"""
Class CLI - Manage and inspect class dependencies
"""

import sys
import argparse
from collections import defaultdict, deque

sys.path.append('/web/ahoy2.radiatorusa.com')
from app.base.cli_v1 import BaseCLI


CLI_DESCRIPTION = "Class dependency management and inspection"

class ClassCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI without database connection"""
        super().__init__(
            name="class",
            log_file="logs/class_cli.log",
            connect_db=False,  # Classes don't need DB
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )


    def list_all_classes(self, show_dependencies=False):
        """List all registered classes"""
        self.log_info("Listing all classes")

        try:
            if not self.class_registry:
                self.output_warning("No classes found in registry")
                return 0

            if show_dependencies:
                headers = ["Class Name", "Module", "Dependencies", "Used By"]
            else:
                headers = ["Class Name", "Module", "File"]
            
            rows = []

            # Build reverse dependency map
            used_by = defaultdict(list)
            for class_name, cls in self.class_registry.items():
                deps = getattr(cls, '__depends_on__', [])
                if isinstance(deps, str):
                    deps = [deps]
                for dep in deps:
                    used_by[dep].append(class_name)

            for class_name, cls in sorted(self.class_registry.items()):
                module_parts = cls.__module__.split('.')
                module_short = '.'.join(module_parts[-2:]) if len(module_parts) > 2 else cls.__module__
                
                if show_dependencies:
                    deps = getattr(cls, '__depends_on__', [])
                    if isinstance(deps, str):
                        deps = [deps]
                    
                    rows.append([
                        class_name,
                        module_short,
                        ', '.join(deps) if deps else 'None',
                        ', '.join(used_by.get(class_name, [])) or 'None'
                    ])
                else:
                    # Get file path from module
                    file_path = getattr(sys.modules[cls.__module__], '__file__', 'Unknown')
                    file_short = '/'.join(file_path.split('/')[-3:]) if '/' in file_path else file_path
                    
                    rows.append([
                        class_name,
                        module_short,
                        file_short
                    ])

            self.output_info(f"Registered Classes ({len(rows)} total):")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing classes: {e}")
            self.output_error(f"Error listing classes: {e}")
            return 1

    def show_class_info(self, class_name):
        """Show detailed information about a specific class"""
        self.log_info(f"Showing info for class: {class_name}")

        try:
            cls = self.class_registry.get(class_name)
            if not cls:
                self.output_error(f"Class '{class_name}' not found")
                self.output_info(f"Available classes: {', '.join(sorted(self.class_registry.keys()))}")
                return 1

            self.output_info(f"Class: {class_name}")
            self.output_info(f"Module: {cls.__module__}")
            
            # Get file path
            file_path = getattr(sys.modules[cls.__module__], '__file__', 'Unknown')
            self.output_info(f"File: {file_path}")

            # Show dependencies
            deps = getattr(cls, '__depends_on__', [])
            if isinstance(deps, str):
                deps = [deps]
            
            if deps:
                self.output_info(f"Dependencies ({len(deps)}):")
                for dep in deps:
                    if dep in self.class_registry:
                        self.output_success(f"  ✓ {dep}")
                    else:
                        self.output_warning(f"  ✗ {dep} (not found)")
            else:
                self.output_info("Dependencies: None")

            # Show what uses this class
            used_by = []
            for other_name, other_cls in self.class_registry.items():
                other_deps = getattr(other_cls, '__depends_on__', [])
                if isinstance(other_deps, str):
                    other_deps = [other_deps]
                if class_name in other_deps:
                    used_by.append(other_name)
            
            if used_by:
                self.output_info(f"Used by ({len(used_by)}):")
                for user in used_by:
                    self.output_info(f"  - {user}")
            else:
                self.output_info("Used by: None")

            # Show class docstring
            if cls.__doc__:
                self.output_info(f"Description: {cls.__doc__.strip()}")

            return 0

        except Exception as e:
            self.log_error(f"Error showing class info: {e}")
            self.output_error(f"Error showing class info: {e}")
            return 1

    def show_load_order(self):
        """Show the topological load order for all classes"""
        self.log_info("Calculating class load order")

        try:
            # Build dependency graph
            dep_graph = {}
            reverse_graph = defaultdict(list)  # Who depends on each class
            
            for class_name, cls in self.class_registry.items():
                deps = getattr(cls, '__depends_on__', [])
                if isinstance(deps, str):
                    deps = [deps]
                
                # Only include deps that are in registry
                valid_deps = [d for d in deps if d in self.class_registry]
                dep_graph[class_name] = valid_deps
                
                # Build reverse graph
                for dep in valid_deps:
                    reverse_graph[dep].append(class_name)

            # Topological sort using Kahn's algorithm
            in_degree = defaultdict(int)
            
            # Calculate in-degrees (how many things each class depends on)
            for node, deps in dep_graph.items():
                in_degree[node] = len(deps)
            
            # Ensure all nodes are in in_degree
            for node in dep_graph:
                if node not in in_degree:
                    in_degree[node] = 0

            # Debug: Show initial state
            self.log_debug("Initial dependency state:")
            zero_deps = [n for n, d in in_degree.items() if d == 0]
            self.log_debug(f"  Classes with no dependencies: {zero_deps}")
            non_zero = [(n, d) for n, d in in_degree.items() if d > 0]
            if non_zero:
                self.log_debug(f"  Classes with dependencies:")
                for node, degree in non_zero:
                    self.log_debug(f"    {node}: {degree} deps -> {dep_graph[node]}")

            # Find all nodes with no dependencies
            queue = deque([node for node in dep_graph if in_degree[node] == 0])
            self.log_debug(f"Initial queue: {list(queue)}")
            
            load_order = []
            iteration = 0

            while queue:
                iteration += 1
                node = queue.popleft()
                load_order.append(node)
                self.log_debug(f"Iteration {iteration}: Processing {node}")
                
                # For each class that depends on this one
                for dependent in reverse_graph[node]:
                    in_degree[dependent] -= 1
                    self.log_debug(f"  Decreased in_degree of {dependent} to {in_degree[dependent]}")
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
                        self.log_debug(f"  Added {dependent} to queue")

            # Check if all nodes were processed
            if len(load_order) != len(dep_graph):
                # Some nodes weren't processed
                processed = set(load_order)
                unprocessed = set(dep_graph.keys()) - processed
                
                self.output_error("Circular dependency detected!")
                self.output_error("=" * 60)
                
                # Debug why these weren't processed
                self.output_error("\nDEBUG: Unprocessed classes analysis:")
                for class_name in sorted(unprocessed):
                    self.output_error(f"\n{class_name}:")
                    self.output_error(f"  Dependencies: {dep_graph[class_name]}")
                    self.output_error(f"  Final in_degree: {in_degree[class_name]}")
                    self.output_error(f"  Depended on by: {reverse_graph[class_name]}")
                    
                    # Check if dependencies are also unprocessed
                    unproc_deps = [d for d in dep_graph[class_name] if d in unprocessed]
                    if unproc_deps:
                        self.output_error(f"  Unprocessed dependencies: {unproc_deps}")
                
                # Now find actual cycles
                self.output_error("\nSearching for circular dependencies...")
                
                def find_cycles(graph, nodes):
                    cycles = []
                    
                    def dfs(node, path, visited):
                        if node in path:
                            cycle_idx = path.index(node)
                            cycle = path[cycle_idx:] + [node]
                            cycles.append(cycle)
                            return
                        
                        if node in visited:
                            return
                        
                        visited.add(node)
                        path.append(node)
                        
                        for neighbor in graph.get(node, []):
                            if neighbor in nodes:  # Only follow edges within unprocessed nodes
                                dfs(neighbor, path[:], visited.copy())
                    
                    for node in nodes:
                        dfs(node, [], set())
                    
                    # Deduplicate
                    unique = []
                    seen = set()
                    for cycle in cycles:
                        if len(cycle) > 1:
                            normalized = tuple(sorted(cycle[:-1]))
                            if normalized not in seen:
                                seen.add(normalized)
                                unique.append(cycle)
                    
                    return unique
                
                cycles = find_cycles(dep_graph, unprocessed)
                
                if cycles:
                    self.output_error(f"\nFound {len(cycles)} circular dependency cycle(s):")
                    
                    for i, cycle in enumerate(cycles, 1):
                        self.output_error(f"\nCycle #{i}: {' -> '.join(cycle)}")
                        
                        # Show dependency tree
                        def show_tree(node, visited=None, indent=0, prefix=""):
                            if visited is None:
                                visited = set()
                            
                            if node in visited:
                                self.output_error(f"{prefix}└── {node} ← CIRCULAR!")
                                return
                            
                            if indent == 0:
                                self.output_error(node)
                            else:
                                self.output_error(f"{prefix}└── {node}")
                            
                            visited.add(node)
                            new_prefix = prefix + "    "
                            
                            for dep in dep_graph.get(node, []):
                                show_tree(dep, visited.copy(), indent + 1, new_prefix)
                        
                        show_tree(cycle[0])
                        self.output_error("")
                else:
                    self.output_error("\nNo cycles found! This suggests a bug in the topological sort.")
                    self.output_error("The unprocessed classes might have dependencies on classes not in the registry.")
                
                return 1
            
            # Success - show load order
            self.output_info("Class Load Order:")
            headers = ["Order", "Class Name", "Dependencies"]
            rows = []

            for i, class_name in enumerate(load_order, 1):
                deps = dep_graph[class_name]
                rows.append([
                    str(i),
                    class_name,
                    ', '.join(deps) if deps else 'None'
                ])

            self.output_table(rows, headers=headers)
            
            self.output_success(f"Total: {len(load_order)} classes")
            return 0

        except Exception as e:
            self.log_error(f"Error calculating load order: {e}")
            self.output_error(f"Error calculating load order: {e}")
            return 1
        
    def check_dependencies(self):
        """Check for missing or circular dependencies"""
        self.log_info("Checking class dependencies")

        try:
            missing_deps = defaultdict(list)
            circular_deps = []

            # Check each class
            for class_name, cls in self.class_registry.items():
                deps = getattr(cls, '__depends_on__', [])
                if isinstance(deps, str):
                    deps = [deps]

                # Check for missing dependencies
                for dep in deps:
                    if dep not in self.class_registry:
                        missing_deps[class_name].append(dep)

            # Enhanced circular dependency detection
            def find_all_cycles(dep_graph):
                """Find all cycles in dependency graph"""
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
                    
                    for neighbor in dep_graph.get(node, []):
                        dfs(neighbor, path[:], visited.copy())
                
                for node in dep_graph:
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

            # Build dep graph
            dep_graph = {}
            for class_name, cls in self.class_registry.items():
                deps = getattr(cls, '__depends_on__', [])
                if isinstance(deps, str):
                    deps = [deps]
                dep_graph[class_name] = [d for d in deps if d in self.class_registry]

            # Find circular dependencies
            circular_deps = find_all_cycles(dep_graph)

            # Report results
            if not missing_deps and not circular_deps:
                self.output_success("✓ All dependencies are valid!")
                return 0

            if missing_deps:
                self.output_error("Missing Dependencies:")
                for class_name, missing in missing_deps.items():
                    self.output_error(f"  {class_name}:")
                    for dep in missing:
                        self.output_error(f"    ✗ {dep}")

            if circular_deps:
                self.output_error("\nCircular Dependencies Detected!")
                self.output_error("=" * 60)
                
                # Helper function to build dependency tree
                def build_dependency_tree(class_name, dep_graph, visited=None, indent=0, prefix="", is_last=True, cycle_path=None):
                    """Build a tree visualization of dependencies"""
                    if visited is None:
                        visited = set()
                    
                    tree_lines = []
                    
                    # Determine the connector symbols
                    if indent == 0:
                        connector = ""
                        new_prefix = ""
                    else:
                        connector = "└── " if is_last else "├── "
                        new_prefix = prefix + ("    " if is_last else "│   ")
                    
                    # Check if this creates a cycle
                    if class_name in visited:
                        tree_lines.append(f"{prefix}{connector}{class_name} ← CIRCULAR DEPENDENCY!")
                        return tree_lines
                    
                    # Add current class
                    tree_lines.append(f"{prefix}{connector}{class_name}")
                    
                    # Add this class to visited
                    visited.add(class_name)
                    
                    # Get dependencies
                    deps = dep_graph.get(class_name, [])
                    
                    # Process each dependency
                    for i, dep in enumerate(deps):
                        is_last_dep = (i == len(deps) - 1)
                        
                        # Check if this dependency is part of the cycle
                        if cycle_path and dep in cycle_path:
                            # Highlight cycle dependencies
                            dep_lines = build_dependency_tree(
                                dep, 
                                dep_graph, 
                                visited.copy(), 
                                indent + 1, 
                                new_prefix, 
                                is_last_dep,
                                cycle_path
                            )
                        else:
                            # Regular dependency
                            dep_lines = build_dependency_tree(
                                dep, 
                                dep_graph, 
                                visited.copy(), 
                                indent + 1, 
                                new_prefix, 
                                is_last_dep,
                                cycle_path
                            )
                        
                        tree_lines.extend(dep_lines)
                    
                    return tree_lines
                
                # For each cycle, show the full dependency tree
                for i, cycle in enumerate(circular_deps, 1):
                    self.output_error(f"\nCircular Dependency #{i}")
                    self.output_error(f"Cycle: {' -> '.join(cycle)}")
                    self.output_error("")
                    
                    # Convert cycle to set for easy lookup (excluding the duplicate at end)
                    cycle_set = set(cycle[:-1])
                    
                    # Show tree for each class in the cycle
                    self.output_error("Dependency trees for classes in this cycle:")
                    self.output_error("")
                    
                    for class_name in cycle[:-1]:  # Skip the duplicate at end
                        tree_lines = build_dependency_tree(class_name, dep_graph, cycle_path=cycle_set)
                        for line in tree_lines:
                            self.output_error(line)
                        self.output_error("")  # Empty line between trees
                
                # Show summary
                self.output_error("=" * 60)
                self.output_error("Summary:")
                
                # Show all involved classes
                involved = set()
                for cycle in circular_deps:
                    involved.update(cycle[:-1])  # Don't count the duplicate at end
                
                self.output_error(f"Total cycles found: {len(circular_deps)}")
                self.output_error(f"Total classes in cycles: {len(involved)}")
                self.output_error(f"Classes: {', '.join(sorted(involved))}")
                
                # Show which classes are in multiple cycles
                class_cycle_count = defaultdict(int)
                for cycle in circular_deps:
                    for class_name in cycle[:-1]:
                        class_cycle_count[class_name] += 1
                
                multi_cycle_classes = [(name, count) for name, count in class_cycle_count.items() if count > 1]
                if multi_cycle_classes:
                    self.output_error(f"\nClasses in multiple cycles:")
                    for name, count in sorted(multi_cycle_classes, key=lambda x: x[1], reverse=True):
                        self.output_error(f"  {name}: {count} cycles")

            return 1

        except Exception as e:
            self.log_error(f"Error checking dependencies: {e}")
            self.output_error(f"Error checking dependencies: {e}")
            return 1
        
    def close(self):
        """Clean up resources"""
        self.log_debug("Closing class CLI")
        super().close()

    def debug_class(self, class_name):
        """Debug why a class might be missing or having issues"""
        self.log_info(f"Debugging class: {class_name}")
        
        try:
            # Check if class is in registry
            cls = self.class_registry.get(class_name)
            if cls:
                self.output_success(f"✓ Class '{class_name}' found in registry")
                self.show_class_info(class_name)
                return 0
            
            self.output_warning(f"✗ Class '{class_name}' NOT in registry")
            
            # Search for files that might contain this class
            self.output_info("\nSearching for potential files...")
            
            import os
            import re
            from app.config import config
            
            # Get app root
            register_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            app_root = os.path.dirname(register_dir)
            
            found_files = []
            pattern = re.compile(rf'class\s+{class_name}\s*[:\(]', re.MULTILINE)
            
            for scan_path in config['SYSTEM_SCAN_PATHS']:
                base_dir = os.path.join(app_root, scan_path)
                if not os.path.exists(base_dir):
                    continue
                    
                for root, dirs, files in os.walk(base_dir):
                    for filename in files:
                        if filename.endswith('.py'):
                            filepath = os.path.join(root, filename)
                            try:
                                with open(filepath, 'r') as f:
                                    content = f.read()
                                    if pattern.search(content):
                                        rel_path = os.path.relpath(filepath, app_root)
                                        found_files.append(rel_path)
                            except:
                                pass
            
            if found_files:
                self.output_info(f"\nFound class '{class_name}' defined in:")
                for filepath in found_files:
                    self.output_info(f"  - {filepath}")
                    
                    # Check if it's a _class.py file
                    if not filepath.endswith('_class.py'):
                        self.output_warning(f"    ⚠ File doesn't match *_class.py pattern!")
            else:
                self.output_error(f"\nClass '{class_name}' not found in any Python files")
            
            # Show similar class names
            similar = [name for name in self.class_registry.keys() 
                    if class_name.lower() in name.lower() or name.lower() in class_name.lower()]
            
            if similar:
                self.output_info(f"\nSimilar classes in registry:")
                for name in similar:
                    self.output_info(f"  - {name}")
            
            return 1
            
        except Exception as e:
            self.log_error(f"Error debugging class: {e}")
            self.output_error(f"Error debugging class: {e}")
            return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst'],
                       help='Override table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List classes
    list_parser = subparsers.add_parser('list', help='List all registered classes')
    list_parser.add_argument('--deps', '-d', action='store_true', 
                           help='Show dependencies and usage')

    # Show class info
    info_parser = subparsers.add_parser('info', help='Show detailed info about a class')
    info_parser.add_argument('class_name', help='Name of the class')

    # Show load order
    subparsers.add_parser('load-order', help='Show topological load order')

    # Check dependencies
    subparsers.add_parser('check', help='Check for dependency issues')


    # Debug a specific class
    debug_parser = subparsers.add_parser('debug', help='Debug why a class might be missing')
    debug_parser.add_argument('class_name', help='Name of the class to debug')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = ClassCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute commands
    try:
        if args.command == 'list':
            return cli.list_all_classes(show_dependencies=args.deps)
        elif args.command == 'info':
            return cli.show_class_info(args.class_name)
        elif args.command == 'load-order':
            return cli.show_load_order()
        elif args.command == 'check':
            return cli.check_dependencies()
        elif args.command == 'debug':
            return cli.debug_class(args.class_name)    
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())