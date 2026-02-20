"""Template API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.services.template_service import TemplateService
from app.services.audit_service import get_audit_logger
from app.dependencies import get_template_service, get_settings
from app.schemas.template import (
    TemplateInfo,
    TemplateListResponse,
    CloneRequest,
    CloneResponse,
    BatchCloneResponse
)
from app.core.exceptions import (
    TemplateNotFoundError,
    VMCloneError,
    InvalidVMIDError,
    ProxmoxConnectionError
)

router = APIRouter(tags=["Templates"])


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    template_service: TemplateService = Depends(get_template_service)
):
    """
    List all available VM templates

    Returns a list of all templates across all nodes in the Proxmox cluster
    """
    try:
        templates = template_service.list_templates()
        return TemplateListResponse(
            templates=templates,
            count=len(templates)
        )
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/{vmid}", response_model=TemplateInfo)
async def get_template_details(
    vmid: int,
    template_service: TemplateService = Depends(get_template_service)
):
    """
    Get detailed information about a specific template

    Args:
        vmid: Template VM ID

    Returns template configuration including CPU, memory, disk size, etc.
    """
    try:
        template = template_service.get_template_details(vmid)
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template details: {str(e)}"
        )


@router.post("/clone", response_model=CloneResponse, status_code=status.HTTP_201_CREATED)
async def clone_template(
    request: CloneRequest,
    template_service: TemplateService = Depends(get_template_service)
):
    """
    Clone a VM from a template

    Creates a new VM by cloning from an existing template. Supports:
    - Full or linked clones
    - Custom CPU and memory allocation
    - Auto-assignment of VM ID if not provided
    - Optional auto-start after cloning

    Example request body:
    ```json
    {
        "source_vmid": 9000,
        "name": "my-new-server",
        "full_clone": true,
        "cores": 4,
        "memory": 8192,
        "start_after_clone": true
    }
    ```
    """
    try:
        result = template_service.clone_from_template(request)
        return result
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidVMIDError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except VMCloneError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProxmoxConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone template: {str(e)}"
        )


@router.post("/batch-clone", response_model=BatchCloneResponse, status_code=status.HTTP_201_CREATED)
async def batch_clone_templates(
    requests: List[CloneRequest],
    template_service: TemplateService = Depends(get_template_service)
):
    """
    Clone multiple VMs from templates in batch

    Creates multiple VMs by cloning from templates. Each VM is cloned sequentially.
    Partial failures are allowed - successful clones are reported along with any errors.

    Example request body:
    ```json
    [
        {
            "source_vmid": 9000,
            "name": "server-01",
            "cores": 4,
            "memory": 8192
        },
        {
            "source_vmid": 9000,
            "name": "server-02",
            "cores": 4,
            "memory": 8192
        }
    ]
    ```
    """
    results = []
    successful = 0
    failed = 0

    for request in requests:
        try:
            result = template_service.clone_from_template(request)
            results.append(result)
            successful += 1
        except (TemplateNotFoundError, InvalidVMIDError, VMCloneError, ProxmoxConnectionError) as e:
            # Create error response for this VM
            error_result = CloneResponse(
                vmid=0,
                name=request.name,
                node="",
                status="failed",
                message=f"Failed: {str(e)}",
                task_id=None
            )
            results.append(error_result)
            failed += 1
        except Exception as e:
            # Unexpected error
            error_result = CloneResponse(
                vmid=0,
                name=request.name,
                node="",
                status="failed",
                message=f"Unexpected error: {str(e)}",
                task_id=None
            )
            results.append(error_result)
            failed += 1

    response = BatchCloneResponse(
        results=results,
        total=len(requests),
        successful=successful,
        failed=failed
    )

    # Audit log: batch operation summary
    audit_logger = get_audit_logger()
    settings = get_settings()
    audit_logger.log_batch_operation(
        operation_type='batch_clone',
        username=settings.proxmox_user,
        total=len(requests),
        successful=successful,
        failed=failed,
        requests=[req.dict() for req in requests],
        results=[res.dict() for res in results]
    )

    return response


@router.get("/{vmid}/validate", response_model=dict)
async def validate_template_exists(
    vmid: int,
    template_service: TemplateService = Depends(get_template_service)
):
    """
    Validate if a template exists

    Quick check to verify if a template ID is valid before attempting to clone

    Args:
        vmid: Template VM ID to validate
    """
    exists = template_service.validate_template_exists(vmid)

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {vmid} not found"
        )

    return {
        "vmid": vmid,
        "exists": True,
        "message": f"Template {vmid} exists and is valid"
    }
