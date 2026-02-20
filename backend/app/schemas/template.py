"""Pydantic schemas for template operations"""
from typing import Optional
from pydantic import BaseModel, Field


class TemplateInfo(BaseModel):
    """Template information"""
    vmid: int = Field(..., description="Template VM ID")
    name: str = Field(..., description="Template name")
    node: str = Field(..., description="Node where template resides")
    status: str = Field(..., description="Template status")
    template: bool = Field(..., description="Is template")
    cores: Optional[int] = Field(None, description="Number of CPU cores")
    memory: Optional[int] = Field(None, description="Memory in MB")
    disk_size: Optional[int] = Field(None, description="Disk size in bytes")
    disk_size_gb: Optional[str] = Field(None, description="Disk size formatted (e.g., '32 GB')")
    description: Optional[str] = Field(None, description="Template description")


class CloudInitUser(BaseModel):
    """Cloud-init user configuration"""
    username: str = Field(..., description="Username", min_length=1)
    password: Optional[str] = Field(None, description="Password for the user")
    ssh_keys: Optional[list[str]] = Field(None, description="List of SSH public keys")
    sudo: bool = Field(default=False, description="Grant sudo privileges")
    groups: Optional[list[str]] = Field(None, description="Additional groups for the user")


class CloudInitConfig(BaseModel):
    """Cloud-init configuration"""
    # Network configuration
    ipconfig: Optional[str] = Field(None, description="IP configuration (e.g., 'ip=192.168.1.100/24,gw=192.168.1.1')")
    nameserver: Optional[str] = Field(None, description="DNS nameserver")
    searchdomain: Optional[str] = Field(None, description="DNS search domain")

    # Users
    users: Optional[list[CloudInitUser]] = Field(None, description="List of users to create")

    # Packages
    packages: Optional[list[str]] = Field(None, description="List of packages to install")

    # Custom commands
    runcmd: Optional[list[str]] = Field(None, description="Commands to run on first boot")


class CloneRequest(BaseModel):
    """Request to clone a VM from template"""
    source_vmid: int = Field(..., description="Source template VM ID", gt=0)
    new_vmid: Optional[int] = Field(None, description="New VM ID (auto-assigned if not provided)")
    name: str = Field(..., description="Name for the new VM", min_length=1, max_length=255)
    node: Optional[str] = Field(None, description="Target node (uses default if not provided)")
    storage: Optional[str] = Field(None, description="Target storage (uses default if not provided)")
    full_clone: bool = Field(default=True, description="Full clone (True) or linked clone (False)")
    cores: Optional[int] = Field(None, description="Number of CPU cores to override", gt=0, le=256)
    memory: Optional[int] = Field(None, description="Memory in MB to override", gt=0)
    start_after_clone: bool = Field(default=False, description="Start VM after cloning")
    description: Optional[str] = Field(None, description="VM description")
    tags: Optional[list[str]] = Field(None, description="List of tags for the VM")

    # Cloud-init configuration
    cloudinit: Optional[CloudInitConfig] = Field(None, description="Cloud-init configuration for Ubuntu VMs")


class CloneResponse(BaseModel):
    """Response after cloning a VM"""
    vmid: int = Field(..., description="New VM ID")
    name: str = Field(..., description="VM name")
    node: str = Field(..., description="Node where VM is created")
    status: str = Field(..., description="Clone status")
    message: str = Field(..., description="Status message")
    task_id: Optional[str] = Field(None, description="Proxmox task ID (UPID)")


class TemplateListResponse(BaseModel):
    """Response containing list of templates"""
    templates: list[TemplateInfo] = Field(..., description="List of available templates")
    count: int = Field(..., description="Number of templates")


class BatchCloneResponse(BaseModel):
    """Response after batch cloning VMs"""
    results: list[CloneResponse] = Field(..., description="List of clone results")
    total: int = Field(..., description="Total number of VMs requested")
    successful: int = Field(..., description="Number of successful clones")
    failed: int = Field(..., description="Number of failed clones")
