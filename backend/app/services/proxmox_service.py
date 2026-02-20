"""Proxmox API service - Core wrapper around proxmoxer"""
import time
from typing import Dict, List, Optional, Any
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException, AuthenticationError

from app.config import Settings
from app.core.exceptions import (
    ProxmoxConnectionError,
    VMCreationError,
    VMCloneError,
    VMNotFoundError,
    ResourceNotFoundError,
    InvalidVMIDError
)


class ProxmoxService:
    """Service for interacting with Proxmox API"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._proxmox: Optional[ProxmoxAPI] = None

    @property
    def proxmox(self) -> ProxmoxAPI:
        """Get or create Proxmox API connection"""
        if self._proxmox is None:
            self._proxmox = self.connect()
        else:
            # Test if connection is still valid
            try:
                self._proxmox.version.get()
            except Exception:
                # Connection expired, reconnect
                self._proxmox = self.connect()
        return self._proxmox

    def connect(self) -> ProxmoxAPI:
        """Connect to Proxmox API"""
        try:
            proxmox = ProxmoxAPI(
                self.settings.proxmox_host,
                user=self.settings.proxmox_user,
                password=self.settings.proxmox_password,
                port=self.settings.proxmox_port,
                verify_ssl=self.settings.proxmox_verify_ssl
            )
            # Test connection
            proxmox.version.get()
            return proxmox
        except AuthenticationError as e:
            raise ProxmoxConnectionError(f"Authentication failed: {str(e)}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to connect to Proxmox: {str(e)}")

    def get_version(self) -> Dict[str, Any]:
        """Get Proxmox version information"""
        try:
            return self.proxmox.version.get()
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get version: {str(e)}")

    def list_nodes(self) -> List[Dict[str, Any]]:
        """List all Proxmox nodes"""
        try:
            return self.proxmox.nodes.get()
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to list nodes: {str(e)}")

    def get_node_info(self, node: str) -> Dict[str, Any]:
        """Get information about a specific node"""
        try:
            return self.proxmox.nodes(node).status.get()
        except ResourceException:
            raise ResourceNotFoundError(f"Node '{node}' not found")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get node info: {str(e)}")

    def list_vms(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all VMs on a node or all nodes"""
        try:
            if node:
                return self.proxmox.nodes(node).qemu.get()
            else:
                # List VMs from all nodes
                all_vms = []
                for node_info in self.list_nodes():
                    node_name = node_info['node']
                    vms = self.proxmox.nodes(node_name).qemu.get()
                    for vm in vms:
                        vm['node'] = node_name
                    all_vms.extend(vms)
                return all_vms
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to list VMs: {str(e)}")

    def get_vm_config(self, node: str, vmid: int) -> Dict[str, Any]:
        """Get VM configuration"""
        try:
            return self.proxmox.nodes(node).qemu(vmid).config.get()
        except ResourceException:
            raise VMNotFoundError(f"VM {vmid} not found on node {node}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get VM config: {str(e)}")

    def get_vm_status(self, node: str, vmid: int) -> Dict[str, Any]:
        """Get VM status"""
        try:
            return self.proxmox.nodes(node).qemu(vmid).status.current.get()
        except ResourceException:
            raise VMNotFoundError(f"VM {vmid} not found on node {node}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get VM status: {str(e)}")

    def find_vm_node(self, vmid: int) -> Optional[str]:
        """Find which node a VM is on"""
        try:
            all_vms = self.list_vms()
            for vm in all_vms:
                if vm['vmid'] == vmid:
                    return vm.get('node')
            return None
        except Exception:
            return None

    def get_next_vmid(self) -> int:
        """Get next available VM ID"""
        try:
            return int(self.proxmox.cluster.nextid.get())
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get next VMID: {str(e)}")

    def clone_vm(
        self,
        node: str,
        source_vmid: int,
        new_vmid: int,
        name: Optional[str] = None,
        storage: Optional[str] = None,
        full: int = 1,
        **kwargs
    ) -> str:
        """
        Clone a VM

        Args:
            node: Target node name
            source_vmid: Source VM ID to clone from
            new_vmid: New VM ID
            name: Name for the new VM
            storage: Target storage
            full: 1 for full clone, 0 for linked clone
            **kwargs: Additional clone parameters

        Returns:
            Task ID (UPID)
        """
        try:
            clone_params = {
                'newid': new_vmid,
                'full': full,
            }

            if name:
                clone_params['name'] = name
            if storage:
                clone_params['storage'] = storage

            clone_params.update(kwargs)

            # Start clone task
            task_id = self.proxmox.nodes(node).qemu(source_vmid).clone.post(**clone_params)
            return task_id

        except ResourceException as e:
            if "already exists" in str(e).lower():
                raise InvalidVMIDError(f"VM ID {new_vmid} already exists")
            raise VMCloneError(f"Failed to clone VM: {str(e)}")
        except Exception as e:
            raise VMCloneError(f"Failed to clone VM: {str(e)}")

    def create_vm(self, node: str, vmid: int, **kwargs) -> str:
        """
        Create a new VM

        Args:
            node: Target node name
            vmid: VM ID
            **kwargs: VM configuration parameters

        Returns:
            Task ID (UPID)
        """
        try:
            vm_params = {'vmid': vmid}
            vm_params.update(kwargs)

            task_id = self.proxmox.nodes(node).qemu.post(**vm_params)
            return task_id

        except ResourceException as e:
            if "already exists" in str(e).lower():
                raise InvalidVMIDError(f"VM ID {vmid} already exists")
            raise VMCreationError(f"Failed to create VM: {str(e)}")
        except Exception as e:
            raise VMCreationError(f"Failed to create VM: {str(e)}")

    def start_vm(self, node: str, vmid: int) -> str:
        """
        Start a VM

        Returns:
            Task ID (UPID)
        """
        try:
            task_id = self.proxmox.nodes(node).qemu(vmid).status.start.post()
            return task_id
        except ResourceException:
            raise VMNotFoundError(f"VM {vmid} not found on node {node}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to start VM: {str(e)}")

    def stop_vm(self, node: str, vmid: int) -> str:
        """
        Stop a VM

        Returns:
            Task ID (UPID)
        """
        try:
            task_id = self.proxmox.nodes(node).qemu(vmid).status.stop.post()
            return task_id
        except ResourceException:
            raise VMNotFoundError(f"VM {vmid} not found on node {node}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to stop VM: {str(e)}")

    def delete_vm(self, node: str, vmid: int, purge: bool = True) -> str:
        """
        Delete a VM

        Args:
            node: Node name
            vmid: VM ID
            purge: Remove VM from all disk locations

        Returns:
            Task ID (UPID)
        """
        try:
            task_id = self.proxmox.nodes(node).qemu(vmid).delete(purge=int(purge))
            return task_id
        except ResourceException:
            raise VMNotFoundError(f"VM {vmid} not found on node {node}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to delete VM: {str(e)}")

    def get_task_status(self, node: str, upid: str) -> Dict[str, Any]:
        """Get status of a Proxmox task"""
        try:
            return self.proxmox.nodes(node).tasks(upid).status.get()
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to get task status: {str(e)}")

    def wait_for_task(self, node: str, upid: str, timeout: int = 300) -> bool:
        """
        Wait for a Proxmox task to complete

        Args:
            node: Node name
            upid: Task ID (UPID)
            timeout: Maximum wait time in seconds

        Returns:
            True if task completed successfully, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status = self.get_task_status(node, upid)

                if status['status'] == 'stopped':
                    return status.get('exitstatus') == 'OK'

                time.sleep(2)

            except Exception:
                time.sleep(2)

        return False

    def update_vm_config(self, node: str, vmid: int, **kwargs) -> None:
        """Update VM configuration"""
        try:
            self.proxmox.nodes(node).qemu(vmid).config.put(**kwargs)
        except ResourceException:
            raise VMNotFoundError(f"VM {vmid} not found on node {node}")
        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to update VM config: {str(e)}")

    def get_vm_agent_info(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get QEMU agent information (if available)"""
        try:
            return self.proxmox.nodes(node).qemu(vmid).agent.get()
        except Exception:
            return None

    def get_vm_network_interfaces(self, node: str, vmid: int) -> Optional[List[Dict[str, Any]]]:
        """Get VM network interfaces via QEMU agent"""
        try:
            result = self.proxmox.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
            return result.get('result', [])
        except Exception:
            return None
