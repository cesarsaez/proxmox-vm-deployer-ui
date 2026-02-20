"""VM service - Handle VM creation and management"""
from typing import Optional

from app.config import Settings
from app.services.proxmox_service import ProxmoxService
from app.services.audit_service import get_audit_logger
from app.schemas.vm import VMCreateRequest, VMCreateResponse, VMInfo, VMStatus
from app.core.exceptions import (
    VMCreationError,
    InvalidVMIDError,
    ProxmoxConnectionError,
    VMNotFoundError
)


class VMService:
    """Service for VM operations"""

    def __init__(self, proxmox_service: ProxmoxService, settings: Settings):
        self.proxmox = proxmox_service
        self.settings = settings
        self.audit_logger = get_audit_logger()

    def create_vm(self, request: VMCreateRequest) -> VMCreateResponse:
        """
        Create a new VM from scratch

        Args:
            request: VMCreateRequest object

        Returns:
            VMCreateResponse object
        """
        try:
            # Determine node
            node = request.node or self.settings.default_node

            # Get or assign VMID
            vmid = request.vmid
            if not vmid:
                vmid = self.proxmox.get_next_vmid()

            # Validate VMID range
            if vmid < self.settings.vmid_min or vmid > self.settings.vmid_max:
                raise InvalidVMIDError(
                    f"VM ID {vmid} is outside allowed range "
                    f"({self.settings.vmid_min}-{self.settings.vmid_max})"
                )

            # Prepare VM configuration
            storage = request.storage or self.settings.default_storage
            network_bridge = request.network_bridge or self.settings.default_network_bridge

            vm_config = {
                'name': request.name,
                'cores': request.cores,
                'sockets': request.sockets,
                'cpu': request.cpu_type,
                'memory': request.memory,
                'net0': f'{request.network_model},bridge={network_bridge}',
                'ostype': 'l26' if request.os_type == 'linux' else 'win11',
                'bios': request.bios,
                'machine': request.machine,
            }

            # Add EFI disk for UEFI systems (required for OVMF to work properly)
            if request.bios == 'ovmf':
                vm_config['efidisk0'] = f'{storage}:1,efitype=4m,pre-enrolled-keys=1'

            # Add disk configuration
            vm_config['scsi0'] = f'{storage}:{request.disk_size}'
            vm_config['scsihw'] = 'virtio-scsi-pci'

            # Add QEMU guest agent if enabled
            if request.enable_guest_agent:
                vm_config['agent'] = '1'

            # Add primary ISO if provided (ide2 is standard for first CD/DVD, bootable)
            if request.iso:
                vm_config['ide2'] = f'{request.iso},media=cdrom'

            # Add VirtIO drivers ISO as second CD/DVD (ide0) for Windows VMs
            # Using ide0 instead of ide3 to avoid boot order issues
            if request.virtio_iso:
                vm_config['ide0'] = f'{request.virtio_iso},media=cdrom'

            # Set boot order: CD-ROM first for installation, then disk
            # ide2 = Windows installation ISO (bootable)
            # scsi0 = Hard disk (boots after OS is installed)
            vm_config['boot'] = 'order=ide2;scsi0'

            # Add description if provided
            if request.description:
                vm_config['description'] = request.description

            # Add tags if provided
            if request.tags:
                vm_config['tags'] = ';'.join(request.tags)

            # Create VM
            task_id = self.proxmox.create_vm(node, vmid, **vm_config)

            # Wait for creation to complete
            creation_success = self.proxmox.wait_for_task(node, task_id, timeout=120)

            if not creation_success:
                raise VMCreationError(f"VM creation timed out or failed")

            # Start VM if requested
            if request.start_on_creation and self.settings.enable_auto_start:
                try:
                    self.proxmox.start_vm(node, vmid)
                    status = "started"
                    message = f"VM {vmid} created and started successfully"
                except Exception as e:
                    status = "created"
                    message = f"VM {vmid} created but failed to start: {str(e)}"
            else:
                status = "created"
                message = f"VM {vmid} created successfully"

            response = VMCreateResponse(
                vmid=vmid,
                name=request.name,
                node=node,
                status=status,
                message=message,
                task_id=task_id
            )

            # Audit log: successful creation
            self.audit_logger.log_vm_creation(
                request=request,
                username=self.settings.proxmox_user,
                result=response.dict()
            )

            return response

        except (InvalidVMIDError, VMCreationError) as e:
            # Audit log: failed creation
            self.audit_logger.log_vm_creation(
                request=request,
                username=self.settings.proxmox_user,
                error=str(e)
            )
            raise
        except Exception as e:
            # Audit log: unexpected error
            self.audit_logger.log_vm_creation(
                request=request,
                username=self.settings.proxmox_user,
                error=f"Unexpected error: {str(e)}"
            )
            raise VMCreationError(f"Failed to create VM: {str(e)}")

    def get_vm_info(self, vmid: int) -> VMInfo:
        """
        Get VM information

        Args:
            vmid: VM ID

        Returns:
            VMInfo object
        """
        try:
            # Find node
            node = self.proxmox.find_vm_node(vmid)
            if not node:
                raise VMNotFoundError(f"VM {vmid} not found")

            # Get VM status
            status = self.proxmox.get_vm_status(node, vmid)

            # Get VM config
            config = self.proxmox.get_vm_config(node, vmid)

            vm_info = VMInfo(
                vmid=vmid,
                name=config.get('name', f"vm-{vmid}"),
                node=node,
                status=status.get('status', 'unknown'),
                cores=config.get('cores', config.get('cpus')),
                memory=config.get('memory'),
                uptime=status.get('uptime')
            )

            return vm_info

        except VMNotFoundError:
            raise
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get VM info: {str(e)}")

    def get_vm_status(self, vmid: int) -> VMStatus:
        """
        Get VM status

        Args:
            vmid: VM ID

        Returns:
            VMStatus object
        """
        try:
            # Find node
            node = self.proxmox.find_vm_node(vmid)
            if not node:
                raise VMNotFoundError(f"VM {vmid} not found")

            # Get status
            status = self.proxmox.get_vm_status(node, vmid)

            return VMStatus(
                vmid=vmid,
                node=node,
                status=status.get('status', 'unknown'),
                uptime=status.get('uptime'),
                cpu=status.get('cpu'),
                memory=status.get('mem'),
                maxmem=status.get('maxmem')
            )

        except VMNotFoundError:
            raise
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get VM status: {str(e)}")

    def validate_vm_config(self, request: VMCreateRequest) -> dict:
        """
        Validate VM configuration before creation

        Args:
            request: VMCreateRequest object

        Returns:
            Validation result dictionary
        """
        issues = []

        # Check cores
        if request.cores < 1 or request.cores > 256:
            issues.append("cores must be between 1 and 256")

        # Check memory
        if request.memory < 512:
            issues.append("memory must be at least 512 MB")

        # Check disk size
        if request.disk_size < 8:
            issues.append("disk_size must be at least 8 GB")

        # Check OS type
        if request.os_type not in ['linux', 'windows']:
            issues.append("os_type must be 'linux' or 'windows'")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
