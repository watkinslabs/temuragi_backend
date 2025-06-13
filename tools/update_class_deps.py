#!/usr/bin/env python3
import argparse
import ast
import os
import re
from pathlib import Path
import json

def find_all_classes(root_dir):
    """
    Find all Python files and extract class definitions
    Returns: {
        'ClassName': {
            'file': '/path/to/file.py',
            'line': 42,
            'bases': ['BaseClass'],
            'dependencies': ['OtherClass', 'AnotherClass'],
        },
        ...
    }
    """
    class_registry = {}
    
    # First pass: Find all classes
    for py_file in Path(root_dir).rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                tree = ast.parse(f.read(), filename=str(py_file))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'file': str(py_file),
                        'line': node.lineno,
                        'bases': [base.id for base in node.bases 
                                 if isinstance(base, ast.Name)],
                        'dependencies': []  # Will be filled in second pass
                    }
                    class_registry[node.name] = class_info
                    
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")
    
    return class_registry

def find_class_dependencies(file_path, class_registry):
    """
    Find which classes each class in a file depends on
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.splitlines()
        
        tree = ast.parse(content, filename=file_path)
        dependencies = {}
        
        # Get all class names we're looking for
        all_class_names = set(class_registry.keys())
        
        # Get all classes in this file
        class_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_nodes.append(node)
        
        # Sort by line number
        class_nodes.sort(key=lambda x: x.lineno)
        
        for i, node in enumerate(class_nodes):
            class_name = node.name
            class_start = node.lineno - 1  # 0-indexed
            
            # Find class end
            if i + 1 < len(class_nodes):
                class_end = class_nodes[i + 1].lineno - 1
            else:
                class_end = len(lines)
            
            # Extract class body
            class_lines = lines[class_start:class_end]
            class_body = '\n'.join(class_lines)
            
            # Find references to other classes
            found_deps = set()
            for other_class in all_class_names:
                if other_class != class_name:  # Don't include self
                    # Multiple patterns to catch different usage types
                    patterns = [
                        rf'\b{other_class}\(',  # Direct instantiation
                        rf'\b{other_class}\.',  # Class method/attribute
                        rf':\s*{other_class}\b',  # Type hints
                        rf'isinstance\([^,]+,\s*{other_class}\)',  # isinstance
                        rf'["\']{{other_class}}["\']',  # String reference
                        rf'get_class\(["\']{{other_class}}["\']',  # get_class
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, class_body):
                            found_deps.add(other_class)
                            break
            
            dependencies[class_name] = sorted(list(found_deps))
        
        return dependencies
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {}

def analyze_all_dependencies(root_dir):
    """
    Main function to analyze all classes and their dependencies
    """
    print(f"Scanning {root_dir} for Python classes...")
    
    # First pass: discover all classes
    class_registry = find_all_classes(root_dir)
    print(f"Found {len(class_registry)} classes")
    
    # Second pass: find dependencies for each file
    processed_files = set()
    
    for class_name, class_info in class_registry.items():
        file_path = class_info['file']
        
        # Only process each file once
        if file_path not in processed_files:
            processed_files.add(file_path)
            
            # Find all dependencies in this file
            file_deps = find_class_dependencies(file_path, class_registry)
            
            # Update registry with dependencies
            for cls_name, deps in file_deps.items():
                if cls_name in class_registry:
                    class_registry[cls_name]['dependencies'] = deps
    
    return class_registry

def resolve_transitive_dependencies(class_registry):
    """
    Resolve transitive dependencies recursively
    """
    def get_all_deps(class_name, visited=None):
        if visited is None:
            visited = set()
        
        if class_name in visited or class_name not in class_registry:
            return set()
        
        visited.add(class_name)
        all_deps = set()
        
        direct_deps = class_registry[class_name].get('dependencies', [])
        for dep in direct_deps:
            all_deps.add(dep)
            all_deps.update(get_all_deps(dep, visited.copy()))
        
        return all_deps
    
    # Add transitive dependencies
    for class_name in class_registry:
        trans_deps = get_all_deps(class_name)
        class_registry[class_name]['transitive_dependencies'] = sorted(list(trans_deps))
    
    return class_registry

def update_class_depends_on(class_registry, dry_run=False):
    """
    Update __depends_on__ in each class file
    """
    files_to_update = {}
    
    # Group classes by file
    for class_name, info in class_registry.items():
        file_path = info['file']
        if file_path not in files_to_update:
            files_to_update[file_path] = []
        files_to_update[file_path].append({
            'name': class_name,
            'line': info['line'],
            'dependencies': info.get('dependencies', [])
        })
    
    # Process each file
    for file_path, classes in files_to_update.items():
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Sort classes by line number (reverse order to update from bottom)
            classes.sort(key=lambda x: x['line'], reverse=True)
            
            for class_info in classes:
                class_name = class_info['name']
                class_line = class_info['line'] - 1  # 0-indexed
                deps = class_info['dependencies']
                
                if not deps:  # Skip if no dependencies
                    continue
                
                # Find where to insert __depends_on__
                insert_line = None
                existing_depends_line = None
                
                # Look for class definition and scan for insertion point
                for i in range(class_line, len(lines)):
                    line = lines[i]
                    stripped = line.strip()
                    
                    # Skip empty lines and comments after class definition
                    if i == class_line:  # class definition line
                        continue
                    
                    # Check if __depends_on__ already exists
                    if '__depends_on__' in stripped:
                        existing_depends_line = i
                        break
                    
                    # Find first non-comment, non-empty line after class
                    if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                        # Check if it's a docstring
                        if i > class_line and (lines[i-1].strip().endswith('"""') or lines[i-1].strip().endswith("'''")):
                            continue
                        insert_line = i
                        break
                
                # Prepare the __depends_on__ line
                indent = '    '  # Standard 4-space indent
                depends_line = f"{indent}__depends_on__ = {deps}\n"
                
                # Update or insert
                if existing_depends_line is not None:
                    lines[existing_depends_line] = depends_line
                    print(f"Updated {class_name} in {file_path}")
                elif insert_line is not None:
                    lines.insert(insert_line, depends_line)
                    print(f"Added __depends_on__ to {class_name} in {file_path}")
                else:
                    print(f"WARNING: Could not find insertion point for {class_name} in {file_path}")
            
            # Write back to file
            if not dry_run and any(c['dependencies'] for c in classes):
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                print(f"Updated {file_path}")
            elif dry_run:
                print(f"Would update {file_path}")
                
        except Exception as e:
            print(f"Error updating {file_path}: {e}")

# Add to main function
def main():
    parser = argparse.ArgumentParser(description='Analyze Python class dependencies')
    parser.add_argument('root', help='Root directory to scan')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--transitive', '-t', action='store_true', 
                       help='Include transitive dependencies')
    parser.add_argument('--update', '-u', action='store_true',
                       help='Update __depends_on__ in class files')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    # Analyze all classes and dependencies
    class_registry = analyze_all_dependencies(args.root)
    
    # Resolve transitive dependencies if requested
    if args.transitive:
        class_registry = resolve_transitive_dependencies(class_registry)
    
    # Update files if requested
    if args.update:
        update_class_depends_on(class_registry, dry_run=args.dry_run)
        return
    
    # ... rest of output logic

if __name__ == '__main__':
    main()