"""Audit logging service - Track all VM deployments and clones"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from logging.handlers import RotatingFileHandler

from app.schemas.vm import VMCreateRequest
from app.schemas.template import CloneRequest


class AuditLogger:
    """Audit logger for VM operations"""

    def __init__(self, log_file: str = "logs/audit.log"):
        """
        Initialize audit logger

        Args:
            log_file: Path to audit log file (JSON Lines format)
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create dedicated audit logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Rotating file handler (10MB per file, keep 10 files)
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )

        # Use JSON formatter (one JSON object per line)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

        # Don't propagate to root logger
        self.logger.propagate = False

    def _log_entry(self, entry: Dict[str, Any]) -> None:
        """
        Write audit entry to log file as JSON

        Args:
            entry: Audit entry dictionary
        """
        # Add timestamp if not present
        if 'timestamp' not in entry:
            entry['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Write as single-line JSON (JSON Lines format)
        self.logger.info(json.dumps(entry, ensure_ascii=False))

    def log_vm_creation(
        self,
        request: VMCreateRequest,
        username: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log VM creation attempt

        Args:
            request: VM creation request
            username: Proxmox username used
            result: Creation result if successful
            error: Error message if failed
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'operation': 'vm_creation',
            'operation_type': 'create',
            'username': username,
            'status': 'success' if result else 'failed',
            'vm_name': request.name,
            'vm_id': request.vmid or (result.get('vmid') if result else None),
            'configuration': {
                'cores': request.cores,
                'sockets': request.sockets,
                'cpu_type': request.cpu_type,
                'memory_mb': request.memory,
                'disk_size_gb': request.disk_size,
                'storage': request.storage,
                'network_bridge': request.network_bridge,
                'network_model': request.network_model,
                'os_type': request.os_type,
                'bios': request.bios,
                'machine': request.machine,
                'iso': request.iso,
                'virtio_iso': request.virtio_iso,
                'enable_guest_agent': request.enable_guest_agent,
                'start_on_creation': request.start_on_creation,
                'tags': request.tags or []
            },
            'node': result.get('node') if result else request.node,
            'task_id': result.get('task_id') if result else None,
            'error': error
        }

        self._log_entry(entry)

    def log_template_clone(
        self,
        request: CloneRequest,
        username: str,
        template_name: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log template cloning attempt

        Args:
            request: Clone request
            username: Proxmox username used
            template_name: Name of source template
            result: Clone result if successful
            error: Error message if failed
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'operation': 'template_clone',
            'operation_type': 'clone',
            'username': username,
            'status': 'success' if result else 'failed',
            'source_template': {
                'template_id': request.source_vmid,
                'template_name': template_name
            },
            'vm_name': request.name,
            'vm_id': request.new_vmid or (result.get('vmid') if result else None),
            'configuration': {
                'cores': request.cores,
                'memory_mb': request.memory,
                'storage': request.storage,
                'full_clone': request.full_clone,
                'start_after_clone': request.start_after_clone,
                'tags': request.tags or []
            },
            'node': result.get('node') if result else request.node,
            'task_id': result.get('task_id') if result else None,
            'error': error
        }

        self._log_entry(entry)

    def log_batch_operation(
        self,
        operation_type: str,
        username: str,
        total: int,
        successful: int,
        failed: int,
        requests: List[Dict[str, Any]],
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Log batch operation summary

        Args:
            operation_type: 'batch_clone' or 'batch_create'
            username: Proxmox username used
            total: Total number of VMs requested
            successful: Number of successful operations
            failed: Number of failed operations
            requests: List of request data
            results: List of results
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'operation': operation_type,
            'operation_type': 'batch',
            'username': username,
            'status': 'partial' if failed > 0 else 'success',
            'summary': {
                'total_requested': total,
                'successful': successful,
                'failed': failed,
                'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%"
            },
            'operations': [
                {
                    'vm_name': req.get('name'),
                    'vm_id': res.get('vmid'),
                    'status': res.get('status'),
                    'message': res.get('message')
                }
                for req, res in zip(requests, results)
            ]
        }

        self._log_entry(entry)

    def log_validation(
        self,
        vm_id: int,
        vm_name: Optional[str],
        username: str,
        validation_result: Dict[str, Any]
    ) -> None:
        """
        Log post-deployment validation

        Args:
            vm_id: VM ID
            vm_name: VM name
            username: Proxmox username used
            validation_result: Validation result
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'operation': 'validation',
            'operation_type': 'validate',
            'username': username,
            'vm_id': vm_id,
            'vm_name': vm_name,
            'validation_status': validation_result.get('status'),
            'checks': validation_result.get('checks', {})
        }

        self._log_entry(entry)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
