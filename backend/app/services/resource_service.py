"""Resource service - Handle resource discovery and listing"""
from typing import List, Dict, Any, Optional

from app.config import Settings
from app.services.proxmox_service import ProxmoxService
from app.schemas.resource import StorageInfo, ISOInfo
from app.core.exceptions import ProxmoxConnectionError


class ResourceService:
    """Service for resource discovery operations"""

    def __init__(self, proxmox_service: ProxmoxService, settings: Settings):
        self.proxmox = proxmox_service
        self.settings = settings

    def list_storages(self, node: Optional[str] = None) -> List[StorageInfo]:
        """
        List available storage pools

        Args:
            node: Optional node name to filter storages

        Returns:
            List of StorageInfo objects
        """
        try:
            target_node = node or self.settings.default_node
            storages = self.proxmox.proxmox.nodes(target_node).storage.get()

            storage_list = []
            for storage in storages:
                storage_info = StorageInfo(
                    storage=storage['storage'],
                    type=storage.get('type', 'unknown'),
                    content=storage.get('content', ''),
                    active=storage.get('active', 0) == 1,
                    enabled=storage.get('enabled', 0) == 1,
                    avail=storage.get('avail'),
                    total=storage.get('total'),
                    used=storage.get('used')
                )
                storage_list.append(storage_info)

            return storage_list

        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to list storages: {str(e)}")

    def list_iso_images(self, node: Optional[str] = None) -> List[ISOInfo]:
        """
        List available ISO images

        Args:
            node: Optional node name

        Returns:
            List of ISOInfo objects
        """
        try:
            target_node = node or self.settings.default_node

            # Get all storages that support ISO content
            storages = self.proxmox.proxmox.nodes(target_node).storage.get()

            iso_list = []
            for storage in storages:
                storage_id = storage['storage']
                content = storage.get('content', '')

                # Check if storage supports ISO content
                if 'iso' in content or 'vztmpl' in content:
                    try:
                        # List content from this storage
                        contents = self.proxmox.proxmox.nodes(target_node).storage(storage_id).content.get()

                        for item in contents:
                            # Filter ISO files
                            if item.get('content') == 'iso':
                                iso_info = ISOInfo(
                                    volid=item['volid'],
                                    size=item.get('size', 0),
                                    format=item.get('format', 'iso'),
                                    content='iso'
                                )
                                iso_list.append(iso_info)
                    except Exception:
                        # Skip storages that fail to list
                        continue

            return iso_list

        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to list ISO images: {str(e)}")

    def list_network_bridges(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available network bridges

        Args:
            node: Optional node name

        Returns:
            List of network bridge information
        """
        try:
            target_node = node or self.settings.default_node

            # Get network configuration
            networks = self.proxmox.proxmox.nodes(target_node).network.get()

            bridges = []
            for network in networks:
                if network.get('type') == 'bridge':
                    bridges.append({
                        'iface': network['iface'],
                        'type': network['type'],
                        'active': network.get('active', 0) == 1,
                        'autostart': network.get('autostart', 0) == 1
                    })

            return bridges

        except Exception as e:
            raise ProxmoxConnectionError(f"Failed to list network bridges: {str(e)}")

    def get_available_resources(self, node: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all available resources at once

        Args:
            node: Optional node name

        Returns:
            Dictionary with storages, ISOs, and networks
        """
        return {
            'storages': self.list_storages(node),
            'iso_images': self.list_iso_images(node),
            'network_bridges': self.list_network_bridges(node)
        }
