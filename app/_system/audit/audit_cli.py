#!/usr/bin/env python3
"""
Audit Log Analysis CLI - Monitor API usage, security events, and performance
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from tabulate import tabulate
from collections import defaultdict

from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Analyze API audit logs for security, performance, and usage monitoring"

class AuditAnalysisCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        super().__init__(
            name="audit",
            log_file="logs/audit_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        # Get required models
        self.audit_log_model = self.get_model('RbacAuditLog')
        self.user_model = self.get_model('User')

        if not self.audit_log_model:
            self.log_error("RbacAuditLog model not found in registry")
            raise Exception("RbacAuditLog model not found")

    def show_recent_activity(self, hours=24, limit=50):
        """Show recent API activity"""
        self.log_info(f"Showing recent activity for last {hours} hours")

        try:
            activities = self.audit_log_model.get_recent_activity(self.session, hours, limit)

            if not activities:
                self.output_info(f"No API activity found in last {hours} hours")
                return 0

            self.output_success(f"Recent RBAC Activity (Last {hours} hours)")

            headers = ['Time', 'User', 'Permission', 'Interface', 'Resource', 'Status', 'Duration']
            rows = []

            for activity in activities:
                user_display = 'System' if not activity.user_uuid else str(activity.user_uuid)[:8] + '...'
                time_str = activity.created_at.strftime('%H:%M:%S')
                status_icon = '✓' if activity.permission_granted else '✗'
                resource_display = f"{activity.resource_type or 'N/A'}/{activity.resource_name or 'N/A'}"

                rows.append([
                    time_str,
                    user_display,
                    activity.permission_name,
                    activity.interface_type,
                    resource_display,
                    f"{status_icon} {'GRANTED' if activity.permission_granted else 'DENIED'}",
                    f"{activity.check_duration_ms}ms" if activity.check_duration_ms else 'N/A'
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error showing recent activity: {e}")
            self.output_error(f"Error retrieving activity: {e}")
            return 1

    def show_security_alerts(self, hours=24):
        """Show security-related events"""
        self.log_info(f"Checking for security alerts in last {hours} hours")

        try:
            alerts = self.audit_log_model.get_security_alerts(self.session, hours)

            if not alerts:
                self.output_success(f"No security alerts found in last {hours} hours")
                return 0

            self.output_warning(f"Security Alerts (Last {hours} hours)")

            headers = ['Time', 'User', 'Permission', 'Interface', 'Resource', 'Reason', 'IP Address']
            rows = []

            for alert in alerts:
                user_display = 'System' if not alert.user_uuid else str(alert.user_uuid)[:8] + '...'
                time_str = alert.created_at.strftime('%m-%d %H:%M')
                resource_display = f"{alert.resource_type or 'N/A'}/{alert.resource_name or 'N/A'}"
                reason = alert.access_denied_reason or 'Permission denied'

                rows.append([
                    time_str,
                    user_display,
                    alert.permission_name,
                    alert.interface_type,
                    resource_display,
                    reason[:50] + '...' if len(reason) > 50 else reason,
                    alert.ip_address or 'N/A'
                ])

            self.output_table(rows, headers=headers)

            # Show summary
            self.output_warning(f"Total alerts: {len(alerts)}")
            return 0

        except Exception as e:
            self.log_error(f"Error checking security alerts: {e}")
            self.output_error(f"Error retrieving alerts: {e}")
            return 1

    def show_performance_stats(self, interface_type=None, hours=24):
        """Show performance statistics for permission checks"""
        self.log_info(f"Generating permission check performance stats for last {hours} hours")

        try:
            stats = self.audit_log_model.get_performance_stats(self.session, interface_type, hours)

            if not stats:
                filter_text = f" for {interface_type}" if interface_type else ""
                self.output_info(f"No performance data found{filter_text}")
                return 0

            title = f"Permission Check Performance (Last {hours} hours)"
            if interface_type:
                title += f" - {interface_type}"
            self.output_success(title)

            headers = ['Interface', 'Permission', 'Checks', 'Avg Duration (ms)', 'Max Duration (ms)', 'Granted', 'Denied']
            rows = []

            for stat in stats:
                success_rate = f"{(stat.granted / stat.total_checks * 100):.1f}%" if stat.total_checks > 0 else "0%"
                rows.append([
                    stat.interface_type,
                    stat.permission_name,
                    stat.total_checks,
                    f"{stat.avg_duration:.1f}" if stat.avg_duration else 'N/A',
                    f"{stat.max_duration}" if stat.max_duration else 'N/A',
                    f"{stat.granted} ({success_rate})",
                    stat.denied
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error generating performance stats: {e}")
            self.output_error(f"Error retrieving stats: {e}")
            return 1

    def show_user_activity(self, user_identity, days=7):
        """Show activity for a specific user"""
        self.log_info(f"Showing user activity for {user_identity}")

        try:
            # Find user
            if self.user_model:
                user = self.user_model.find_by_identity(self.session, user_identity)
                if not user:
                    self.output_error(f"User not found: {user_identity}")
                    return 1
                user_uuid = user.uuid
                user_display = f"{user.username} ({user.email})"
            else:
                # Assume user_identity is UUID
                user_uuid = user_identity
                user_display = user_identity

            # Get activity summary using the model method
            activity_summary = self.audit_log_model.get_user_permission_activity(self.session, user_uuid, days)

            if not activity_summary:
                self.output_info(f"No activity found for user {user_display}")
                return 0

            self.output_success(f"User Permission Activity - {user_display} (Last {days} days)")

            headers = ['Permission', 'Interface', 'Resource Type', 'Attempts', 'Granted', 'Denied', 'Success Rate']
            rows = []

            total_attempts = 0
            total_granted = 0
            for activity in activity_summary:
                total_attempts += activity.attempts
                total_granted += activity.granted
                success_rate = f"{(activity.granted / activity.attempts * 100):.1f}%" if activity.attempts > 0 else "0%"

                rows.append([
                    activity.permission_name,
                    activity.interface_type,
                    activity.resource_type or 'N/A',
                    activity.attempts,
                    activity.granted,
                    activity.denied,
                    success_rate
                ])

            self.output_table(rows, headers=headers)

            overall_success = f"{(total_granted / total_attempts * 100):.1f}%" if total_attempts > 0 else "0%"
            self.output_info(f"Total attempts: {total_attempts}, Overall success rate: {overall_success}")

            # Show recent detailed activity using model method
            recent_activity = self.audit_log_model.get_user_recent_activity(self.session, user_uuid, days=1, limit=10)

            if recent_activity:
                self.output_info("\nRecent Activity (Last 24 hours):")
                headers = ['Time', 'Permission', 'Interface', 'Resource', 'Status']
                rows = []

                for activity in recent_activity:
                    time_str = activity.created_at.strftime('%H:%M:%S')
                    status_icon = '✓' if activity.permission_granted else '✗'
                    resource_display = f"{activity.resource_type or 'N/A'}/{activity.resource_name or 'N/A'}"

                    rows.append([
                        time_str,
                        activity.permission_name,
                        activity.interface_type,
                        resource_display,
                        f"{status_icon} {'GRANTED' if activity.permission_granted else 'DENIED'}"
                    ])

                self.output_table(rows, headers=headers)

            return 0

        except Exception as e:
            self.log_error(f"Error showing user activity: {e}")
            self.output_error(f"Error retrieving user activity: {e}")
            return 1

    def show_permission_usage(self, days=7):
        """Show permission usage statistics"""
        self.log_info(f"Generating permission usage stats for last {days} days")

        try:
            usage_stats = self.audit_log_model.get_permission_usage_stats(self.session, days)

            if not usage_stats:
                self.output_info(f"No permission usage data found for last {days} days")
                return 0

            self.output_success(f"Permission Usage Statistics (Last {days} days)")

            headers = ['Permission', 'Interface', 'Total Checks', 'Granted', 'Denied', 'Success Rate', 'Unique Users']
            rows = []

            for stat in usage_stats:
                success_rate = f"{(stat.granted / stat.total_checks * 100):.1f}%" if stat.total_checks > 0 else "0%"

                rows.append([
                    stat.permission_name,
                    stat.interface_type,
                    stat.total_checks,
                    stat.granted,
                    stat.denied,
                    success_rate,
                    stat.unique_users
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error generating permission usage stats: {e}")
            self.output_error(f"Error retrieving usage stats: {e}")
            return 1

    def show_error_analysis(self, hours=24):
        """Analyze permission denials and their patterns"""
        self.log_info(f"Analyzing permission denials for last {hours} hours")

        try:
            denial_summary, recent_denials = self.audit_log_model.get_denial_analysis(self.session, hours)

            if not denial_summary:
                self.output_success(f"No permission denials found in last {hours} hours")
                return 0

            self.output_warning(f"Permission Denial Analysis (Last {hours} hours)")

            headers = ['Permission', 'Interface', 'Reason', 'Count']
            rows = []

            total_denials = 0
            for denial in denial_summary:
                total_denials += denial.count
                reason = denial.access_denied_reason or 'No reason provided'
                rows.append([
                    denial.permission_name,
                    denial.interface_type,
                    reason[:50] + '...' if len(reason) > 50 else reason,
                    denial.count
                ])

            self.output_table(rows, headers=headers)
            self.output_warning(f"Total denials: {total_denials}")

            # Show recent denial details
            if recent_denials:
                self.output_info("\nRecent Denial Details:")
                headers = ['Time', 'User', 'Permission', 'Interface', 'Reason']
                rows = []

                for denial in recent_denials:
                    time_str = denial.created_at.strftime('%H:%M:%S')
                    user_display = 'System' if not denial.user_uuid else str(denial.user_uuid)[:8] + '...'
                    reason = (denial.access_denied_reason or 'No reason')[:50]
                    if len(denial.access_denied_reason or '') > 50:
                        reason += '...'

                    rows.append([
                        time_str,
                        user_display,
                        denial.permission_name,
                        denial.interface_type,
                        reason
                    ])

                self.output_table(rows, headers=headers)

            return 0

        except Exception as e:
            self.log_error(f"Error analyzing denials: {e}")
            self.output_error(f"Error retrieving denial analysis: {e}")
            return 1

    def show_suspicious_activity(self, hours=24, min_denials=5):
        """Show users with suspicious activity patterns"""
        self.log_info(f"Checking for suspicious activity in last {hours} hours")

        try:
            suspicious_users = self.audit_log_model.get_suspicious_activity(self.session, hours, min_denials)

            if not suspicious_users:
                self.output_success(f"No suspicious activity detected (threshold: {min_denials} denials)")
                return 0

            self.output_warning(f"Suspicious Activity Detected (Last {hours} hours)")

            headers = ['User UUID', 'Total Denials', 'Unique Permissions', 'Unique IPs', 'Last Denial']
            rows = []

            for user_activity in suspicious_users:
                user_display = str(user_activity.user_uuid)[:8] + '...' if user_activity.user_uuid else 'System'
                last_denial_str = user_activity.last_denial.strftime('%m-%d %H:%M') if user_activity.last_denial else 'N/A'

                rows.append([
                    user_display,
                    user_activity.total_denials,
                    user_activity.unique_permissions,
                    user_activity.unique_ips,
                    last_denial_str
                ])

            self.output_table(rows, headers=headers)
            self.output_warning(f"Found {len(suspicious_users)} users with suspicious activity")

            return 0

        except Exception as e:
            self.log_error(f"Error checking suspicious activity: {e}")
            self.output_error(f"Error retrieving suspicious activity: {e}")
            return 1

    def cleanup_old_logs(self, days=90, dry_run=True):
        """Clean up old RBAC audit logs"""
        try:
            # Get count and cutoff using model method
            old_count, cutoff_date = self.audit_log_model.cleanup_old_logs(self.session, days)

            if old_count == 0:
                self.output_info(f"No RBAC audit logs older than {days} days found")
                return 0

            if dry_run:
                self.output_warning(f"DRY RUN: Would delete {old_count} RBAC audit logs older than {days} days")
                self.output_info("Use --no-dry-run to actually delete")
                return 0
            else:
                # Actually delete using model method
                deleted = self.audit_log_model.delete_old_logs(self.session, cutoff_date)
                self.output_success(f"Deleted {deleted} RBAC audit logs older than {days} days")
                return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error cleaning up logs: {e}")
            self.output_error(f"Error during cleanup: {e}")
            return 1


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='Audit Log Analysis CLI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Recent activity
    activity_parser = subparsers.add_parser('activity', help='Show recent API activity')
    activity_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    activity_parser.add_argument('--limit', type=int, default=50, help='Max records to show (default: 50)')

    # Security alerts
    security_parser = subparsers.add_parser('security', help='Show security alerts')
    security_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')

    # Performance stats
    perf_parser = subparsers.add_parser('performance', help='Show permission check performance')
    perf_parser.add_argument('--interface', choices=['api', 'web', 'cli', 'system'], help='Filter by interface type')
    perf_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')

    # User activity
    user_parser = subparsers.add_parser('user', help='Show user permission activity')
    user_parser.add_argument('user_identity', help='Username, email, or UUID')
    user_parser.add_argument('--days', type=int, default=7, help='Days to look back (default: 7)')

    # Permission usage
    usage_parser = subparsers.add_parser('usage', help='Show permission usage statistics')
    usage_parser.add_argument('--days', type=int, default=7, help='Days to look back (default: 7)')

    # Permission denial analysis
    error_parser = subparsers.add_parser('denials', help='Analyze permission denials')
    error_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')

    # Suspicious activity
    suspicious_parser = subparsers.add_parser('suspicious', help='Find suspicious activity patterns')
    suspicious_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    suspicious_parser.add_argument('--min-denials', type=int, default=5, help='Minimum denials to flag as suspicious (default: 5)')

    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old audit logs')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Delete logs older than X days (default: 90)')
    cleanup_parser.add_argument('--no-dry-run', action='store_true', help='Actually delete (default is dry run)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = AuditAnalysisCLI(
        verbose=args.verbose,
        show_icons=not args.no_icons,
        table_format=args.table_format
    )

    try:
        if args.command == 'activity':
            return cli.show_recent_activity(args.hours, args.limit)
        elif args.command == 'security':
            return cli.show_security_alerts(args.hours)
        elif args.command == 'performance':
            return cli.show_performance_stats(args.interface, args.hours)
        elif args.command == 'user':
            return cli.show_user_activity(args.user_identity, args.days)
        elif args.command == 'usage':
            return cli.show_permission_usage(args.days)
        elif args.command == 'denials':
            return cli.show_error_analysis(args.hours)
        elif args.command == 'suspicious':
            return cli.show_suspicious_activity(args.hours, args.min_denials)
        elif args.command == 'cleanup':
            return cli.cleanup_old_logs(args.days, not args.no_dry_run)

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