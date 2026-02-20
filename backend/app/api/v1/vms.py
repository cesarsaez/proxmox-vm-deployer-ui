"""VM API endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.services.vm_service import VMService
from app.services.validation_service import ValidationService
from app.services.audit_service import get_audit_logger
from app.dependencies import get_vm_service, get_validation_service, get_settings
from app.schemas.vm import (
    VMInfo,
    VMCreateRequest,
    VMCreateResponse,
    VMStatus,
    BatchVMCreateResponse
)
from app.schemas.validation import ValidationResult
from app.core.exceptions import (
    VMCreationError,
    InvalidVMIDError,
    VMNotFoundError,
    ProxmoxConnectionError
)

router = APIRouter(tags=["VMs"])


@router.post("/create", response_model=VMCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(
    request: VMCreateRequest,
    vm_service: VMService = Depends(get_vm_service)
):
    """
    Create a new VM from scratch

    Creates a new VM with the specified configuration including CPU, memory, disk, etc.

    Example request body:
    ```json
    {
        "name": "my-server",
        "cores": 4,
        "memory": 8192,
        "disk_size": 50,
        "os_type": "linux",
        "start_on_creation": false
    }
    ```
    """
    try:
        # Validate configuration
        validation = vm_service.validate_vm_config(request)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid VM configuration", "issues": validation["issues"]}
            )

        # Create VM
        result = vm_service.create_vm(request)
        return result

    except InvalidVMIDError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except VMCreationError as e:
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
            detail=f"Failed to create VM: {str(e)}"
        )


@router.post("/batch-create", response_model=BatchVMCreateResponse, status_code=status.HTTP_201_CREATED)
async def batch_create_vms(
    requests: List[VMCreateRequest],
    vm_service: VMService = Depends(get_vm_service)
):
    """
    Create multiple VMs from scratch in batch

    Creates multiple VMs with the specified configurations. Each VM is created sequentially.
    Partial failures are allowed - successful creations are reported along with any errors.

    Example request body:
    ```json
    [
        {
            "name": "server-01",
            "cores": 4,
            "memory": 8192,
            "disk_size": 50,
            "os_type": "linux"
        },
        {
            "name": "server-02",
            "cores": 4,
            "memory": 8192,
            "disk_size": 50,
            "os_type": "linux"
        }
    ]
    ```
    """
    results = []
    successful = 0
    failed = 0

    for request in requests:
        try:
            # Validate configuration
            validation = vm_service.validate_vm_config(request)
            if not validation["valid"]:
                error_result = VMCreateResponse(
                    vmid=0,
                    name=request.name,
                    node="",
                    status="failed",
                    message=f"Invalid configuration: {', '.join(validation['issues'])}",
                    task_id=None
                )
                results.append(error_result)
                failed += 1
                continue

            # Create VM
            result = vm_service.create_vm(request)
            results.append(result)
            successful += 1

        except (InvalidVMIDError, VMCreationError, ProxmoxConnectionError) as e:
            # Create error response for this VM
            error_result = VMCreateResponse(
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
            error_result = VMCreateResponse(
                vmid=0,
                name=request.name,
                node="",
                status="failed",
                message=f"Unexpected error: {str(e)}",
                task_id=None
            )
            results.append(error_result)
            failed += 1

    response = BatchVMCreateResponse(
        results=results,
        total=len(requests),
        successful=successful,
        failed=failed
    )

    # Audit log: batch operation summary
    audit_logger = get_audit_logger()
    settings = get_settings()
    audit_logger.log_batch_operation(
        operation_type='batch_create',
        username=settings.proxmox_user,
        total=len(requests),
        successful=successful,
        failed=failed,
        requests=[req.dict() for req in requests],
        results=[res.dict() for res in results]
    )

    return response


@router.get("/{vmid}", response_model=VMInfo)
async def get_vm_info(
    vmid: int,
    vm_service: VMService = Depends(get_vm_service)
):
    """
    Get VM information

    Returns detailed information about a specific VM including configuration and status

    Args:
        vmid: VM ID
    """
    try:
        vm_info = vm_service.get_vm_info(vmid)
        return vm_info

    except VMNotFoundError as e:
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
            detail=f"Failed to get VM info: {str(e)}"
        )


@router.get("/{vmid}/status", response_model=VMStatus)
async def get_vm_status(
    vmid: int,
    vm_service: VMService = Depends(get_vm_service)
):
    """
    Get VM status

    Returns current status information including uptime, CPU, and memory usage

    Args:
        vmid: VM ID
    """
    try:
        vm_status = vm_service.get_vm_status(vmid)
        return vm_status

    except VMNotFoundError as e:
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
            detail=f"Failed to get VM status: {str(e)}"
        )


@router.post("/{vmid}/validate", response_model=ValidationResult)
async def validate_vm_deployment(
    vmid: int,
    os_type: str = "linux",
    validation_service: ValidationService = Depends(get_validation_service)
):
    """
    Run post-deployment validation on a VM

    Performs comprehensive validation including:
    - Proxmox health status check
    - IP address assignment verification
    - Port connectivity testing (SSH for Linux, RDP for Windows)

    Args:
        vmid: VM ID to validate
        os_type: Operating system type ("linux" or "windows")

    Returns detailed validation results with individual check status
    """
    try:
        result = await validation_service.validate_vm(vmid, os_type)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate VM: {str(e)}"
        )
