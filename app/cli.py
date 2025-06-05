#!/usr/bin/env python3
"""
Master CLI - Recursive CLI Module Loader
Automatically discovers and loads all *_cli.py modules from the project
Usage: python -m app.cli <module_name> [args...]
"""

import os
import sys
import importlib
import inspect
import argparse
from pathlib import Path


class CLILoader:
    def __init__(self, base_path=None):
        """Initialize CLI loader with base search path"""
        if base_path is None:
            # Use the directory containing this file as base
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
        
        self.discovered_clis = {}
        self.root_package = self._determine_root_package()
    
    def _determine_root_package(self):
        """Determine the root package name from the current module"""
        # Get the package this module is in (e.g., 'app')
        return __package__.split('.')[0] if __package__ else 'app'
    
    def discover_cli_modules(self):
        """Recursively discover all *_cli.py modules"""
        print(f"🔍 Discovering CLI modules in {self.base_path}...")
        
        for dirpath, dirnames, filenames in os.walk(self.base_path):
            # Skip certain directories
            dirnames[:] = [d for d in dirnames if not d.startswith('.') 
                          and d not in ['__pycache__', 'static', 'templates']]
            
            # Look for CLI files
            cli_files = [f for f in filenames if f.endswith('_cli.py')]
            
            for cli_file in cli_files:
                self._register_cli_module(dirpath, cli_file)
        
        print(f"✓ Found {len(self.discovered_clis)} CLI modules")
        return self.discovered_clis
    
    def _register_cli_module(self, dirpath, cli_file):
        """Register a discovered CLI module"""
        try:
            # Convert file path to module import path
            rel_path = os.path.relpath(dirpath, self.base_path.parent)
            path_parts = rel_path.split(os.sep)
            
            # Build import path: app.admin.something.module_cli
            module_name = cli_file[:-3]  # Remove .py extension
            import_path = '.'.join(filter(None, path_parts + [module_name]))
            
            # Extract CLI name from filename (remove _cli suffix)
            cli_name = module_name[:-4] if module_name.endswith('_cli') else module_name
            
            # Store the CLI registration
            self.discovered_clis[cli_name] = {
                'import_path': import_path,
                'file_path': os.path.join(dirpath, cli_file),
                'module_name': module_name
            }
            
            print(f"  📝 {cli_name} -> {import_path}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to register {cli_file}: {e}")
    
    def load_cli_module(self, cli_name):
        """Load and return a specific CLI module"""
        if cli_name not in self.discovered_clis:
            print(f"❌ CLI module '{cli_name}' not found")
            print(f"Available modules: {', '.join(self.discovered_clis.keys())}")
            return None
        
        cli_info = self.discovered_clis[cli_name]
        
        try:
            # Import the module
            module = importlib.import_module(cli_info['import_path'])
            
            # Look for main function or CLI class
            if hasattr(module, 'main'):
                return module.main
            elif hasattr(module, 'CLI'):
                return module.CLI
            else:
                # Look for any callable that might be the CLI entry point
                for name, obj in inspect.getmembers(module):
                    if (inspect.isfunction(obj) and 
                        name in ['cli', 'run', 'execute'] and 
                        not name.startswith('_')):
                        return obj
                
                print(f"❌ No main(), CLI class, or entry point found in {cli_name}")
                return None
                
        except ImportError as e:
            print(f"❌ Failed to import {cli_name}: {e}")
            return None
    
    def list_available_clis(self):
        """List all available CLI modules"""
        if not self.discovered_clis:
            print("No CLI modules found")
            return
        
        print("\n📋 Available CLI Modules:")
        print("=" * 50)
        
        for cli_name, cli_info in sorted(self.discovered_clis.items()):
            # Try to get description from module docstring
            try:
                module = importlib.import_module(cli_info['import_path'])
                description = (module.__doc__ or "").strip().split('\n')[0]
                if not description:
                    description = "No description available"
            except:
                description = "Import failed"
            
            print(f"  {cli_name:15} - {description}")
        
        print("\n💡 Usage: python -m app.cli <module_name> [args...]")
    
    def run_cli(self, cli_name, args=None):
        """Run a specific CLI module"""
        if args is None:
            args = []
        
        # Load the CLI module
        cli_func = self.load_cli_module(cli_name)
        if not cli_func:
            return 1
        
        try:
            # Temporarily modify sys.argv for the CLI module
            original_argv = sys.argv[:]
            sys.argv = [f"{cli_name}_cli.py"] + args
            
            # Run the CLI
            result = cli_func()
            
            # Restore original argv
            sys.argv = original_argv
            
            return result if result is not None else 0
            
        except SystemExit as e:
            # Handle sys.exit() calls from the CLI
            return e.code if e.code is not None else 0
        except Exception as e:
            print(f"❌ Error running {cli_name}: {e}")
            return 1


def create_dynamic_parser(loader):
    """Create argument parser with dynamic subcommands"""
    parser = argparse.ArgumentParser(
        description='Master CLI - Recursive CLI Module Loader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli list                    # List available CLI modules
  python -m app.cli menu status             # Run menu CLI with 'status' command
  python -m app.cli firewall list --all     # Run firewall CLI with arguments
  python -m app.cli backup create daily     # Run backup CLI with multiple args
        """
    )
    
    # Discover CLI modules first
    loader.discover_cli_modules()
    
    subparsers = parser.add_subparsers(dest='cli_module', help='Available CLI modules')
    
    # Add 'list' command to show available modules
    list_parser = subparsers.add_parser('list', help='List all available CLI modules')
    
    # Add discovered CLI modules as subcommands
    for cli_name in loader.discovered_clis.keys():
        cli_parser = subparsers.add_parser(
            cli_name, 
            help=f'Run {cli_name} CLI module',
            add_help=False  # Let the actual CLI handle help
        )
        cli_parser.add_argument('cli_args', nargs='*', help='Arguments for the CLI module')
    
    return parser


def main():
    """Main entry point for master CLI"""
    # Initialize loader
    loader = CLILoader()
    
    # Create dynamic parser
    parser = create_dynamic_parser(loader)
    
    # Handle case where no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n" + "="*50)
        loader.list_available_clis()
        return 0
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.cli_module:
        parser.print_help()
        return 1
    
    # Handle special 'list' command
    if args.cli_module == 'list':
        loader.list_available_clis()
        return 0
    
    # Run the specified CLI module
    cli_args = getattr(args, 'cli_args', [])
    return loader.run_cli(args.cli_module, cli_args)


if __name__ == '__main__':
    sys.exit(main())