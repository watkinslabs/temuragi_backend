def close(self):
        """Clean up resources"""
        # Check if we have the full BaseCLI functionality
        if hasattr(super(), 'close') and self._backend_initialized:
            super().close()
        else:
            # Basic cleanup
            self.log_info("Closing CLI instance")
            if hasattr(self, 'backend') and self.backend:
                try:
                    self.backend.close()
                except Exception:
                    pass#!/usr/bin/env python3
"""
tmcli - Temuragi CLI Entry Point
Automatically discovers and loads all *_cli.py modules from the project
Also provides base authentication commands for remote backend
Usage: tmcli <module_name> [args...]
"""

import os
import sys
import importlib
import inspect
import argparse
import getpass
from pathlib import Path
from app.base.cli import BaseCLI

class CLIDiscovery:
    def __init__(self, base_path=None, logger=None):
        """Initialize CLI discovery with search rooted at ./app"""
        if base_path is None:
            self.base_path = Path(__file__).resolve().parent
        else:
            self.base_path = Path(base_path)

        self.discovered_clis = {}
        self.failed_modules = {}
        self.root_package = self._determine_root_package()
        self.logger = logger

    def _determine_root_package(self):
        """Determine the root package name from the current module"""
        return __package__.split('.')[0] if __package__ else 'app'

    def _log(self, message, level='info'):
        """Log message if logger is available"""
        if self.logger:
            if hasattr(self.logger, f'log_{level}'):
                getattr(self.logger, f'log_{level}')(message)
            else:
                getattr(self.logger, level)(message)

    def discover_cli_modules(self, verbose=False):
        """Recursively discover all *_cli.py modules"""
        self._log(f"Discovering CLI modules in {self.base_path}", 'info')
        
        if verbose:
            if hasattr(self.logger, 'output_info'):
                self.logger.output_info(f"Discovering CLI modules in {self.base_path}...")
            else:
                print(f"Discovering CLI modules in {self.base_path}...")

        for dirpath, dirnames, filenames in os.walk(self.base_path):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')
                          and d not in ['__pycache__', 'static', 'tpl']]

            cli_files = [f for f in filenames if f.endswith('_cli.py')]

            for cli_file in cli_files:
                if cli_file == "base_cli.py":
                    continue
                self._register_cli_module(dirpath, cli_file, verbose)

        if verbose and self.failed_modules:
            if hasattr(self.logger, 'output_warning'):
                self.logger.output_warning(f"Failed to load {len(self.failed_modules)} modules:")
                for name, error in self.failed_modules.items():
                    self.logger.output_error(f"  {name}: {error}")
            else:
                print(f"Failed to load {len(self.failed_modules)} modules:")
                for name, error in self.failed_modules.items():
                    print(f"  {name}: {error}")

        self._log(f"Discovery complete: {len(self.discovered_clis)} modules found, {len(self.failed_modules)} failed", 'info')
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

            self._log(f"Registered CLI module: {cli_name} -> {import_path}", 'debug')
            
            if verbose:
                if hasattr(self.logger, 'output_success'):
                    self.logger.output_success(f"{cli_name} -> {import_path}")
                else:
                    print(f"  {cli_name} -> {import_path}")

        except Exception as e:
            self.failed_modules[cli_file] = str(e)
            self._log(f"Failed to register {cli_file}: {e}", 'error')

    def get_cli_description(self, cli_name):
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
            self._log(f"Failed to get description for {cli_name}: {e}", 'warning')
            return f"Failed to load: {e}"

    def load_cli_module(self, cli_name):
        """Load and return a specific CLI module"""
        if cli_name not in self.discovered_clis:
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

                self._log(f"No entry point found in {cli_name}", 'error')
                return None

        except ImportError as e:
            self._log(f"Failed to import {cli_name}: {e}", 'error')
            return None


class TMasterCLI(BaseCLI):
    """Master CLI that discovers and executes other CLI modules"""

    def __init__(self, base_path=None, **kwargs):
        """Initialize master CLI with discovery capabilities"""
        # For the master CLI, we'll handle backend initialization more carefully
        # since some commands don't need a backend at all
        self.base_path = base_path
        self.discovery = None
        self.parser = None
        self._backend_initialized = False
        self.initialization_errors = []  # Initialize this early
        
        # Store kwargs for delayed initialization
        self._init_kwargs = kwargs.copy()
        # Remove backend_type from kwargs if present to avoid duplicate
        self._init_kwargs.pop('backend_type', None)
        
        # Initialize without backend first
        try:
            super().__init__(
                name="tmcli",
                backend_type="remote",
                **self._init_kwargs
            )
            self._backend_initialized = True
        except Exception as e:
            # If backend init fails, continue without it for non-backend commands
            self.name = "tmcli"
            self.verbose = kwargs.get('verbose', False)
            self.console_logging = kwargs.get('console_logging', False)
            self.backend = None
            self._setup_basic_logging()
            self.log_warning(f"Backend initialization failed: {e}")
            self.log_info("Some commands may not be available")
        
        self.discovery = CLIDiscovery(base_path, self)
    
    def _setup_basic_logging(self):
        """Setup basic logging when full BaseCLI init fails"""
        import logging
        self.logger = logging.getLogger(f'cli_{self.name}')
        self.logger.setLevel(logging.INFO)
        
        # Add console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Add output methods
        self.output = lambda msg, t='info': print(msg)
        self.output_info = lambda msg: print(f"ℹ {msg}")
        self.output_success = lambda msg: print(f"✓ {msg}")
        self.output_error = lambda msg: print(f"✗ {msg}")
        self.output_warning = lambda msg: print(f"⚠ {msg}")
        
    def _ensure_backend(self):
        """Ensure backend is initialized for commands that need it"""
        if self._backend_initialized:
            return True
            
        # Commands that don't need backend
        no_backend_commands = ['list', 'debug', 'configure']
        if len(sys.argv) > 1 and sys.argv[1] in no_backend_commands:
            return False
            
        self.output_error("Backend not initialized. Please run 'tmcli configure' first.")
        return False

    def discover_modules(self, verbose=False):
        """Discover available CLI modules"""
        return self.discovery.discover_cli_modules(verbose)

    def list_available_clis(self):
        """List all available CLI modules with dynamic descriptions"""
        modules = self.discover_modules()
        
        if not modules:
            self.output_warning("No CLI modules found")
            return

        self.output_info("Available CLI Modules:")
        self.output("=" * 60)

        # Add built-in commands first
        self.output_info("\nBuilt-in Commands:")
        self.output(f"  {'login':15} - Login to remote API")
        self.output(f"  {'logout':15} - Logout and clear stored credentials")
        self.output(f"  {'whoami':15} - Show current user information")
        self.output(f"  {'configure':15} - Configure API settings")
        self.output(f"  {'list':15} - List all available CLI modules")
        
        # Then show discovered modules
        self.output_info("\nDiscovered Modules:")
        for cli_name in sorted(modules.keys()):
            description = self.discovery.get_cli_description(cli_name)
            self.output(f"  {cli_name:15} - {description}")

        self.output(f"\nUsage: tmcli <command> [args...]")

    def run_cli_module(self, cli_name, args=None):
        """Run a specific CLI module"""
        if args is None:
            args = []

        cli_func = self.discovery.load_cli_module(cli_name)
        if not cli_func:
            available = ', '.join(sorted(self.discovery.discovered_clis.keys()))
            self.output_error(f"CLI module '{cli_name}' not found")
            self.output_info(f"Available: {available}")
            return 1

        try:
            original_argv = sys.argv[:]
            sys.argv = [f"{cli_name}_cli.py"] + args

            result = cli_func()
            sys.argv = original_argv

            self.log_operation_end(f"CLI module: {cli_name}", success=True)
            return result if result is not None else 0

        except SystemExit as e:
            sys.argv = original_argv
            return e.code if e.code is not None else 0
        except Exception as e:
            sys.argv = original_argv
            self.log_operation_end(f"CLI module: {cli_name}", success=False, details=str(e))
            self.output_error(f"Error running {cli_name}: {e}")
            return 1

    def handle_login(self, username=None, password=None):
        """Handle login command"""
        if not self._ensure_backend():
            return False
            
        self.output_info("Login to Remote API")
        
        # Get credentials if not provided
        if not username:
            username = input("Username: ")
        if not password:
            password = getpass.getpass("Password: ")
        
        try:
            if self.authenticate(username=username, password=password):
                self.output_success("Login successful!")
                
                # Show user info if available
                if hasattr(self.backend, 'user_id') and self.backend.user_id:
                    self.output_info(f"User ID: {self.backend.user_id}")
                
                return True
            else:
                self.output_error("Login failed!")
                return False
                
        except Exception as e:
            self.output_error(f"Login error: {e}")
            return False

    def handle_logout(self):
        """Handle logout command"""
        if not self._ensure_backend():
            return False
            
        try:
            if hasattr(self, 'logout') and callable(self.logout):
                if self.logout():
                    self.output_success("Logged out successfully")
                    return True
                else:
                    self.output_error("Logout failed")
                    return False
            else:
                self.output_warning("Logout not available")
                return False
        except Exception as e:
            self.output_error(f"Logout error: {e}")
            return False

    def handle_whoami(self):
        """Show current user information"""
        if not self._ensure_backend():
            return False
            
        if not hasattr(self, 'is_authenticated') or not self.is_authenticated():
            self.output_warning("Not logged in")
            return True
        
        self.output_info("Current User Information:")
        
        if hasattr(self.backend, 'user_id'):
            self.output(f"  User ID: {self.backend.user_id or 'Unknown'}")
        
        if hasattr(self.backend, 'api_token') and self.backend.api_token:
            self.output(f"  Token: ***{self.backend.api_token[-8:]}")
        
        if hasattr(self.backend, 'base_url'):
            self.output(f"  API URL: {self.backend.base_url}")
        
        return True

    def handle_configure(self):
        """Configure API settings"""
        self.output_info("API Configuration")
        self.output("=" * 40)
        
        # Load existing config if any
        config_file = Path.home() / '.config' / 'tmcli' / 'config.yaml'
        current_config = {}
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    current_config = yaml.safe_load(f) or {}
            except Exception:
                pass
        
        # Get current URL from config
        current_url = current_config.get('base_url', 'https://temuragi.watkinslabs.com')
        
        # Prompt for new URL
        url = input(f"API Base URL [{current_url}]: ").strip() or current_url
        
        # Create config directory
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        import yaml
        config = {
            'base_url': url.rstrip('/')
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        self.output_success(f"Configuration saved to {config_file}")
        self.output_info(f"API URL: {url}")
        self.output_info("\nYou may need to restart tmcli for changes to take effect.")
        
        return True

    def create_dynamic_parser(self):
        """Create argument parser with dynamic subcommands"""
        parser = argparse.ArgumentParser(
            description='Master CLI - Recursive CLI Module Loader with Authentication',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  tmcli login                   # Login to remote API
  tmcli whoami                  # Show current user
  tmcli list                    # List available CLI modules
  tmcli po pull 12345 PACIFIC   # Run po CLI with arguments
  tmcli logout                  # Logout from API
            """
        )

        # Add global log level argument
        parser.add_argument(
            '--log-level', 
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set logging level'
        )
        
        parser.add_argument(
            '--debug', '-v',
            action='store_true',
            help='Enable debug logging (same as --log-level DEBUG)'
        )

        # Discover CLI modules silently
        self.discover_modules(verbose=False)

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Add built-in commands
        # Login
        login_parser = subparsers.add_parser('login', help='Login to remote API')
        login_parser.add_argument('--username', '-u', help='Username (will prompt if not provided)')
        login_parser.add_argument('--password', '-p', help='Password (will prompt if not provided)')
        
        # Logout
        subparsers.add_parser('logout', help='Logout and clear stored credentials')
        
        # Whoami
        subparsers.add_parser('whoami', help='Show current user information')
        
        # Configure
        subparsers.add_parser('configure', help='Configure API settings')
        
        # List
        subparsers.add_parser('list', help='List all available CLI modules')

        # Debug
        subparsers.add_parser('debug', help='Show detailed module discovery info')

        # Add discovered CLI modules as subcommands
        for cli_name in self.discovery.discovered_clis.keys():
            description = self.discovery.get_cli_description(cli_name)
            cli_parser = subparsers.add_parser(
                cli_name,
                help=description,
                add_help=False
            )

        return parser

    def execute(self):
        """Execute the master CLI command"""
        # Pre-parse for log level arguments to set logging early
        debug_mode = False
        log_level_override = None
        
        # Quick scan for log level args before full parsing
        for i, arg in enumerate(sys.argv):
            if arg == '--debug' or arg == '-v':
                debug_mode = True
                break
            elif arg == '--log-level' and i + 1 < len(sys.argv):
                log_level_override = sys.argv[i + 1].upper()
                break

        # Re-setup logger if needed with new level
        if debug_mode or log_level_override:
            self._apply_log_level(debug_mode, log_level_override)

        self.parser = self.create_dynamic_parser()

        if len(sys.argv) == 1:
            self.list_available_clis()
            return 0

        args, unknown_args = self.parser.parse_known_args()

        if args.debug or args.log_level:
            self._apply_log_level(args.debug, args.log_level)

        if not args.command:
            self.parser.print_help()
            return 1

        # Handle built-in commands
        if args.command == 'login':
            username = getattr(args, 'username', None)
            password = getattr(args, 'password', None)
            return 0 if self.handle_login(username, password) else 1
            
        elif args.command == 'logout':
            return 0 if self.handle_logout() else 1
            
        elif args.command == 'whoami':
            return 0 if self.handle_whoami() else 1
            
        elif args.command == 'configure':
            return 0 if self.handle_configure() else 1
            
        elif args.command == 'list':
            self.list_available_clis()
            return 0

        elif args.command == 'debug':
            self.output_info("Debug mode - verbose discovery:")
            self.discover_modules(verbose=True)
            return 0

        # Otherwise, run the discovered CLI module
        return self.run_cli_module(args.command, unknown_args)

    def _apply_log_level(self, debug_mode, log_level_name):
        """Apply log level using BaseCLI's logging infrastructure"""
        if not hasattr(self, '_setup_logger'):
            return
            
        if debug_mode:
            # Re-setup logger with debug mode
            self._setup_logger(log_level=10)  # DEBUG level
            self.verbose = True
        elif log_level_name:
            level_map = {
                'DEBUG': 10,
                'INFO': 20,
                'WARNING': 30,
                'ERROR': 40,
                'CRITICAL': 50
            }
            if log_level_name in level_map:
                self._setup_logger(log_level=level_map[log_level_name])
                if log_level_name == 'DEBUG':
                    self.verbose = True
    
    # Add missing log methods for basic logging
    def log_info(self, msg):
        if hasattr(self, 'logger'):
            self.logger.info(msg)
    
    def log_warning(self, msg):
        if hasattr(self, 'logger'):
            self.logger.warning(msg)
    
    def log_error(self, msg):
        if hasattr(self, 'logger'):
            self.logger.error(msg)
    
    def log_operation_end(self, op, success=True, details=None):
        msg = f"Operation {op} {'succeeded' if success else 'failed'}"
        if details:
            msg += f": {details}"
        if success:
            self.log_info(msg)
        else:
            self.log_error(msg)
                    
def create_master_cli(**kwargs):
    """Factory function to create master CLI instance"""
    return TMasterCLI(**kwargs)


def main():
    """Main entry point for master CLI"""
    master_cli = create_master_cli()
    result = master_cli.execute()
    master_cli.close()
    return result

if __name__ == '__main__':
    sys.exit(main())