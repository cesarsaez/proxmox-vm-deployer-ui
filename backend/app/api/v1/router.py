"""Main API v1 router"""
from fastapi import APIRouter

from app.api.v1 import health, templates, vms, resources

# Create main v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(vms.router, prefix="/vms", tags=["VMs"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
