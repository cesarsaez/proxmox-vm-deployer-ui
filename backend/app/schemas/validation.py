"""Pydantic schemas for validation operations"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ValidationCheck(BaseModel):
    """Individual validation check result"""
    passed: bool = Field(..., description="Whether the check passed")
    message: Optional[str] = Field(None, description="Check message or error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional check details")
    required: bool = Field(default=True, description="Whether this check is required")


class ValidationResult(BaseModel):
    """Complete validation result for a VM"""
    vmid: int = Field(..., description="VM ID")
    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    ip_address: Optional[str] = Field(None, description="VM IP address")
    checks: Dict[str, ValidationCheck] = Field(..., description="Individual check results")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")
    message: Optional[str] = Field(None, description="Overall validation message")


class ValidationRequest(BaseModel):
    """Request to validate a VM"""
    vmid: int = Field(..., description="VM ID to validate", gt=0)
    os_type: str = Field(default="linux", description="OS type: linux or windows")
    timeout: Optional[int] = Field(None, description="Validation timeout in seconds")
