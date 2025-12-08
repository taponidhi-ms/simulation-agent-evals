"""
Configuration schema for transcript downloader.

This module defines the Pydantic model for validating transcript downloader
configuration loaded from config.json.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TranscriptDownloaderConfig(BaseModel):
    """Configuration schema for transcript downloader."""
    
    # Required Dynamics 365 Organization Settings
    organization_url: str = Field(..., description="Dynamics 365 organization URL")
    tenant_id: str = Field(..., description="Azure AD tenant ID")
    workstream_id: str = Field(..., description="Workstream ID to fetch conversations from")
    max_conversations: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Maximum number of conversations to download"
    )
    
    # Optional Authentication Settings
    client_id: str = Field(
        default="51f81489-12ee-4a9e-aaae-a2591f45987d",
        description="Azure AD application client ID"
    )
    login_hint: str = Field(
        default="",
        description="Email hint for authentication login"
    )
    
    # API Settings
    api_version: str = Field(
        default="v9.2",
        description="Dataverse API version"
    )
    
    # Time Range Settings
    days_to_fetch: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Number of days to look back for conversations"
    )
    
    # Pagination and Size Settings
    page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Batch size for pagination"
    )
    max_content_size: int = Field(
        default=52428800,  # 50MB
        ge=1024,
        description="Maximum base64 content size in bytes"
    )
    
    # Optional Authentication Tokens
    access_token: str = Field(
        default="",
        description="Access token for direct authentication (bypasses interactive login)"
    )
    token_cache_path: str = Field(
        default=".token_cache.json",
        description="Path to token cache file"
    )
    
    # Output Settings
    output_dir: str = Field(
        default="transcript_downloader/output/",
        description="Output directory for downloaded transcripts"
    )
    
    @field_validator('organization_url')
    @classmethod
    def validate_org_url(cls, v: str) -> str:
        """Validate organization URL."""
        if not v.startswith('https://'):
            raise ValueError('Organization URL must start with https://')
        return v.rstrip('/')
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'
