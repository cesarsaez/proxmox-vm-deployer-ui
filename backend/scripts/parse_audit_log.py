#!/usr/bin/env python3
"""
Audit Log Parser - Parse and analyze Proxmox VM Deployer audit logs

Usage:
    python parse_audit_log.py                           # Show statistics
    python parse_audit_log.py --export-csv output.csv   # Export to CSV
    python parse_audit_log.py --filter-status failed    # Show only failed operations
    python parse_audit_log.py --filter-user root@pam    # Filter by user
    python parse_audit_log.py --since "2026-02-09"      # Operations since date
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Optional
import argparse


class AuditLogParser:
    """Parser for Proxmox VM Deployer audit logs"""

    def __init__(self, log_file: str = None):
        """Initialize parser with log file path"""
        if log_file is None:
            # Default: look for audit.log relative to this script's location
            script_dir = Path(__file__).parent
            log_file = script_dir / ".." / "logs" / "audit.log"

        self.log_file = Path(log_file).resolve()
        if not self.log_file.exists():
            raise FileNotFoundError(f"Audit log not found: {self.log_file}")

    def parse(self) -> List[Dict[str, Any]]:
        """Parse audit log and return list of entries"""
        entries = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}", file=sys.stderr)
        return entries

    def filter_entries(
        self,
        entries: List[Dict[str, Any]],
        status: Optional[str] = None,
        operation: Optional[str] = None,
        username: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter entries based on criteria"""
        filtered = entries

        if status:
            filtered = [e for e in filtered if e.get('status') == status]

        if operation:
            filtered = [e for e in filtered if e.get('operation') == operation]

        if username:
            filtered = [e for e in filtered if e.get('username') == username]

        if since:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) >= since_dt
            ]

        if until:
            until_dt = datetime.fromisoformat(until.replace('Z', '+00:00'))
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) <= until_dt
            ]

        return filtered

    def print_statistics(self, entries: List[Dict[str, Any]]):
        """Print statistics about audit log entries"""
        print("\n📊 Audit Log Statistics")
        print("=" * 60)
        print(f"Total entries: {len(entries)}")
        print()

        # Status breakdown
        status_counts = Counter(e.get('status', 'unknown') for e in entries)
        print("Status breakdown:")
        for status, count in status_counts.most_common():
            percentage = (count / len(entries) * 100) if entries else 0
            print(f"  {status:12} {count:6} ({percentage:5.1f}%)")
        print()

        # Operation breakdown
        operation_counts = Counter(e.get('operation', 'unknown') for e in entries)
        print("Operation breakdown:")
        for operation, count in operation_counts.most_common():
            print(f"  {operation:20} {count:6}")
        print()

        # User activity
        user_counts = Counter(e.get('username', 'unknown') for e in entries)
        print("User activity:")
        for user, count in user_counts.most_common():
            print(f"  {user:30} {count:6}")
        print()

        # Time range
        if entries:
            timestamps = [e['timestamp'] for e in entries if 'timestamp' in e]
            if timestamps:
                print(f"Time range:")
                print(f"  First entry: {min(timestamps)}")
                print(f"  Last entry:  {max(timestamps)}")
                print()

        # VM creation stats
        vm_creations = [e for e in entries if e.get('operation') == 'vm_creation']
        if vm_creations:
            print(f"VM Creations: {len(vm_creations)}")
            os_types = Counter(
                e.get('configuration', {}).get('os_type', 'unknown')
                for e in vm_creations
            )
            print("  By OS type:")
            for os_type, count in os_types.most_common():
                print(f"    {os_type:15} {count:6}")
            print()

        # Template clones
        clones = [e for e in entries if e.get('operation') == 'template_clone']
        if clones:
            print(f"Template Clones: {len(clones)}")
            print()

        # Failures
        failures = [e for e in entries if e.get('status') == 'failed']
        if failures:
            print(f"⚠️  Recent failures: {len(failures)}")
            for failure in failures[-5:]:  # Show last 5
                print(f"  • {failure.get('timestamp')} - {failure.get('operation')}: {failure.get('error', 'Unknown error')}")

    def export_csv(self, entries: List[Dict[str, Any]], output_file: str):
        """Export entries to CSV file"""
        if not entries:
            print("No entries to export")
            return

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            # Define CSV columns
            fieldnames = [
                'timestamp', 'operation', 'operation_type', 'username',
                'status', 'vm_name', 'vm_id', 'node', 'task_id', 'error'
            ]

            # Add configuration fields for VM creation
            if any(e.get('operation') == 'vm_creation' for e in entries):
                fieldnames.extend([
                    'cores', 'memory_mb', 'disk_size_gb', 'os_type',
                    'iso', 'virtio_iso', 'tags'
                ])

            # Add template fields for clones
            if any(e.get('operation') == 'template_clone' for e in entries):
                fieldnames.extend(['template_id', 'template_name'])

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for entry in entries:
                row = {
                    'timestamp': entry.get('timestamp'),
                    'operation': entry.get('operation'),
                    'operation_type': entry.get('operation_type'),
                    'username': entry.get('username'),
                    'status': entry.get('status'),
                    'vm_name': entry.get('vm_name'),
                    'vm_id': entry.get('vm_id'),
                    'node': entry.get('node'),
                    'task_id': entry.get('task_id'),
                    'error': entry.get('error'),
                }

                # Add configuration details if present
                config = entry.get('configuration', {})
                if config:
                    row.update({
                        'cores': config.get('cores'),
                        'memory_mb': config.get('memory_mb'),
                        'disk_size_gb': config.get('disk_size_gb'),
                        'os_type': config.get('os_type'),
                        'iso': config.get('iso'),
                        'virtio_iso': config.get('virtio_iso'),
                        'tags': ','.join(config.get('tags', [])) if config.get('tags') else ''
                    })

                # Add template details if present
                template = entry.get('source_template', {})
                if template:
                    row.update({
                        'template_id': template.get('template_id'),
                        'template_name': template.get('template_name')
                    })

                writer.writerow(row)

        print(f"✅ Exported {len(entries)} entries to {output_file}")

    def print_entries(self, entries: List[Dict[str, Any]]):
        """Print entries in human-readable format"""
        for entry in entries:
            print("\n" + "=" * 60)
            print(f"Timestamp:  {entry.get('timestamp')}")
            print(f"Operation:  {entry.get('operation')}")
            print(f"Username:   {entry.get('username')}")
            print(f"Status:     {entry.get('status')}")

            if entry.get('vm_name'):
                print(f"VM Name:    {entry.get('vm_name')}")
            if entry.get('vm_id'):
                print(f"VM ID:      {entry.get('vm_id')}")

            if entry.get('error'):
                print(f"Error:      {entry.get('error')}")

            if entry.get('configuration'):
                print("\nConfiguration:")
                config = entry['configuration']
                for key, value in config.items():
                    print(f"  {key:20} {value}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Parse and analyze Proxmox VM Deployer audit logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parse_audit_log.py
  python parse_audit_log.py --export-csv output.csv
  python parse_audit_log.py --filter-status failed
  python parse_audit_log.py --filter-operation vm_creation
  python parse_audit_log.py --since "2026-02-09T00:00:00Z"
        """
    )

    parser.add_argument(
        '--log-file',
        default=None,
        help='Path to audit log file (default: auto-detect backend/logs/audit.log)'
    )
    parser.add_argument(
        '--export-csv',
        metavar='FILE',
        help='Export entries to CSV file'
    )
    parser.add_argument(
        '--filter-status',
        choices=['success', 'failed', 'partial'],
        help='Filter by status'
    )
    parser.add_argument(
        '--filter-operation',
        help='Filter by operation (vm_creation, template_clone, etc.)'
    )
    parser.add_argument(
        '--filter-user',
        help='Filter by username'
    )
    parser.add_argument(
        '--since',
        help='Show entries since timestamp (ISO format)'
    )
    parser.add_argument(
        '--until',
        help='Show entries until timestamp (ISO format)'
    )
    parser.add_argument(
        '--print-entries',
        action='store_true',
        help='Print individual entries'
    )

    args = parser.parse_args()

    try:
        # Parse log file
        log_parser = AuditLogParser(args.log_file)
        entries = log_parser.parse()

        if not entries:
            print("No entries found in audit log")
            return

        # Apply filters
        filtered_entries = log_parser.filter_entries(
            entries,
            status=args.filter_status,
            operation=args.filter_operation,
            username=args.filter_user,
            since=args.since,
            until=args.until
        )

        # Export or print
        if args.export_csv:
            log_parser.export_csv(filtered_entries, args.export_csv)
        elif args.print_entries:
            log_parser.print_entries(filtered_entries)
        else:
            log_parser.print_statistics(filtered_entries)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing audit log: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
