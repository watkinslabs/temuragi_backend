#!/usr/bin/env python3
"""
Class CLI - Manage and inspect class dependencies
"""

import sys
import argparse
from collections import defaultdict, deque
sys.path.append('/web/temuragi')
from app.base.cli import BaseCLI
from app.register.classes import (
    register_classes_for_cli
)

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

        self.log_info("Starting class CLI initialization")

        try:
            # Register classes for CLI usage
            self.class_registry = register_classes_for_cli()
            self.log_info(f"Loaded {len(self.class_registry)} classes")
                        
            self.log_info("Class CLI initialized successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize class CLI: {e}")
            raise

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
            for class_name, cls in self.class_registry.items():
                deps = getattr(cls, '__depends_on__', [])
                if isinstance(deps, str):
                    deps = [deps]
                # Only include deps that are in registry
                valid_deps = [d for d in deps if d in self.class_registry]
                dep_graph[class_name] = valid_deps

            # Topological sort
            in_degree = defaultdict(int)
            for node, deps in dep_graph.items():
                for dep in deps:
                    in_degree[dep] += 1

            # Find nodes with no dependencies
            queue = deque([node for node in dep_graph if in_degree[node] == 0])
            load_order = []

            while queue:
                node = queue.popleft()
                load_order.append(node)
                
                # Update in-degrees
                for other, deps in dep_graph.items():
                    if node in deps:
                        in_degree[other] -= 1
                        if in_degree[other] == 0:
                            queue.append(other)

            # Check for circular dependencies
            if len(load_order) != len(dep_graph):
                missing = set(dep_graph.keys()) - set(load_order)
                self.output_error(f"Circular dependency detected!")
                self.output_error(f"Classes involved: {', '.join(missing)}")
                
                # Show the circular deps
                for cls in missing:
                    deps = dep_graph[cls]
                    circular = [d for d in deps if d in missing]
                    if circular:
                        self.output_error(f"  {cls} -> {circular}")
                return 1

            # Display load order
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
                
                for i, cycle in enumerate(circular_deps, 1):
                    self.output_error(f"\nCycle {i}: {' -> '.join(cycle)}")
                    
                    # Show details for each edge in the cycle
                    for j in range(len(cycle) - 1):
                        current = cycle[j]
                        next_class = cycle[j + 1]
                        cls = self.class_registry[current]
                        module = cls.__module__
                        self.output_error(f"  {current} depends on {next_class}")
                        self.output_error(f"    (defined in {module})")
                
                # Show all involved classes
                involved = set()
                for cycle in circular_deps:
                    involved.update(cycle[:-1])  # Don't count the duplicate at end
                
                self.output_error(f"\nTotal classes in cycles: {len(involved)}")
                self.output_error(f"Classes: {', '.join(sorted(involved))}")

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