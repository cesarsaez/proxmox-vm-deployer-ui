"""Custom exception classes"""


class ProxmoxAPIException(Exception):
    """Base exception for Proxmox API errors"""
    pass


class ProxmoxConnectionError(ProxmoxAPIException):
    """Connection to Proxmox failed"""
    pass


class VMCreationError(ProxmoxAPIException):
    """VM creation failed"""
    pass


class VMCloneError(ProxmoxAPIException):
    """VM cloning failed"""
    pass


class VMNotFoundError(ProxmoxAPIException):
    """VM not found"""
    pass


class ValidationError(ProxmoxAPIException):
    """Post-deployment validation failed"""
    pass


class ResourceNotFoundError(ProxmoxAPIException):
    """Requested resource not found"""
    pass


class ConfigurationError(Exception):
    """Configuration error"""
    pass


class TemplateNotFoundError(ProxmoxAPIException):
    """Template not found"""
    pass


class InvalidVMIDError(ProxmoxAPIException):
    """Invalid VM ID"""
    pass
