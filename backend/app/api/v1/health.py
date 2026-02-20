"""Health check endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.config import get_settings, Settings
from app.services.proxmox_service import ProxmoxService
from app.dependencies import get_proxmox_service
from app.core.exceptions import ProxmoxConnectionError

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class ProxmoxStatusResponse(BaseModel):
    """Proxmox connection status response"""
    connected: bool
    proxmox_host: str
    proxmox_version: str | None = None
    nodes_count: int | None = None
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint

    Returns API status and timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/proxmox/status", response_model=ProxmoxStatusResponse)
async def proxmox_status(
    proxmox: ProxmoxService = Depends(get_proxmox_service),
    settings: Settings = Depends(get_settings)
):
    """
    Check Proxmox API connection status

    Returns connection status, version, and node count
    """
    try:
        # Try to get version
        version_info = proxmox.get_version()
        proxmox_version = version_info.get('version', 'unknown')

        # Try to list nodes
        nodes = proxmox.list_nodes()
        nodes_count = len(nodes)

        return ProxmoxStatusResponse(
            connected=True,
            proxmox_host=settings.proxmox_host,
            proxmox_version=proxmox_version,
            nodes_count=nodes_count,
            message="Connected to Proxmox successfully"
        )

    except ProxmoxConnectionError as e:
        return ProxmoxStatusResponse(
            connected=False,
            proxmox_host=settings.proxmox_host,
            message=f"Failed to connect to Proxmox: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking Proxmox status: {str(e)}"
        )
