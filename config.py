"""
Configuration Management - Simplified
Loads and validates environment variables for RunPod serverless
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration with environment variable loading and validation"""

    # Oracle Object Storage (REQUIRED)
    OCI_NAMESPACE: str = Field(..., description="Oracle Cloud namespace")
    OCI_BUCKET_NAME: str = Field(default="ltx-video-outputs")
    OCI_REGION: str = Field(default="us-ashburn-1")
    OCI_USER_OCID: str = Field(..., description="Oracle Cloud user OCID")
    OCI_FINGERPRINT: str = Field(..., description="API key fingerprint")
    OCI_TENANCY_OCID: str = Field(..., description="Tenancy OCID")
    OCI_PRIVATE_KEY_PATH: str = Field(..., description="Path to private key file")

    # Model Configuration
    MODEL_PATH: str = Field(default="/workspace/models/ltxv-13b-distilled")
    OUTPUT_DIR: str = Field(default="/tmp/outputs")
    UPLOAD_DIR: str = Field(default="/tmp/uploads")

    # Video Generation Defaults
    DEFAULT_WIDTH: int = Field(default=1280, ge=256, le=1920)
    DEFAULT_HEIGHT: int = Field(default=720, ge=256, le=1080)
    DEFAULT_NUM_FRAMES: int = Field(default=121, ge=25, le=257)
    DEFAULT_NUM_STEPS: int = Field(default=8, ge=1, le=50)
    DEFAULT_FPS: int = Field(default=24, ge=1, le=60)

    # Limits (Security)
    MAX_WIDTH: int = Field(default=1920, ge=256, le=3840)
    MAX_HEIGHT: int = Field(default=1080, ge=256, le=2160)
    MAX_FRAMES: int = Field(default=257, ge=25, le=500)
    MAX_STEPS: int = Field(default=50, ge=1, le=100)

    # File Upload Limits
    MAX_FILE_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_IMAGE_TYPES: str = Field(
        default="image/jpeg,image/png,image/webp"
    )

    # Optional features
    LOG_LEVEL: str = Field(default="INFO")

    @field_validator('DEFAULT_WIDTH', 'DEFAULT_HEIGHT', 'MAX_WIDTH', 'MAX_HEIGHT')
    @classmethod
    def validate_dimensions(cls, v, info):
        """Ensure dimensions are multiples of 8 (model requirement)"""
        if v % 8 != 0:
            raise ValueError(f"{info.field_name} must be a multiple of 8, got {v}")
        return v

    def get_allowed_image_types(self) -> List[str]:
        """Get list of allowed MIME types"""
        if isinstance(self.ALLOWED_IMAGE_TYPES, list):
            return self.ALLOWED_IMAGE_TYPES
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(',') if t.strip()]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'ignore'


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"ERROR: Failed to load settings: {e}")
    print("Please check your .env file or environment variables")
    raise


# Validate configuration on import
def validate_config():
    """Validate critical configuration"""
    errors = []

    # Check Oracle Cloud config
    required_oci = ['OCI_NAMESPACE', 'OCI_USER_OCID', 'OCI_FINGERPRINT', 
                    'OCI_TENANCY_OCID', 'OCI_PRIVATE_KEY_PATH']
    for key in required_oci:
        if not getattr(settings, key, None):
            errors.append(f"Missing Oracle Cloud config: {key}")

    if errors:
        print("\n⚠️  Configuration Validation Warnings:")
        for error in errors:
            print(f"  - {error}")
        print()

    return len(errors) == 0


# Run validation on import (but don't fail, just warn)
validate_config()
