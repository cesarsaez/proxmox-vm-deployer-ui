"""Pydantic schemas for VM operations"""
from typing import Optional
from pydantic import BaseModel, Field


class VMInfo(BaseModel):
    """VM information"""
    vmid: int = Field(..., description="VM ID")
    name: str = Field(..., description="VM name")
    node: str = Field(..., description="Node where VM resides")
    status: str = Field(..., description="VM status")
    cores: Optional[int] = Field(None, description="Number of CPU cores")
    memory: Optional[int] = Field(None, description="Memory in MB")
    uptime: Optional[int] = Field(None, description="Uptime in seconds")


class VMCreateRequest(BaseModel):
    """Request to create a new VM"""
    vmid: Optional[int] = Field(None, description="VM ID (auto-assigned if not provided)", gt=0)
    name: str = Field(..., description="VM name", min_length=1, max_length=255)
    node: Optional[str] = Field(None, description="Target node (uses default if not provided)")
    cores: int = Field(default=2, description="Number of CPU cores", gt=0, le=256)
    sockets: int = Field(default=1, description="Number of CPU sockets", gt=0, le=4)
    cpu_type: str = Field(default="host", description="CPU type (host, kvm64, qemu64)")
    memory: int = Field(default=2048, description="Memory in MB", gt=0)
    disk_size: int = Field(default=20, description="Disk size in GB", gt=0)
    storage: Optional[str] = Field(None, description="Storage pool (uses default if not provided)")
    network_bridge: Optional[str] = Field(None, description="Network bridge (uses default if not provided)")
    network_model: str = Field(default="virtio", description="Network card model (virtio, e1000, rtl8139)")
    os_type: str = Field(default="linux", description="OS type: linux or windows")
    bios: str = Field(default="seabios", description="BIOS type (seabios or ovmf)")
    machine: str = Field(default="q35", description="Machine type (q35 or i440fx)")
    iso: Optional[str] = Field(None, description="ISO image (e.g., local:iso/ubuntu.iso)")
    virtio_iso: Optional[str] = Field(None, description="VirtIO drivers ISO for Windows (attached as second CD/DVD)")
    start_on_creation: bool = Field(default=False, description="Start VM after creation")
    enable_guest_agent: bool = Field(default=False, description="Enable QEMU guest agent")
    description: Optional[str] = Field(None, description="VM description")
    tags: Optional[list[str]] = Field(None, description="List of tags for the VM")


class VMCreateResponse(BaseModel):
    """Response after creating a VM"""
    vmid: int = Field(..., description="VM ID")
    name: str = Field(..., description="VM name")
    node: str = Field(..., description="Node where VM is created")
    status: str = Field(..., description="Creation status")
    message: str = Field(..., description="Status message")
    task_id: Optional[str] = Field(None, description="Proxmox task ID (UPID)")


class VMStatus(BaseModel):
    """VM status information"""
    vmid: int = Field(..., description="VM ID")
    node: str = Field(..., description="Node name")
    status: str = Field(..., description="VM status (running, stopped, etc.)")
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    cpu: Optional[float] = Field(None, description="CPU usage")
    memory: Optional[int] = Field(None, description="Current memory usage in bytes")
    maxmem: Optional[int] = Field(None, description="Maximum memory in bytes")


class BatchVMCreateResponse(BaseModel):
    """Response after batch creating VMs"""
    results: list[VMCreateResponse] = Field(..., description="List of VM creation results")
    total: int = Field(..., description="Total number of VMs requested")
    successful: int = Field(..., description="Number of successful creations")
    failed: int = Field(..., description="Number of failed creations")
