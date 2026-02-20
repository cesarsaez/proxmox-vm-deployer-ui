"""FastAPI application entry point"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import get_settings
from app.api.v1.router import api_router
from app.core.exceptions import (
    ProxmoxConnectionError,
    VMCreationError,
    VMCloneError,
    VMNotFoundError,
    TemplateNotFoundError,
    InvalidVMIDError,
    ValidationError as CustomValidationError
)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Proxmox VM Deployer API",
    version="1.0.0",
    description="API for deploying VMs on Proxmox via templates and direct creation",
    docs_url="/docs",
    redoc_url=None,  # We'll create a custom ReDoc endpoint
    openapi_url="/api/v1/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ProxmoxConnectionError)
async def proxmox_connection_handler(request: Request, exc: ProxmoxConnectionError):
    """Handle Proxmox connection errors"""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "ProxmoxConnectionError",
            "message": str(exc),
            "details": "Unable to connect to Proxmox API",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(VMCreationError)
async def vm_creation_handler(request: Request, exc: VMCreationError):
    """Handle VM creation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "VMCreationError",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(VMCloneError)
async def vm_clone_handler(request: Request, exc: VMCloneError):
    """Handle VM clone errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "VMCloneError",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(VMNotFoundError)
async def vm_not_found_handler(request: Request, exc: VMNotFoundError):
    """Handle VM not found errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "VMNotFoundError",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(TemplateNotFoundError)
async def template_not_found_handler(request: Request, exc: TemplateNotFoundError):
    """Handle template not found errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "TemplateNotFoundError",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(InvalidVMIDError)
async def invalid_vmid_handler(request: Request, exc: InvalidVMIDError):
    """Handle invalid VMID errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "InvalidVMIDError",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(CustomValidationError)
async def validation_error_handler(request: Request, exc: CustomValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Custom ReDoc endpoint with explicit HTML
@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def redoc_html():
    """Custom ReDoc documentation page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url="/api/v1/openapi.json"></redoc>
        <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Proxmox VM Deployer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
