"""Validation service - Post-deployment VM validation"""
import asyncio
import time
from typing import Optional, Dict, Any

from app.config import Settings
from app.services.proxmox_service import ProxmoxService
from app.schemas.validation import ValidationCheck, ValidationResult
from app.utils.port_checker import check_port_open
from app.core.exceptions import VMNotFoundError, ValidationError


class ValidationService:
    """Service for post-deployment VM validation"""

    def __init__(self, proxmox_service: ProxmoxService, settings: Settings):
        self.proxmox = proxmox_service
        self.settings = settings

    async def validate_vm(
        self,
        vmid: int,
        os_type: str = "linux",
        timeout: Optional[int] = None
    ) -> ValidationResult:
        """
        Perform comprehensive VM validation

        Args:
            vmid: VM ID to validate
            os_type: Operating system type ("linux" or "windows")
            timeout: Validation timeout in seconds

        Returns:
            ValidationResult object
        """
        timeout = timeout or self.settings.validation_timeout
        checks: Dict[str, ValidationCheck] = {}

        try:
            # Step 1: Check Proxmox status
            checks["proxmox_status"] = await self._check_proxmox_status(vmid)

            # Step 2: Wait for IP address
            ip_address = await self._wait_for_ip(vmid, timeout=120)

            if not ip_address:
                return ValidationResult(
                    vmid=vmid,
                    status="degraded",
                    ip_address=None,
                    checks=checks,
                    message="VM is running but no IP address assigned"
                )

            # Step 3: Check port connectivity
            port = self.settings.validation_ssh_port if os_type == "linux" else self.settings.validation_rdp_port
            port_name = "SSH" if os_type == "linux" else "RDP"

            checks[f"{port_name.lower()}_port"] = await self._check_port(ip_address, port, port_name)

            # Determine overall status
            required_checks = [check for check in checks.values() if check.required]
            all_passed = all(check.passed for check in required_checks)

            status = "healthy" if all_passed else "degraded"
            message = "All validation checks passed" if all_passed else "Some validation checks failed"

            return ValidationResult(
                vmid=vmid,
                status=status,
                ip_address=ip_address,
                checks=checks,
                message=message
            )

        except Exception as e:
            checks["error"] = ValidationCheck(
                passed=False,
                message=f"Validation failed: {str(e)}",
                details={"error": str(e)}
            )

            return ValidationResult(
                vmid=vmid,
                status="unhealthy",
                ip_address=None,
                checks=checks,
                message=f"Validation failed: {str(e)}"
            )

    async def _check_proxmox_status(self, vmid: int) -> ValidationCheck:
        """
        Check VM status in Proxmox

        Args:
            vmid: VM ID

        Returns:
            ValidationCheck object
        """
        try:
            # Find node
            node = self.proxmox.find_vm_node(vmid)
            if not node:
                return ValidationCheck(
                    passed=False,
                    message=f"VM {vmid} not found",
                    required=True
                )

            # Get status
            status = self.proxmox.get_vm_status(node, vmid)

            vm_status = status.get('status', 'unknown')
            uptime = status.get('uptime', 0)

            if vm_status == 'running':
                return ValidationCheck(
                    passed=True,
                    message=f"VM is running (uptime: {uptime}s)",
                    details={
                        "status": vm_status,
                        "uptime": uptime,
                        "node": node
                    },
                    required=True
                )
            else:
                return ValidationCheck(
                    passed=False,
                    message=f"VM is not running (status: {vm_status})",
                    details={
                        "status": vm_status,
                        "node": node
                    },
                    required=True
                )

        except VMNotFoundError:
            return ValidationCheck(
                passed=False,
                message=f"VM {vmid} not found",
                required=True
            )
        except Exception as e:
            return ValidationCheck(
                passed=False,
                message=f"Failed to check Proxmox status: {str(e)}",
                details={"error": str(e)},
                required=True
            )

    async def _wait_for_ip(
        self,
        vmid: int,
        timeout: int = 120,
        retry_interval: int = 10
    ) -> Optional[str]:
        """
        Wait for VM to get an IP address

        Args:
            vmid: VM ID
            timeout: Maximum wait time in seconds
            retry_interval: Seconds between retries

        Returns:
            IP address or None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                ip = self._get_vm_ip_address(vmid)
                if ip:
                    return ip

                await asyncio.sleep(retry_interval)

            except Exception:
                await asyncio.sleep(retry_interval)

        return None

    def _get_vm_ip_address(self, vmid: int) -> Optional[str]:
        """
        Get VM IP address from QEMU agent

        Args:
            vmid: VM ID

        Returns:
            IP address or None
        """
        try:
            # Find node
            node = self.proxmox.find_vm_node(vmid)
            if not node:
                return None

            # Try to get network interfaces from QEMU agent
            interfaces = self.proxmox.get_vm_network_interfaces(node, vmid)

            if not interfaces:
                return None

            # Look for non-loopback IPv4 address
            for iface in interfaces:
                if 'ip-addresses' in iface:
                    for ip_info in iface['ip-addresses']:
                        ip = ip_info.get('ip-address')
                        ip_type = ip_info.get('ip-address-type', '').lower()

                        # Skip loopback and IPv6
                        if ip and ip_type == 'ipv4' and not ip.startswith('127.'):
                            return ip

            return None

        except Exception:
            return None

    async def _check_port(self, ip_address: str, port: int, port_name: str) -> ValidationCheck:
        """
        Check if a port is reachable

        Args:
            ip_address: VM IP address
            port: Port number
            port_name: Human-readable port name

        Returns:
            ValidationCheck object
        """
        try:
            result = await check_port_open(
                ip_address,
                port,
                timeout=self.settings.validation_retry_interval
            )

            return ValidationCheck(
                passed=result['passed'],
                message=result.get('message', f"{port_name} port check"),
                details=result,
                required=True
            )

        except Exception as e:
            return ValidationCheck(
                passed=False,
                message=f"Failed to check {port_name} port: {str(e)}",
                details={"error": str(e)},
                required=True
            )

    async def quick_health_check(self, vmid: int) -> bool:
        """
        Quick health check - just verify VM is running

        Args:
            vmid: VM ID

        Returns:
            True if VM is running, False otherwise
        """
        try:
            check = await self._check_proxmox_status(vmid)
            return check.passed
        except Exception:
            return False
