"""Configuration management using Pydantic Settings"""
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Proxmox API Configuration
    proxmox_host: str = Field(..., description="Proxmox server hostname or IP")
    proxmox_port: int = Field(default=8006, description="Proxmox API port")
    proxmox_user: str = Field(..., description="Proxmox username (e.g., root@pam)")
    proxmox_password: str = Field(..., description="Proxmox password")
    proxmox_verify_ssl: bool = Field(default=False, description="Verify SSL certificates")

    # Default Cluster Configuration
    default_node: str = Field(..., description="Default Proxmox node")
    default_storage: str = Field(default="local-lvm", description="Default storage pool")
    default_network_bridge: str = Field(default="vmbr0", description="Default network bridge")

    # Template Configuration (optional)
    linux_template_vmid: int | None = Field(default=None, description="Linux template VMID")
    windows_template_vmid: int | None = Field(default=None, description="Windows template VMID")

    # VM ID Range
    vmid_min: int = Field(default=150, description="Minimum VM ID")
    vmid_max: int = Field(default=999, description="Maximum VM ID")

    # Validation Configuration
    validation_timeout: int = Field(default=300, description="Validation timeout in seconds")
    validation_ssh_port: int = Field(default=22, description="SSH port for validation")
    validation_rdp_port: int = Field(default=3389, description="RDP port for validation")
    validation_max_retries: int = Field(default=10, description="Max retries for validation")
    validation_retry_interval: int = Field(default=15, description="Retry interval in seconds")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: str = Field(default="http://localhost:3001", description="CORS allowed origins (comma-separated)")

    # Feature Flags
    enable_vm_deletion: bool = Field(default=False, description="Allow VM deletion via API")
    enable_auto_start: bool = Field(default=True, description="Allow auto-start after creation")
    require_post_validation: bool = Field(default=True, description="Require post-deployment validation")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
