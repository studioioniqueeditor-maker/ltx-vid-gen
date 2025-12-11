"""
Configuration Management with Pydantic
Loads and validates environment variables with type safety
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator, field_validator
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration with environment variable loading and validation"""

    # API Configuration
    API_KEYS: str = Field(..., description="Comma-separated API keys")
    ALLOWED_ORIGINS: str = Field(
        default="https://localhost:3000",
        description="Comma-separated CORS allowed origins"
    )

    # Oracle Object Storage
    OCI_NAMESPACE: str = Field(..., description="Oracle Cloud namespace")
    OCI_BUCKET_NAME: str = Field(default="ltx-video-outputs")
    OCI_REGION: str = Field(default="us-ashburn-1")
    OCI_USER_OCID: str = Field(..., description="Oracle Cloud user OCID")
    OCI_FINGERPRINT: str = Field(..., description="API key fingerprint")
    OCI_TENANCY_OCID: str = Field(..., description="Tenancy OCID")
    OCI_PRIVATE_KEY_PATH: str = Field(..., description="Private key content or path")

    # Oracle Database
    ORACLE_DB_USER: str = Field(..., description="Database username")
    ORACLE_DB_PASSWORD: str = Field(..., description="Database password")
    ORACLE_DB_DSN: str = Field(..., description="Database connection string")
    ORACLE_WALLET_DIR: str = Field(..., description="Database connection string")

    # Webhook Configuration
    WEBHOOK_TIMEOUT: int = Field(default=30, ge=5, le=300)
    WEBHOOK_MAX_RETRIES: int = Field(default=3, ge=1, le=10)
    WEBHOOK_SECRET: str = Field(
        default="change-me-in-production",
        min_length=16,
        description="Secret for HMAC signature"
    )

    # File Upload Limits
    MAX_FILE_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_IMAGE_TYPES: str = Field(
        default="image/jpeg,image/png,image/webp"
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=10, ge=1, le=1000)

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

    # Optional features
    ENABLE_METRICS: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    @field_validator('API_KEYS')
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys and validate"""
        if isinstance(v, str):
            keys = [k.strip() for k in v.split(',') if k.strip()]
            if not keys:
                raise ValueError("At least one API key is required")
            # Validate minimum key length
            for key in keys:
                if len(key) < 16:
                    raise ValueError(f"API key too short (minimum 16 characters): {key[:4]}...")
            return keys
        return v

    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def parse_origins(cls, v):
        """Parse comma-separated origins"""
        if isinstance(v, str):
            origins = [o.strip() for o in v.split(',') if o.strip()]
            return origins if origins else ["*"]
        return v

    @field_validator('ALLOWED_IMAGE_TYPES')
    @classmethod
    def parse_image_types(cls, v):
        """Parse comma-separated MIME types"""
        if isinstance(v, str):
            types = [t.strip() for t in v.split(',') if t.strip()]
            return types if types else ["image/jpeg", "image/png"]
        return v

    @field_validator('DEFAULT_WIDTH', 'DEFAULT_HEIGHT', 'MAX_WIDTH', 'MAX_HEIGHT')
    @classmethod
    def validate_dimensions(cls, v, info):
        """Ensure dimensions are multiples of 8 (model requirement)"""
        if v % 8 != 0:
            raise ValueError(f"{info.field_name} must be a multiple of 8, got {v}")
        return v

    def get_api_key_list(self) -> List[str]:
        """Get list of API keys"""
        if isinstance(self.API_KEYS, list):
            return self.API_KEYS
        return [k.strip() for k in self.API_KEYS.split(',') if k.strip()]

    def get_allowed_origins(self) -> List[str]:
        """Get list of allowed origins"""
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(',') if o.strip()]

    def get_allowed_image_types(self) -> List[str]:
        """Get list of allowed MIME types"""
        if isinstance(self.ALLOWED_IMAGE_TYPES, list):
            return self.ALLOWED_IMAGE_TYPES
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(',') if t.strip()]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # Allow extra fields for forward compatibility
        extra = 'ignore'


@field_validator('OCI_PRIVATE_KEY')
@classmethod
def load_private_key(cls, v):
        """Load private key from file if it's a path, otherwise use as-is"""
        if v.startswith('/') or v.startswith('./'):
            # It's a file path
            try:
                with open(v, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                raise ValueError(f"Private key file not found: {v}")
        return v

# Global settings instance
# This will be imported throughout the application
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

    # Check API keys
    api_keys = settings.get_api_key_list()
    if not api_keys:
        errors.append("No API keys configured")

    # Check Oracle Cloud config
    required_oci = ['OCI_NAMESPACE', 'OCI_USER_OCID', 'OCI_FINGERPRINT', 'OCI_TENANCY_OCID']
    for key in required_oci:
        if not getattr(settings, key, None):
            errors.append(f"Missing Oracle Cloud config: {key}")

    # Check database config
    if not all([settings.ORACLE_DB_USER, settings.ORACLE_DB_PASSWORD, settings.ORACLE_DB_DSN]):
        errors.append("Missing Oracle Database configuration")

    # Check webhook secret
    if settings.WEBHOOK_SECRET == "change-me-in-production":
        errors.append("WARNING: Using default webhook secret - change in production!")

    if errors:
        print("\n⚠️  Configuration Validation Warnings:")
        for error in errors:
            print(f"  - {error}")
        print()

    return len(errors) == 0


# Run validation on import (but don't fail, just warn)
validate_config()
