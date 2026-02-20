"""Resource API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.services.resource_service import ResourceService
from app.dependencies import get_resource_service
from app.schemas.resource import StorageInfo, ISOInfo
from app.core.exceptions import ProxmoxConnectionError

router = APIRouter(tags=["Resources"])


@router.get("/storages", response_model=List[StorageInfo])
async def list_storages(
    resource_service: ResourceService = Depends(get_resource_service)
):
    """
    List available storage pools

    Returns a list of all storage pools available on the default Proxmox node
    """
    try:
        storages = resource_service.list_storages()
        return storages
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list storages: {str(e)}"
        )


@router.get("/iso-images", response_model=List[ISOInfo])
async def list_iso_images(
    resource_service: ResourceService = Depends(get_resource_service)
):
    """
    List available ISO images

    Returns a list of all ISO images available across all storages
    """
    try:
        iso_images = resource_service.list_iso_images()
        return iso_images
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list ISO images: {str(e)}"
        )


@router.get("/network-bridges")
async def list_network_bridges(
    resource_service: ResourceService = Depends(get_resource_service)
):
    """
    List available network bridges

    Returns a list of all network bridges on the default node
    """
    try:
        bridges = resource_service.list_network_bridges()
        return bridges
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list network bridges: {str(e)}"
        )


@router.get("/all")
async def get_all_resources(
    resource_service: ResourceService = Depends(get_resource_service)
):
    """
    Get all available resources at once

    Returns storages, ISO images, and network bridges in a single response
    """
    try:
        resources = resource_service.get_available_resources()
        return resources
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resources: {str(e)}"
        )
