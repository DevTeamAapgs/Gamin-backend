from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Literal
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
    data: List[Any] = Field(..., description="List of items")
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
    status: Optional[int] = Field(None, description="User status (1=active, 0=inactive)")
    fk_role_id: Optional[str] = Field(None, description="Role ID")
    player_prefix: Optional[str] = Field(None, description="Player prefix")
    wallet_address: Optional[str] = Field(None, description="Wallet address")
    profile_photo: Optional[Dict[str, str | float]] = Field(None, description="Profile photo information")
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

class AdminCreateRequest(BaseModel):
    """Request model for creating admin users"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")
    fk_role_id: str = Field(..., description="Role ID")
    profile_photo: Optional[Dict[str, str | float]] = Field(None, description="Profile photo information with uploadfilename, uploadurl, and filesize_kb")

class AdminGetRequest(BaseModel):
    """Request model for getting admin by ID"""
    admin_id: str = Field(..., description="Admin ID to retrieve")

class AdminUpdateRequest(BaseModel):
    """Request model for updating admin users"""
    id: str = Field(..., description="Admin ID to update")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[str] = Field(None, description="Email address")
    password: Optional[str] = Field(None, min_length=6, description="Password (minimum 6 characters)")
    fk_role_id: Optional[str] = Field(None, description="Role ID")
    profile_photo: Optional[Dict[str, str | float]] = Field(None, description="Profile photo information")

class NumericStatusUpdateRequest(BaseModel):
    """Request model for numeric status updates (0=inactive, 1=active)"""
    status: Literal[0, 1] = Field(..., description="Status: 0=inactive, 1=active")

class AdminStatusUpdateRequest(NumericStatusUpdateRequest):
    """Request model for admin status updates"""
    id: str = Field(..., description="Admin ID")

class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password - send OTP"""
    email: str = Field(..., description="Email address")

class VerifyOTPRequest(BaseModel):
    """Request model for OTP verification"""
    email: str = Field(..., description="Email address")
    otp: str = Field(..., description="6-digit OTP")

class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="Email address")
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")
    reset_token: str = Field(..., description="Password reset token") 