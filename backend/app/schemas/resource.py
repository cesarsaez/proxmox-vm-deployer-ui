"""Pydantic schemas for resource operations"""
from typing import Optional, List
from pydantic import BaseModel, Field


class StorageInfo(BaseModel):
    """Storage information"""
    storage: str = Field(..., description="Storage ID")
    type: str = Field(..., description="Storage type")
    content: str = Field(..., description="Content types")
    active: bool = Field(..., description="Is active")
    enabled: bool = Field(..., description="Is enabled")
    avail: Optional[int] = Field(None, description="Available space in bytes")
    total: Optional[int] = Field(None, description="Total space in bytes")
    used: Optional[int] = Field(None, description="Used space in bytes")


class ISOInfo(BaseModel):
    """ISO image information"""
    volid: str = Field(..., description="Volume ID (e.g., local:iso/ubuntu.iso)")
    size: int = Field(..., description="Size in bytes")
    format: str = Field(..., description="Format (usually iso)")
    content: str = Field(default="iso", description="Content type")


class ResourceListResponse(BaseModel):
    """Generic resource list response"""
    items: List[dict] = Field(..., description="List of resources")
    count: int = Field(..., description="Number of items")
