#!/usr/bin/env python3
"""
API Test CLI - Test Miner endpoints with tokens
"""

import argparse
import requests
import json
import sys
from tabulate import tabulate

from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Test API endpoints with authentication tokens"

class APITestCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        super().__init__(
            name="apitest",
            log_file="logs/apitest_cli.log",
            connect_db=False,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

    def test_endpoint(self, base_url, token, model, operation, data=None, id=None, csrf_token="test-token"):
        url = f"{base_url.rstrip('/')}/api/data"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        }
        payload = {'model': model, 'operation': operation}
        if id:
            payload['id'] = id
        if data:
            payload['data'] = data

        self.log_info(f"{operation.upper()} {model}")
        self.output_info(f"POST {url}")
        self.output_info(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            self.output_info(f"Status: {res.status_code}")
            try:
                parsed = res.json()
                print(json.dumps(parsed, indent=2))
            except:
                self.output_info(res.text)
                return False, None
            if res.status_code in (200, 201):
                return True, parsed
            return False, None
        except requests.exceptions.RequestException as e:
            self.output_error(f"Request failed: {e}")
            return False, None

    def run_full_test(self, base_url, token, model, test_data, csrf_token="test-token"):
        results = {}
        id = None

        self.output_info("=== CREATE ===")
        ok, res = self.test_endpoint(base_url, token, model, "create", data=test_data, csrf_token=csrf_token)
        results["create"] = "PASS" if ok else "FAIL"
        id = res.get("id") or res.get("data", {}).get("id") if res else None

        if not id:
            self.output_error("No UUID returned; cannot run remaining tests.")
            self.output_table([[k.upper(), v] for k, v in results.items()], headers=["Operation", "Result"])
            return results

        self.output_info("=== READ ===")
        ok, _ = self.test_endpoint(base_url, token, model, "read", id=id, csrf_token=csrf_token)
        results["read"] = "PASS" if ok else "FAIL"

        self.output_info("=== UPDATE ===")
        update_data = {"name": "Updated Name"}
        ok, _ = self.test_endpoint(base_url, token, model, "update", id=id, data=update_data, csrf_token=csrf_token)
        results["update"] = "PASS" if ok else "FAIL"

        self.output_info("=== DELETE ===")
        ok, _ = self.test_endpoint(base_url, token, model, "delete", id=id, csrf_token=csrf_token)
        results["delete"] = "PASS" if ok else "FAIL"

        self.output_info("=== RESULTS ===")
        self.output_table([[k.upper(), v] for k, v in results.items()], headers=["Operation", "Result"])
        return results

    def validate_token(self, base_url, token):
        url = f"{base_url.rstrip('/')}/api/data"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'NoModel',
            'operation': 'read',
            'id': '00000000-0000-0000-0000-000000000000'
        }

        self.output_info("Validating token...")
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 401:
                self.output_error("Token invalid or expired")
                return False
            elif res.status_code == 404:
                self.output_success("Token valid (model not found as expected)")
                return True
            self.output_success(f"Token valid (status {res.status_code})")
            return True
        except requests.exceptions.RequestException as e:
            self.output_error(f"Connection failed: {e}")
            return False


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='API Test CLI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons')
    parser.add_argument('--base-url', default='http://localhost:5000', help='Base URL for API')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Test endpoint command
    test_parser = subparsers.add_parser('test', help='Test specific endpoint')
    test_parser.add_argument('token', help='Authentication token')
    test_parser.add_argument('model', help='Model name')
    test_parser.add_argument('operation', choices=['create', 'read', 'update', 'delete'])
    test_parser.add_argument('--id', help='Record UUID (for read/update/delete)')
    test_parser.add_argument('--data', help='JSON data (for create/update)')
    
    # Validate token command
    validate_parser = subparsers.add_parser('validate', help='Validate token')
    validate_parser.add_argument('token', help='Authentication token')
    
    # Full test command
    full_parser = subparsers.add_parser('full-test', help='Run full CRUD test')
    full_parser.add_argument('token', help='Authentication token')
    full_parser.add_argument('model', help='Model name')
    full_parser.add_argument('--data', help='JSON test data for create', default='{"name": "Test Record"}')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = APITestCLI(
        verbose=args.verbose,
        show_icons=not args.no_icons
    )
    
    try:
        if args.command == 'test':
            data = json.loads(args.data) if args.data else None
            success = cli.test_endpoint(args.base_url, args.token, args.model, args.operation, data, args.id)
            return 0 if success else 1
            
        elif args.command == 'validate':
            success = cli.validate_token(args.base_url, args.token)
            return 0 if success else 1
            
        elif args.command == 'full-test':
            test_data = json.loads(args.data)
            results = cli.run_full_test(args.base_url, args.token, args.model, test_data)
            # Return 0 if all tests passed
            return 0 if all(r == 'PASS' for r in results.values()) else 1
            
    except KeyboardInterrupt:
        cli.output_info("\nOperation cancelled")
        return 1
    except Exception as e:
        cli.output_error(f"Error: {e}")
        return 1
    finally:
        cli.close()


if __name__ == '__main__':
    sys.exit(main())