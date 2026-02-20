"""Template service - Handle template listing and cloning"""
import time
from typing import List, Optional

from app.config import Settings
from app.services.proxmox_service import ProxmoxService
from app.services.audit_service import get_audit_logger
from app.schemas.template import TemplateInfo, CloneRequest, CloneResponse
from app.core.exceptions import (
    TemplateNotFoundError,
    VMCloneError,
    InvalidVMIDError,
    ProxmoxConnectionError
)


class TemplateService:
    """Service for template operations"""

    def __init__(self, proxmox_service: ProxmoxService, settings: Settings):
        self.proxmox = proxmox_service
        self.settings = settings
        self.audit_logger = get_audit_logger()

    def list_templates(self, node: Optional[str] = None) -> List[TemplateInfo]:
        """
        List all VM templates

        Args:
            node: Optional node name to filter templates

        Returns:
            List of TemplateInfo objects
        """
        try:
            vms = self.proxmox.list_vms(node=node)

            templates = []
            for vm in vms:
                # Filter only templates
                if vm.get('template', 0) == 1:
                    # Format disk size
                    disk_size = vm.get('maxdisk')
                    disk_size_gb = None
                    if disk_size:
                        disk_size_gb = f"{disk_size / (1024**3):.2f} GB"

                    template_info = TemplateInfo(
                        vmid=vm['vmid'],
                        name=vm.get('name', f"template-{vm['vmid']}"),
                        node=vm.get('node', self.settings.default_node),
                        status=vm.get('status', 'unknown'),
                        template=True,
                        cores=vm.get('cpus'),
                        memory=vm.get('maxmem', 0) // (1024 * 1024) if vm.get('maxmem') else None,  # Convert to MB
                        disk_size=disk_size,
                        disk_size_gb=disk_size_gb,
                        description=None  # Will be fetched from config if needed
                    )
                    templates.append(template_info)

            return templates

        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to list templates: {str(e)}")

    def get_template_details(self, vmid: int) -> TemplateInfo:
        """
        Get detailed information about a specific template

        Args:
            vmid: Template VM ID

        Returns:
            TemplateInfo object
        """
        try:
            # Find which node the template is on
            node = self.proxmox.find_vm_node(vmid)
            if not node:
                raise TemplateNotFoundError(f"Template {vmid} not found")

            # Get VM status
            status = self.proxmox.get_vm_status(node, vmid)

            # Get VM config
            config = self.proxmox.get_vm_config(node, vmid)

            # Check if it's actually a template
            if not config.get('template', 0):
                raise TemplateNotFoundError(f"VM {vmid} is not a template")

            # Parse disk size
            disk_size = None
            disk_size_gb = None
            for key, value in config.items():
                if key.startswith('scsi') or key.startswith('virtio') or key.startswith('ide'):
                    if isinstance(value, str) and 'size=' in value:
                        size_str = value.split('size=')[1].split(',')[0]
                        disk_size_gb = size_str
                        # Try to convert to bytes for consistency
                        try:
                            if 'G' in size_str:
                                disk_size = int(float(size_str.replace('G', '')) * (1024**3))
                        except:
                            pass
                        break

            template_info = TemplateInfo(
                vmid=vmid,
                name=config.get('name', f"template-{vmid}"),
                node=node,
                status=status.get('status', 'unknown'),
                template=True,
                cores=config.get('cores', config.get('cpus')),
                memory=config.get('memory'),
                disk_size=disk_size,
                disk_size_gb=disk_size_gb,
                description=config.get('description')
            )

            return template_info

        except TemplateNotFoundError:
            raise
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get template details: {str(e)}")

    def clone_from_template(self, request: CloneRequest) -> CloneResponse:
        """
        Clone a VM from a template

        Args:
            request: CloneRequest object

        Returns:
            CloneResponse object
        """
        try:
            # Verify source template exists
            source_node = self.proxmox.find_vm_node(request.source_vmid)
            if not source_node:
                raise TemplateNotFoundError(f"Template {request.source_vmid} not found")

            # Verify it's actually a template
            config = self.proxmox.get_vm_config(source_node, request.source_vmid)
            if not config.get('template', 0):
                raise TemplateNotFoundError(f"VM {request.source_vmid} is not a template")

            # Determine target node
            target_node = request.node or self.settings.default_node

            # Get or assign new VMID
            new_vmid = request.new_vmid
            if not new_vmid:
                new_vmid = self.proxmox.get_next_vmid()

            # Validate VMID range
            if new_vmid < self.settings.vmid_min or new_vmid > self.settings.vmid_max:
                raise InvalidVMIDError(
                    f"VM ID {new_vmid} is outside allowed range "
                    f"({self.settings.vmid_min}-{self.settings.vmid_max})"
                )

            # Prepare clone parameters
            storage = request.storage or self.settings.default_storage

            # Start cloning
            task_id = self.proxmox.clone_vm(
                node=source_node,
                source_vmid=request.source_vmid,
                new_vmid=new_vmid,
                name=request.name,
                storage=storage,
                full=1 if request.full_clone else 0,
                description=request.description
            )

            # Wait for clone to complete
            clone_success = self.wait_for_clone_completion(
                node=source_node,
                task_id=task_id,
                timeout=self.settings.validation_timeout
            )

            if not clone_success:
                raise VMCloneError(f"Clone operation timed out or failed")

            # Apply customizations if specified
            if request.cores or request.memory or request.tags:
                self._apply_customizations(target_node, new_vmid, request)

            # Apply cloud-init configuration if specified
            if request.cloudinit:
                self._apply_cloudinit(target_node, new_vmid, request)

            # Start VM if requested
            if request.start_after_clone and self.settings.enable_auto_start:
                try:
                    self.proxmox.start_vm(target_node, new_vmid)
                    status = "started"
                    message = f"VM {new_vmid} cloned and started successfully"
                except Exception as e:
                    status = "created"
                    message = f"VM {new_vmid} cloned successfully but failed to start: {str(e)}"
            else:
                status = "created"
                message = f"VM {new_vmid} cloned successfully"

            response = CloneResponse(
                vmid=new_vmid,
                name=request.name,
                node=target_node,
                status=status,
                message=message,
                task_id=task_id
            )

            # Get template name for audit log
            template_name = config.get('name', f"template-{request.source_vmid}")

            # Audit log: successful clone
            self.audit_logger.log_template_clone(
                request=request,
                username=self.settings.proxmox_user,
                template_name=template_name,
                result=response.dict()
            )

            return response

        except (TemplateNotFoundError, InvalidVMIDError, VMCloneError) as e:
            # Audit log: failed clone
            self.audit_logger.log_template_clone(
                request=request,
                username=self.settings.proxmox_user,
                error=str(e)
            )
            raise
        except Exception as e:
            # Audit log: unexpected error
            self.audit_logger.log_template_clone(
                request=request,
                username=self.settings.proxmox_user,
                error=f"Unexpected error: {str(e)}"
            )
            raise VMCloneError(f"Failed to clone template: {str(e)}")

    def wait_for_clone_completion(
        self,
        node: str,
        task_id: str,
        timeout: int = 300
    ) -> bool:
        """
        Wait for clone task to complete

        Args:
            node: Node name where task is running
            task_id: Proxmox task ID (UPID)
            timeout: Maximum wait time in seconds

        Returns:
            True if successful, False otherwise
        """
        return self.proxmox.wait_for_task(node, task_id, timeout)

    def _apply_customizations(
        self,
        node: str,
        vmid: int,
        request: CloneRequest
    ) -> None:
        """
        Apply CPU, memory, and tags customizations to cloned VM

        Args:
            node: Node name
            vmid: VM ID
            request: Clone request with customizations
        """
        try:
            update_params = {}

            if request.cores:
                update_params['cores'] = request.cores

            if request.memory:
                update_params['memory'] = request.memory

            if request.tags:
                # Tags in Proxmox are semicolon-separated
                update_params['tags'] = ';'.join(request.tags)

            if update_params:
                self.proxmox.update_vm_config(node, vmid, **update_params)

        except Exception as e:
            # Non-fatal error - VM is created, just customization failed
            raise VMCloneError(f"VM cloned but customization failed: {str(e)}")

    def _apply_cloudinit(
        self,
        node: str,
        vmid: int,
        request: CloneRequest
    ) -> None:
        """
        Apply cloud-init configuration to cloned VM

        Args:
            node: Node name
            vmid: VM ID
            request: Clone request with cloud-init config
        """
        try:
            from app.utils.cloudinit import apply_custom_cloudinit

            if request.cloudinit:
                # Use the VM name as hostname
                hostname = request.name

                # Apply custom cloud-init with full configuration support
                apply_custom_cloudinit(
                    proxmox_service=self.proxmox,
                    settings=self.settings,
                    node=node,
                    vmid=vmid,
                    config=request.cloudinit,
                    hostname=hostname
                )

        except Exception as e:
            # Non-fatal error - VM is created, just cloud-init config failed
            raise VMCloneError(f"VM cloned but cloud-init configuration failed: {str(e)}")

    def validate_template_exists(self, vmid: int) -> bool:
        """
        Check if a template exists

        Args:
            vmid: Template VM ID

        Returns:
            True if template exists, False otherwise
        """
        try:
            self.get_template_details(vmid)
            return True
        except TemplateNotFoundError:
            return False
        except Exception:
            return False
