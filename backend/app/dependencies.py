"""Dependency injection for FastAPI"""
from functools import lru_cache
from app.config import get_settings, Settings
from app.services.proxmox_service import ProxmoxService
from app.services.template_service import TemplateService
from app.services.validation_service import ValidationService
from app.services.vm_service import VMService
from app.services.resource_service import ResourceService


def get_proxmox_service() -> ProxmoxService:
    """Get Proxmox service instance"""
    settings = get_settings()
    return ProxmoxService(settings)


def get_template_service() -> TemplateService:
    """Get Template service instance"""
    settings = get_settings()
    proxmox_service = get_proxmox_service()
    return TemplateService(proxmox_service, settings)


def get_validation_service() -> ValidationService:
    """Get Validation service instance"""
    settings = get_settings()
    proxmox_service = get_proxmox_service()
    return ValidationService(proxmox_service, settings)


def get_vm_service() -> VMService:
    """Get VM service instance"""
    settings = get_settings()
    proxmox_service = get_proxmox_service()
    return VMService(proxmox_service, settings)


def get_resource_service() -> ResourceService:
    """Get Resource service instance"""
    settings = get_settings()
    proxmox_service = get_proxmox_service()
    return ResourceService(proxmox_service, settings)
