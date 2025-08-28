"""Data models for the ShowAds data connector."""

import re
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field, validator


class Customer(BaseModel):
    """Customer data model with validation."""

    Name: str = Field(..., description="Customer name")
    Age: int = Field(..., description="Customer age")
    Cookie: str = Field(..., description="Customer cookie (UUID format)")
    Banner_id: int = Field(..., description="Banner ID (0-99)")

    @validator('Name')
    def validate_name(cls, v: str) -> str:
        """Validate that name contains only letters and spaces."""
        if not re.match(r'^[A-Za-z\s]+$', v.strip()):
            raise ValueError('Name must contain only letters and spaces')
        return v.strip()

    @validator('Cookie')
    def validate_cookie(cls, v: str) -> str:
        """Validate that cookie is in UUID format."""
        try:
            UUID(v)
        except ValueError:
            raise ValueError('Cookie must be in UUID format')
        return v

    @validator('Banner_id')
    def validate_banner_id(cls, v: int) -> int:
        """Validate that Banner_id is between 0 and 99."""
        if not 0 <= v <= 99:
            raise ValueError('Banner_id must be between 0 and 99')
        return v

    def validate_age(self, min_age: int, max_age: int) -> None:
        """Validate age against configurable limits."""
        if not min_age <= self.Age <= max_age:
            raise ValueError(f'Age must be between {min_age} and {max_age}')


class AuthRequest(BaseModel):
    """Authentication request model."""

    ProjectKey: str


class AuthResponse(BaseModel):
    """Authentication response model."""

    AccessToken: str


class BannerRequest(BaseModel):
    """Single banner request model."""

    VisitorCookie: str
    BannerId: int


class BulkBannerRequest(BaseModel):
    """Bulk banner request model."""

    Data: List[BannerRequest]
