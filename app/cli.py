#!/usr/bin/env python3
"""
tmcli - Temuragi CLI Entry Point
Automatically discovers and loads all *_cli.py modules from the project
Usage: tmcli <module_name> [args...]
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
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
        
        self.discovered_clis = {}
        self.failed_modules = {}
        self.root_package = self._determine_root_package()
    
    def _determine_root_package(self):
        """Determine the root package name from the current module"""
        return __package__.split('.')[0] if __package__ else 'app'
    
    def discover_cli_modules(self, verbose=False):
        """Recursively discover all *_cli.py modules"""
        if verbose:
            print(f"🔍 Discovering CLI modules in {self.base_path}...")
        
        for dirpath, dirnames, filenames in os.walk(self.base_path):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') 
                          and d not in ['__pycache__', 'static', 'tpl']]
            
            cli_files = [f for f in filenames if f.endswith('_cli.py')]
            
            for cli_file in cli_files:
                if cli_file == "base_cli.py": 
                    continue
                self._register_cli_module(dirpath, cli_file, verbose)
        
        if verbose and self.failed_modules:
            print(f"\n⚠️  Failed to load {len(self.failed_modules)} modules:")
            for name, error in self.failed_modules.items():
                print(f"  {name}: {error}")
        
        return self.discovered_clis
    
    def _register_cli_module(self, dirpath, cli_file, verbose=False):
        """Register a discovered CLI module"""
        try:
            rel_path = os.path.relpath(dirpath, self.base_path.parent)
            path_parts = rel_path.split(os.sep)
            
            module_name = cli_file[:-3]
            import_path = '.'.join(filter(None, path_parts + [module_name]))
            cli_name = module_name[:-4] if module_name.endswith('_cli') else module_name
            
            self.discovered_clis[cli_name] = {
                'import_path': import_path,
                'file_path': os.path.join(dirpath, cli_file),
                'module_name': module_name
            }
            
            if verbose:
                print(f"  📝 {cli_name} -> {import_path}")
            
        except Exception as e:
            self.failed_modules[cli_file] = str(e)
    
    def _get_cli_description(self, cli_name):
        """Dynamically get CLI description by introspecting the module"""
        if cli_name not in self.discovered_clis:
            return "Module not found"
        
        cli_info = self.discovered_clis[cli_name]
        
        try:
            module = importlib.import_module(cli_info['import_path'])
            
            # Try multiple sources for description
            description = None
            
            # 1. Look for CLI_DESCRIPTION constant
            if hasattr(module, 'CLI_DESCRIPTION'):
                description = module.CLI_DESCRIPTION
            
            # 2. Look for get_description() function
            elif hasattr(module, 'get_description'):
                try:
                    description = module.get_description()
                except:
                    pass
            
            # 3. Check main function docstring
            elif hasattr(module, 'main') and module.main.__doc__:
                description = module.main.__doc__.strip().split('\n')[0]
            
            # 4. Check CLI class docstring
            elif hasattr(module, 'CLI') and module.CLI.__doc__:
                description = module.CLI.__doc__.strip().split('\n')[0]
            
            # 5. Fall back to module docstring
            elif module.__doc__:
                description = module.__doc__.strip().split('\n')[0]
            
            # 6. Try to get argparse description
            else:
                # Look for parser creation to extract description
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and 'parser' in name.lower():
                        try:
                            parser = obj()
                            if hasattr(parser, 'description') and parser.description:
                                description = parser.description
                                break
                        except:
                            continue
            
            return description or "No description available"
            
        except Exception as e:
            return f"Failed to load: {e}"
    
    def load_cli_module(self, cli_name):
        """Load and return a specific CLI module"""
        if cli_name not in self.discovered_clis:
            available = ', '.join(sorted(self.discovered_clis.keys()))
            print(f"❌ CLI module '{cli_name}' not found")
            print(f"Available: {available}")
            return None
        
        cli_info = self.discovered_clis[cli_name]
        
        try:
            module = importlib.import_module(cli_info['import_path'])
            
            if hasattr(module, 'main'):
                return module.main
            elif hasattr(module, 'CLI'):
                return module.CLI
            else:
                for name, obj in inspect.getmembers(module):
                    if (inspect.isfunction(obj) and 
                        name in ['cli', 'run', 'execute'] and 
                        not name.startswith('_')):
                        return obj
                
                print(f"❌ No entry point found in {cli_name}")
                return None
                
        except ImportError as e:
            print(f"❌ Failed to import {cli_name}: {e}")
            return None
    
    def list_available_clis(self):
        """List all available CLI modules with dynamic descriptions"""
        if not self.discovered_clis:
            print("No CLI modules found")
            return
        
        print("📋 Available CLI Modules:")
        print("=" * 60)
        
        for cli_name in sorted(self.discovered_clis.keys()):
            description = self._get_cli_description(cli_name)
            print(f"  {cli_name:15} - {description}")
        
        print(f"\n💡 Usage: tmcli <module_name> [args...]")
    
    def run_cli(self, cli_name, args=None):
        """Run a specific CLI module"""
        if args is None:
            args = []
        
        cli_func = self.load_cli_module(cli_name)
        if not cli_func:
            return 1
        
        try:
            original_argv = sys.argv[:]
            sys.argv = [f"{cli_name}_cli.py"] + args
            
            result = cli_func()
            sys.argv = original_argv
            
            return result if result is not None else 0
            
        except SystemExit as e:
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
  tmcli list                    # List available CLI modules
  tmcli menu status             # Run menu CLI with 'status' command
  tmcli firewall list --all     # Run firewall CLI with arguments
        """
    )
    
    # Discover CLI modules silently
    loader.discover_cli_modules(verbose=False)
    
    subparsers = parser.add_subparsers(dest='cli_module', help='Available CLI modules')
    
    # Add 'list' command
    subparsers.add_parser('list', help='List all available CLI modules')
    
    # Add 'debug' command for verbose discovery
    subparsers.add_parser('debug', help='Show detailed module discovery info')
    
    # Add discovered CLI modules as subcommands
    for cli_name in loader.discovered_clis.keys():
        description = loader._get_cli_description(cli_name)
        cli_parser = subparsers.add_parser(
            cli_name, 
            help=description,
            add_help=False
        )
        cli_parser.add_argument('cli_args', nargs='*', help='Arguments for the CLI module')
    
    return parser


def main():
    """Main entry point for master CLI"""
    loader = CLILoader()
    parser = create_dynamic_parser(loader)
    
    if len(sys.argv) == 1:
        loader.list_available_clis()
        return 0
    
    args = parser.parse_args()
    
    if not args.cli_module:
        parser.print_help()
        return 1
    
    if args.cli_module == 'list':
        loader.list_available_clis()
        return 0
    
    if args.cli_module == 'debug':
        print("🔧 Debug mode - verbose discovery:")
        loader.discover_cli_modules(verbose=True)
        return 0
    
    cli_args = getattr(args, 'cli_args', [])
    return loader.run_cli(args.cli_module, cli_args)


if __name__ == '__main__':
    sys.exit(main())