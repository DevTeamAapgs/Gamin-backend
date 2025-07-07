from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.core.enums import PlayerType

class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")

class PaginationResponse(BaseModel):
    """Pagination metadata for list responses"""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class ListResponse(BaseModel):
    """Generic list response with pagination"""
    items: List[Any] = Field(..., description="List of items")
    pagination: PaginationResponse = Field(..., description="Pagination metadata")

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = Field(False, description="Operation failed")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class TokenResponse(BaseModel):
    """Token response for authentication"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class AdminResponse(BaseModel):
    """Admin user response"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_admin: bool = Field(..., description="Whether user is an admin")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

class StatusUpdateRequest(BaseModel):
    """Request model for status updates"""
    status: str = Field(..., description="New status value")

class SearchFilterRequest(BaseModel):
    """Common search and filter parameters"""
    search: Optional[str] = Field(None, description="Search term")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc/desc)") 