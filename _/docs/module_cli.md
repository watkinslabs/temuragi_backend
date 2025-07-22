# BaseCLI Extension Technical Specification

## Overview

The `BaseCLI` class provides a standardized foundation for creating command-line interfaces in the application. It handles database connections, logging, output formatting, and common CLI patterns.

## Quick Start

```python
#!/usr/bin/env python3
"""
Your CLI Tool
Description of what your CLI does
"""

import argparse
import sys
from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Brief description for auto-discovery"

class YourCLI(BaseCLI):  # MANDATORY: Must extend BaseCLI
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        super().__init__(
            name="your_cli_name",
            log_file="logs/your_cli.log", 
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )
        
        # Load your models
        self.your_model = self.get_model('YourModel')
        if not self.your_model:
            raise Exception("YourModel not found in registry")

    def your_operation(self, param1, param2=None):
        """Your CLI operation"""
        self.log_info(f"Starting operation: {param1}")
        
        try:
            # Your business logic here
            result = self.session.query(self.your_model).filter(...).all()
            
            # Output results - ALWAYS show full UUIDs
            if not result:
                self.output_info("No records found")
                return 0
                
            headers = ['UUID', 'Name', 'Status']  # UUID column first
            rows = [[str(r.uuid), r.name, r.status] for r in result]  # Full UUID
            self.output_table(rows, headers=headers)
            
            return 0
            
        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error in operation: {e}")
            self.output_error(f"Operation failed: {e}")
            return 1

def main():
    parser = argparse.ArgumentParser(description='Your CLI Tool')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--no-icons', action='store_true')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe'])
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Add your commands
    op_parser = subparsers.add_parser('operation', help='Do something')
    op_parser.add_argument('param1', help='Required parameter')
    op_parser.add_argument('--param2', help='Optional parameter')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    cli = YourCLI(args.verbose, not args.no_icons, args.table_format)
    
    try:
        if args.command == 'operation':
            return cli.your_operation(args.param1, args.param2)
    finally:
        cli.close()

if __name__ == '__main__':
    sys.exit(main())
```

## BaseCLI Constructor Parameters

```python
def __init__(self, name="cli", log_level=None, log_file=None, connect_db=True, 
             verbose=False, show_icons=True, table_format=None, console_logging=False):
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | "cli" | CLI instance name (used in logging) |
| `log_level` | int | `config.LOG_LEVEL` | Override logging level |
| `log_file` | str | `logs/{name}_cli.log` | Log file path |
| `connect_db` | bool | True | Whether to establish database connection |
| `verbose` | bool | False | Enable debug-level logging |
| `show_icons` | bool | True | Show icons in output messages |
| `table_format` | str | `config.CLI_TABLE_FORMAT` | Table format for tabulate |
| `console_logging` | bool | False | Also log to console |

## Available Methods

### Database Operations

```python
# Get models from registry
self.your_model = self.get_model('YourModel')

# Session is available as self.session
users = self.session.query(self.user_model).all()

# Validate session is working
if not self.validate_session():
    return 1
```

### Logging Methods

```python
self.log_debug("Debug message")
self.log_info("Info message") 
self.log_warning("Warning message")
self.log_error("Error message")
self.log_critical("Critical message")

# Operation logging
self.log_operation_start("Creating user", "username: john")
self.log_operation_end("Creating user", success=True)

# Execute with comprehensive logging
result = self.execute_with_logging("operation_name", function, *args, **kwargs)
```

### Output Methods

```python
# Basic output with optional icons
self.output_success("Operation completed")
self.output_error("Something went wrong")
self.output_warning("Be careful")
self.output_info("FYI message")
self.output_debug("Debug info")  # Only shows if verbose=True

# Table output
headers = ['ID', 'Name', 'Status']
rows = [['1', 'John', 'Active'], ['2', 'Jane', 'Inactive']]
self.output_table(rows, headers=headers)

# Custom table format
self.output_table(rows, headers=headers, table_format='grid')
```

### Transaction Patterns

```python
def create_record(self, data):
    try:
        new_record = self.your_model(**data)
        self.session.add(new_record)
        self.session.commit()
        
        # MANDATORY: Always log and display the new UUID
        self.log_info(f"Record created: {new_record.name} (UUID: {new_record.uuid})")
        self.output_success(f"Record created: {new_record.name}")
        self.output_info(f"UUID: {new_record.uuid}")  # REQUIRED
        return 0
        
    except Exception as e:
        self.session.rollback()
        self.log_error(f"Error creating record: {e}")
        self.output_error(f"Failed to create record: {e}")
        return 1
```

## File Naming and Location

- **File name**: `{feature}_cli.py` (e.g., `user_cli.py`, `role_cli.py`)
- **Location**: Place in appropriate module directory
- **Auto-discovery**: The master CLI (`tmcli`) automatically discovers all `*_cli.py` files

## Standard CLI Patterns

### Return Codes
- `0`: Success
- `1`: Error/failure

### Common Arguments
```python
parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst'], 
                   help='Override table format')
```

### Standard Commands
- `list`: List records with optional filtering
- `add`: Create new records
- `delete`: Delete records (soft delete by default, `--hard` for permanent)
- `update`: Modify existing records
- `show`: Display detailed record information

### CLI Discovery Constant
```python
CLI_DESCRIPTION = "Brief description of what this CLI does"
```

## Error Handling Best Practices

```python
def your_operation(self, param):
    self.log_info(f"Starting operation with param: {param}")
    
    try:
        # Validate inputs
        if not param:
            self.log_warning("Missing required parameter")
            self.output_error("Parameter is required")
            return 1
            
        # Check if record exists
        record = self.session.query(self.your_model).filter(...).first()
        if not record:
            self.log_warning(f"Record not found: {param}")
            self.output_error(f"Record not found: {param}")
            return 1
            
        # Perform operation
        # ...
        
        self.log_info("Operation completed successfully")
        self.output_success("Operation completed")
        return 0
        
    except Exception as e:
        self.session.rollback()
        self.log_error(f"Unexpected error in operation: {e}")
        self.output_error(f"Operation failed: {e}")
        return 1
```

## Testing Your CLI

```bash
# Test basic functionality
tmcli your_cli_name list

# Test with verbose logging
tmcli your_cli_name --verbose operation param1

# Test table formats
tmcli your_cli_name --table-format grid list

# Test error handling
tmcli your_cli_name operation invalid_param
```

## Complete Example Structure

```
app/
├── your_module/
│   ├── __init__.py
│   ├── your_model.py
│   └── your_cli.py          # Your CLI implementation
├── base_cli.py              # Base class (don't modify)
└── cli.py                   # Master CLI (don't modify)
```

## Critical Requirements

**MANDATORY: These requirements must be followed for all CLI implementations:**

1. **Always extend from `app.base_cli.BaseCLI`** - Never create standalone CLI classes
2. **When adding any object, always return the new UUID** - Display it immediately after creation
3. **Always display UUIDs as full strings** - Never truncate or abbreviate UUIDs in any output

## UUID Handling Examples

### Creating Records - REQUIRED Pattern
```python
def add_record(self, name, description):
    try:
        new_record = self.your_model(name=name, description=description)
        self.session.add(new_record)
        self.session.commit()
        
        # REQUIRED: Always log and display the new UUID
        self.log_info(f"Record created: {name} (UUID: {new_record.uuid})")
        self.output_success(f"Record created: {name}")
        self.output_info(f"UUID: {new_record.uuid}")  # MANDATORY
        return 0
    except Exception as e:
        self.session.rollback()
        self.output_error(f"Failed to create record: {e}")
        return 1
```

### Displaying UUIDs - REQUIRED Pattern
```python
# CORRECT: Full UUID display
headers = ['UUID', 'Name', 'Status']
rows = [
    [str(record.uuid), record.name, record.status]  # Full UUID string
]

# WRONG: Never truncate UUIDs
rows = [
    [str(record.uuid)[:8] + '...', record.name, record.status]  # DON'T DO THIS
]
```

## Notes

- Always call `self.close()` in the `finally` block to clean up database sessions
- Use `snake_case` for all variables and function names
- **CRITICAL**: Display full UUIDs in output (never truncate)
- **CRITICAL**: Return UUIDs when creating new records
- **CRITICAL**: Always extend from `app.base_cli.BaseCLI`
- Follow the logging patterns for audit trails
- Handle database transactions properly with rollback on errors