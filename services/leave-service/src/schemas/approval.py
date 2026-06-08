"""Approval and rejection schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class ApprovalRequest(BaseModel):
    """Request schema for approving a leave request."""
    
    comment: Optional[str] = Field(None, max_length=500, description="Optional approval comment")


class RejectionRequest(BaseModel):
    """Request schema for rejecting a leave request."""
    
    comment: str = Field(min_length=1, max_length=500, description="Mandatory rejection reason")
