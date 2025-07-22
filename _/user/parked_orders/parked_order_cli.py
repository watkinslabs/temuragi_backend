#!/usr/bin/env python3
"""
Parked Order CLI - Manage parked orders and parts procurement
Handles parked order operations through the remote API
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
CLI_DESCRIPTION = "Parked order management - retrieve and process parts procurement orders"


class ParkedOrderCLI(BaseCLI):
    """
    Parked Order CLI using the hybrid BaseCLI with remote backend
    All operations go through the ParkedOrder model's process method
    """
    
    def __init__(self, **kwargs):
        """Initialize Parked Order CLI with remote backend"""
        # Force remote backend and set name
        kwargs['backend_type'] = 'remote'
        kwargs.setdefault('name', 'parked')
        
        super().__init__(**kwargs)
        
        # Parked order-specific configuration
        self.model_name = 'ParkedOrder'  # Must match the handler registration
    
    def get_parked_order(self, pr_repair_order_id: int, pt_order_id: str = None, 
                        company: str = None, output_file: str = None, show: bool = False):
        """Get parked order details from API and save to file"""
        
        self.output_info(f"Getting parked order RO={pr_repair_order_id}...")
        
        # Build request data
        request_data = {
            'pr_repair_order_id': pr_repair_order_id
        }
        
        
        # Execute retrieval through the model's get method
        result = self.execute_operation(self.model_name, 'get', request_data)
        
        if not result:
            self.output_error(f"Failed to retrieve parked order")
            return False
        
        self.output_success(f"Successfully retrieved parked order!")
        
        # Add company to result for reference if provided
        if company:
            result['company'] = company
        
        # Display summary
        self._display_order_summary(result)
        
        # Determine output file
        if not output_file:
            pt_id = result.get('order_info', {}).get('pt_order_id', 'UNKNOWN')
            company_str = f"_{company}" if company else ""
            output_file = f"PARKED_{pr_repair_order_id}_{pt_id}{company_str}.yaml"
        
        # Save the complete result
        with open(output_file, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False)
        
        self.output_success(f"Parked order saved to: {output_file}")
        
        # Show YAML if requested
        if show:
            self.output_info("\nYAML Content:")
            self.output(yaml.dump(result, default_flow_style=False, sort_keys=False))
        
        return True
    
    def list_parked_orders(self, company: str, status: str = None, days: int = 30):
        """List parked orders"""
        
        self.output_info(f"Listing parked orders...")
        
        # Build filter criteria
        filters = {}
        if status:
            filters['status'] = status.upper()
        
        # Calculate date range if days specified
        if days:
            from datetime import datetime, timedelta
            date_to = datetime.now().date()
            date_from = date_to - timedelta(days=days)
            filters['date_from'] = date_from.isoformat()
            filters['date_to'] = date_to.isoformat()
        
        # Execute list operation
        result = self.execute_operation(self.model_name, 'list', {
            'start': 0,
            'length': 100,  # Get up to 100 records
            'filters': filters
        })
        
        if not result or 'data' not in result:
            self.output_error(f"Failed to list parked orders")
            return False
        
        orders = result.get('data', [])
        if not orders:
            self.output_info("No parked orders found")
            return True
        
        # Display orders in table format
        self.output_info(f"\nFound {len(orders)} parked orders:")
        
        table_data = []
        for order in orders:
            table_data.append([
                order.get('pr_repair_order_id', ''),
                order.get('pt_order_id', ''),
                order.get('status', 'UNKNOWN'),
                order.get('created_at', '')[:10] if order.get('created_at') else '',  # Just date
                f"${order.get('total', 0):.2f}" if order.get('total') else 'N/A',
                order.get('part_count', 0),
                order.get('customer_code', '')
            ])
        
        self.output_table(table_data, 
                         headers=['RO ID', 'PT Order', 'Status', 'Created', 'Total', 'Parts', 'Customer'])
        
        return True
    
    def create_po_for_part(self, pr_repair_order_id: int, part_line: int, 
                          vendor_code: str, quantity: int, company: str,
                          dry_run: bool = False):
        """Create a purchase order for a specific part"""
        
        self.output_info(f"Creating PO for RO={pr_repair_order_id}, Line={part_line}")
        self.output_info(f"  Vendor: {vendor_code}")
        self.output_info(f"  Quantity: {quantity}")
        
        if dry_run:
            self.output_warning("Dry run - would create PO with above details")
            return True
        
        # Execute PO creation through the model's process method
        result = self.execute_operation(self.model_name, 'process', {
            'action': 'create_po',
            'pr_repair_order_id': pr_repair_order_id,
            'part_line': part_line,
            'vendor_code': vendor_code,
            'quantity': quantity
        })
        
        if result.get('success'):
            po_number = result.get('po_number')
            self.output_success(f"Successfully created PO: {po_number}")
            return True
        else:
            self.output_error(f"Failed to create PO: {result.get('message', 'Unknown error')}")
            return False
    
    def execute_yaml_operation(self, yaml_file: str, dry_run: bool = False):
        """Execute parked order operation from YAML file"""
        
        # Load YAML
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            self.output_error(f"File not found: {yaml_file}")
            return False
        except yaml.YAMLError as e:
            self.output_error(f"Invalid YAML file: {e}")
            return False
        
        if not data:
            self.output_error("Empty YAML file")
            return False
        
        # Ensure model is ParkedOrder
        if data.get('model') != 'ParkedOrder':
            data['model'] = 'ParkedOrder'
        
        # Validate operation
        if 'operation' not in data:
            self.output_error("Missing 'operation' field in YAML")
            return False
        
        operation = data['operation']
        
        # Show what we're doing
        self.output_info(f"Operation: {operation}")
        self.output_info(f"Model: {data['model']}")
        
        if dry_run:
            self.output_warning("Dry run - would send:")
            self.output(json.dumps(data, indent=2, default=str))
            return True
        
        # Execute operation
        self.output_info("Executing...")
        
        result = super().execute_operation(
            model=data['model'],
            operation=data['operation'],
            data=data.get('data')
        )
        
        if result.get('success'):
            self.output_success("Operation completed successfully!")
            
            # Handle different operation results
            if 'message' in result:
                self.output_info(result['message'])
            if 'data' in result:
                self.output(json.dumps(result['data'], indent=2, default=str))
            
            return True
        else:
            self.output_error(f"Operation failed: {result.get('error', 'Unknown error')}")
            if result.get('details'):
                self.output_debug(f"Details: {json.dumps(result['details'], indent=2)}")
            return False
    
    def _display_order_summary(self, result: Dict):
        """Display parked order summary"""
        order_info = result.get('order_info', {})
        customer = result.get('customer', {})
        requester = result.get('requester', {})
        warehouse = result.get('closest_warehouse', {})
        summary = result.get('order_summary', {})
        from pprint import pprint

        


        self.output_info(f"\nParked Order Summary:")
        
        # Order info
        self.output_info("\nOrder Information:")
        order_data = [
            ['PT Order ID', order_info.get('pt_order_id', 'N/A')],
            ['RO ID', order_info.get('pr_repair_order_id', 'N/A')],
            ['Status', order_info.get('status', 'UNKNOWN')],
            ['Created', order_info.get('created_at', 'N/A')],
            ['Total', f"${order_info.get('total', 0):.2f}"]
        ]
        for label, value in order_data:
            self.output(f"  {label}: {value}")
        
        # Customer info
        if customer:
            self.output_info("\nCustomer (Ship To):")
            self.output(f"  Name: {customer.get('name', 'N/A')}")
            self.output(f"  Address: {customer.get('address_1', 'N/A')}")
            if customer.get('address_2'):
                self.output(f"           {customer['address_2']}")
            self.output(f"  City/State/Zip: {customer.get('city', '')}, {customer.get('state', '')} {customer.get('zip', '')}")
            if customer.get('phone'):
                self.output(f"  Phone: {customer['phone']}")
        
        # Requester info
        if requester:
            self.output_info("\nRequester:")
            self.output(f"  Name: {requester.get('name', 'N/A')}")
            if requester.get('email'):
                self.output(f"  Email: {requester['email']}")
            if requester.get('phone'):
                self.output(f"  Phone: {requester['phone']}")
        
        # Warehouse info
        if warehouse:
            self.output_info("\nAssigned Warehouse:")
            self.output(f"  Code: {warehouse.get('code', 'N/A')}")
            self.output(f"  Name: {warehouse.get('name', 'N/A')}")
            self.output(f"  Location: {warehouse.get('city', '')}, {warehouse.get('state', '')}")
        
        # Order summary
        self.output_info("\nProcurement Summary:")
        self.output(f"  Total Parts: {summary.get('total_parts', 0)}")
        self.output(f"  Fully Ordered: {summary.get('parts_fully_ordered', 0)}")
        self.output(f"  Partially Ordered: {summary.get('parts_partially_ordered', 0)}")
        self.output(f"  Not Ordered: {summary.get('parts_not_ordered', 0)}")
        self.output(f"  Total POs Created: {summary.get('total_pos_created', 0)}")
        
    # Parts details
        parts = result.get('parts', [])
        if parts:
            self.output_info("\nParts:")
            table_data = []
            for part in parts:
                
                
                # Handle description truncation
                description = part.get('description', 'N/A')
                if description and len(description) > 30:
                    description = description[:30] + '...'
                
                table_data.append([
                    part.get('line', ''),
                    part.get('part_number', ''),
                    description,
                    part.get('quantity_needed', 0),
                    part.get('quantity_ordered', 0),
                    part.get('list_price'),
                    part.get('sale_price'),
                    part.get('status', 'UNKNOWN')
                ])
            
            self.output_table(table_data,
                            headers=['Line', 'Part #', 'Description', 'Need', 'Ord', 'List',  'Sale', 'Status'])


def create_parser():
    """Create argument parser for Parked Order CLI"""
    parser = argparse.ArgumentParser(
        description='Parked Order CLI - Manage parked orders through remote API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tmcli parked get 12345                       # Get by RO ID only
  tmcli parked get 12345 PT-67890              # Get by RO ID and PT ID
  tmcli parked get 12345 PACIFIC               # Get by RO ID with company
  tmcli parked get 12345 PT-67890 PACIFIC      # Get with all parameters
  tmcli parked list CANADA --status OPEN       # List open parked orders
  tmcli parked create-po 12345 1 VEND01 5 PACIFIC  # Create PO for part
  tmcli parked execute operation.yaml          # Execute operation from YAML
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Get parked order
    get_parser = subparsers.add_parser('get', help='Get parked order details')
    get_parser.add_argument('pr_repair_order_id', type=int, help='PR repair order ID')
    get_parser.add_argument('pt_order_id', nargs='?', help='PartsTrader order ID (optional)')
    get_parser.add_argument('company', nargs='?', help='Company (PACIFIC or CANADA) - optional')
    get_parser.add_argument('-o', '--output', help='Output YAML filename')
    get_parser.add_argument('--show', action='store_true', help='Also display the YAML content')
    
    # List parked orders
    list_parser = subparsers.add_parser('list', help='List parked orders')
    list_parser.add_argument('company', help='Company (PACIFIC or CANADA)')
    list_parser.add_argument('--status', choices=['OPEN', 'PARTIAL', 'COMPLETE'],
                            help='Filter by status')
    list_parser.add_argument('--days', type=int, default=30,
                            help='Show orders from last N days (default: 30)')
    
    # Create PO for part
    po_parser = subparsers.add_parser('create-po', help='Create PO for a specific part')
    po_parser.add_argument('pr_repair_order_id', type=int, help='PR repair order ID')
    po_parser.add_argument('part_line', type=int, help='Part line number')
    po_parser.add_argument('vendor_code', help='Vendor code')
    po_parser.add_argument('quantity', type=int, help='Quantity to order')
    po_parser.add_argument('company', help='Company (PACIFIC or CANADA)')
    po_parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be done without creating PO')
    
    # Execute operation from YAML
    exec_parser = subparsers.add_parser('execute', help='Execute operation from YAML file')
    exec_parser.add_argument('yaml_file', help='YAML file containing operation')
    exec_parser.add_argument('--dry-run', action='store_true', 
                            help='Show what would be sent without executing')
    
    return parser


def main():
    """Main entry point for Parked Order CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize CLI
    try:
        cli = ParkedOrderCLI(
            verbose=args.verbose,
            console_logging=args.verbose
        )
    except Exception as e:
        print(f"Failed to initialize Parked Order CLI: {e}", file=sys.stderr)
        return 1
    
    try:
        if not args.command:
            parser.print_help()
            return 0
        
        elif args.command == 'get':
            success = cli.get_parked_order(
                pr_repair_order_id=args.pr_repair_order_id,
                pt_order_id=args.pt_order_id,
                company=args.company,
                output_file=args.output,
                show=args.show
            )
            return 0 if success else 1
        
        elif args.command == 'list':
            success = cli.list_parked_orders(
                company=args.company,
                status=args.status,
                days=args.days
            )
            return 0 if success else 1
        
        elif args.command == 'create-po':
            success = cli.create_po_for_part(
                pr_repair_order_id=args.pr_repair_order_id,
                part_line=args.part_line,
                vendor_code=args.vendor_code,
                quantity=args.quantity,
                company=args.company,
                dry_run=args.dry_run
            )
            return 0 if success else 1
        
        elif args.command == 'execute':
            success = cli.execute_yaml_operation(
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
CLI = ParkedOrderCLI

if __name__ == '__main__':
    sys.exit(main())