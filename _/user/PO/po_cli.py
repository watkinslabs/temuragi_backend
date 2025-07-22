#!/usr/bin/env python3
"""
PO CLI - Purchase Order management via API
Handles PO operations using the PurchaseOrder model through the remote API
"""

import argparse
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from tabulate import tabulate

from app.base.cli import BaseCLI

# Module description for tmcli discovery
CLI_DESCRIPTION = "Purchase Order management - retrieve and manage POs"


class POCLI(BaseCLI):
    """
    Purchase Order CLI using the hybrid BaseCLI with remote backend
    All PO operations go through the PurchaseOrder model's process method
    """
    
    def __init__(self, **kwargs):
        """Initialize PO CLI with remote backend"""
        # Force remote backend and set name
        kwargs['backend_type'] = 'remote'
        kwargs.setdefault('name', 'po')
        
        super().__init__(**kwargs)
        
        # PO-specific configuration
        self.model_name = 'PurchaseOrder'
    
    def get_po(self, po_number: str, company: str, output_file: str = None, 
               show: bool = False, format: str = 'raw'):
        """Get PO from API and save to file"""
        
        # Validate company
        company = company.upper()
        if company not in ['PACIFIC', 'CANADA']:
            self.output_error(f"Company must be PACIFIC or CANADA (got: {company})")
            return False
        
        self.output_info(f"Getting PO {po_number} from {company}...")
        
        # Determine operation based on format
        if format == 'details':
            operation_type = 'get_po_details'
        else:  # raw format - gets everything including source info
            # Since get_historical_po just calls get_po, we should use a direct operation
            # that returns the raw data with source tracking
            operation_type = 'get_po_details'  # This includes source_info in the response
        
        # Execute PO retrieval through the model's process method
        result = self.execute_operation(self.model_name, 'process', {
            'operation': operation_type,
            'id': po_number,
            'company': company
        })
        
        if not result.get('success'):
            self.output_error(f"Failed to retrieve PO: {result.get('error', 'Unknown error')}")
            if result.get('details'):
                self.output_debug(f"Details: {json.dumps(result['details'], indent=2)}")
            return False
        
        self.output_success(f"Successfully retrieved PO!")
        
        # Check if PO is partially received
        source_info = result.get('source_info', {})
        if source_info.get('is_partially_received'):
            self.output_warning(f"PO is partially received:")
            self.output_warning(f"  - Active lines: {source_info.get('active_line_count', 0)}")
            self.output_warning(f"  - Historical lines: {source_info.get('historical_line_count', 0)}")
        
        # Determine output file
        if not output_file:
            output_file = f"PO_{po_number}_{company}.yaml"
        
        # Save the complete result with source tracking
        with open(output_file, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False)
        
        self.output_success(f"PO saved to: {output_file}")
        
        # Display summary
        self._display_po_summary(result)
        
        # Show YAML if requested
        if show:
            self.output_info("\nYAML Content:")
            self.output(yaml.dump(result, default_flow_style=False, sort_keys=False))
        
        return True
    
    def execute_po_operation(self, yaml_file: str, dry_run: bool = False):
        """Execute PO operation from YAML file"""
        
        # Load YAML
        try:
            with open(yaml_file, 'r') as f:
                po_data = yaml.safe_load(f)
        except FileNotFoundError:
            self.output_error(f"File not found: {yaml_file}")
            return False
        except yaml.YAMLError as e:
            self.output_error(f"Invalid YAML file: {e}")
            return False
        
        if not po_data:
            self.output_error("Empty YAML file")
            return False
        
        # Ensure model is PurchaseOrder
        if po_data.get('model') != 'PurchaseOrder':
            po_data['model'] = 'PurchaseOrder'
        
        # Validate operation
        if 'operation' not in po_data:
            self.output_error("Missing 'operation' field in YAML")
            return False
        
        operation = po_data['operation']
        
        # Show what we're doing
        self.output_info(f"Operation: {operation}")
        self.output_info(f"Model: {po_data['model']}")
        
        if dry_run:
            self.output_warning("Dry run - would send:")
            self.output(json.dumps(po_data, indent=2, default=str))
            return True
        
        # Execute operation
        self.output_info("Executing...")
        
        result = self.execute_operation(
            model=po_data['model'],
            operation=po_data['operation'],
            data=po_data.get('data')
        )
        
        if result.get('success'):
            self.output_success("Operation completed successfully!")
            
            # Handle different operation results
            if operation == 'create' and 'po_number' in result:
                self.output_info(f"PO Number: {result['po_number']}")
                self.output_info(f"Total: ${result.get('total', 0):.2f}")
                
            elif operation == 'process':
                # Handle process sub-operations
                sub_op = po_data.get('data', {}).get('operation')
                if sub_op == 'get_po_details' and 'header' in result:
                    self._display_po_details(result)
                else:
                    # Generic result display
                    self.output(json.dumps(result, indent=2, default=str))
                    
            elif operation == 'metadata' and 'metadata' in result:
                self.output_info("PurchaseOrder Model Metadata:")
                self.output(json.dumps(result['metadata'], indent=2))
                
            else:
                # Generic result display
                if 'data' in result:
                    self.output(json.dumps(result['data'], indent=2, default=str))
                elif 'message' in result:
                    self.output_info(result['message'])
            
            return True
        else:
            self.output_error(f"Operation failed: {result.get('error', 'Unknown error')}")
            if result.get('details'):
                self.output_debug(f"Details: {json.dumps(result['details'], indent=2)}")
            if result.get('errors'):
                self.output_error("Errors:")
                for error in result['errors']:
                    self.output_error(f"  - {error}")
            return False
    
    def _display_po_summary(self, result: Dict):
        """Display PO summary with source information"""
        header = result.get('header', {})
        source_info = result.get('source_info', {})
        
        self.output_info(f"\nPO Summary:")
        summary_data = [
            ['Company', result.get('company', 'Unknown')],
            ['PO Number', result.get('po_number', 'Unknown')],
            ['Vendor', f"{header.get('vendor_name', 'Unknown')} ({header.get('vendor_code', '')})"],
            ['Location', header.get('location', 'Unknown')],
            ['Total', f"${header.get('total', 0):.2f}"],
            ['Order Date', header.get('order_date', 'Unknown')],
            ['Printed', 'Yes' if header.get('printed') else 'No'],
        ]
        
        # Add source information
        self.output_info("\nSource Information:")
        source_data = [
            ['Header Status', 'Active' if source_info.get('is_active') else 'Historical'],
            ['Total Lines', result.get('line_count', 0)],
            ['Active Lines', source_info.get('active_line_count', 0)],
            ['Historical Lines', source_info.get('historical_line_count', 0)],
            ['Partially Received', 'Yes' if source_info.get('is_partially_received') else 'No']
        ]
        
        for label, value in summary_data:
            self.output(f"  {label}: {value}")
        
        self.output("")  # Blank line
        
        for label, value in source_data:
            self.output(f"  {label}: {value}")
    
    def _display_po_details(self, result: Dict):
        """Display detailed PO information"""
        header = result.get('header', {})
        
        self.output_info(f"\nPO: {result.get('po_number', 'Unknown')}")
        self.output_info(f"Company: {result.get('company', 'Unknown')}")
        self.output_info(f"Vendor: {header.get('vendor_name', '')} ({header.get('vendor_code', '')})")
        self.output_info(f"Location: {header.get('location', '')}")
        self.output_info(f"Total: ${header.get('total', 0):.2f}")
        
        if result.get('lines'):
            self.output_info("\nLine Items:")
            table_data = []
            for line in result['lines']:
                # Show all lines with their source
                if line.get('type') == 'R':  # Regular inventory items
                    source = line.get('_source', 'unknown')
                    desc = line.get('description', '')
                    table_data.append([
                        line.get('part', ''),
                        desc[:25] + '...' if len(desc) > 25 else desc,
                        line.get('quantity', 0),
                        f"${line.get('price', 0):.2f}",
                        f"${line.get('extended', 0):.2f}",
                        source.upper()
                    ])
            
            if table_data:
                self.output_table(table_data, 
                                headers=['Part', 'Description', 'Qty', 'Price', 'Extended', 'Source'])


def create_parser():
    """Create argument parser for PO CLI"""
    parser = argparse.ArgumentParser(
        description='Purchase Order CLI - Manage POs through remote API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tmcli po get 12345 PACIFIC               # Get PO with source tracking
  tmcli po get 12345 CANADA -o mypo.yaml   # Get PO and save to specific file
  tmcli po get 12345 PACIFIC --show        # Get PO and display content
  tmcli po execute purchase_order.yaml      # Execute PO operation from YAML
  tmcli po execute po.yaml --dry-run       # Preview what would be sent
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Get PO (replaces both pull and history)
    get_parser = subparsers.add_parser('get', help='Get PO from API with full source tracking')
    get_parser.add_argument('po_number', help='PO number to retrieve')
    get_parser.add_argument('company', help='Company (PACIFIC or CANADA)')
    get_parser.add_argument('-o', '--output', help='Output YAML filename')
    get_parser.add_argument('--show', action='store_true', help='Also display the YAML content')
    get_parser.add_argument('--format', choices=['raw', 'details'], default='raw',
                           help='Output format (raw includes all source info)')
    
    # Execute PO operation from YAML
    exec_parser = subparsers.add_parser('execute', help='Execute PO operation from YAML file')
    exec_parser.add_argument('yaml_file', help='YAML file containing PO operation')
    exec_parser.add_argument('--dry-run', action='store_true', 
                            help='Show what would be sent without executing')
    
    return parser


def main():
    """Main entry point for PO CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize CLI
    try:
        cli = POCLI(
            verbose=args.verbose,
            console_logging=args.verbose
        )
    except Exception as e:
        print(f"Failed to initialize PO CLI: {e}", file=sys.stderr)
        return 1
    
    # The hybrid BaseCLI will automatically handle authentication
    # using stored tokens. If not authenticated, it will fail
    # with appropriate error messages.
    
    try:
        if not args.command:
            parser.print_help()
            return 0
        
        elif args.command == 'get':
            success = cli.get_po(
                po_number=args.po_number,
                company=args.company,
                output_file=args.output,
                show=args.show,
                format=args.format
            )
            return 0 if success else 1
        
        elif args.command == 'execute':
            success = cli.execute_po_operation(
                yaml_file=args.yaml_file,
                dry_run=args.dry_run
            )
            return 0 if success else 1
        
    except KeyboardInterrupt:
        cli.output_warning("\nOperation cancelled by user")
        return 1
    except Exception as e:
        cli.output_error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        cli.close()


# For tmcli discovery
CLI = POCLI

if __name__ == '__main__':
    sys.exit(main())