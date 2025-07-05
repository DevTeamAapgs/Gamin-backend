from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from app.core.enums import Status, DeletionStatus
from app.models.base import PyObjectId

def add_audit_fields(
    data: Dict[str, Any], 
    created_by: Optional[PyObjectId] = None,
    updated_by: Optional[PyObjectId] = None
) -> Dict[str, Any]:
    """
    Add standardized audit fields to a document
    
    Args:
        data: Document data dictionary
        created_by: ID of user creating the document
        updated_by: ID of user updating the document
    
    Returns:
        Document with audit fields added
    """
    now = datetime.utcnow()
    
    # Add audit fields
    data.update({
        "created_on": now,
        "updated_on": now,
        "created_by": created_by,
        "updated_by": updated_by,
        "status": Status.ACTIVE,
        "dels": DeletionStatus.NOT_DELETED
    })
    
    return data

def update_audit_fields(
    data: Dict[str, Any], 
    updated_by: Optional[PyObjectId] = None
) -> Dict[str, Any]:
    """
    Update audit fields for document modification
    
    Args:
        data: Document data dictionary
        updated_by: ID of user updating the document
    
    Returns:
        Document with updated audit fields
    """
    data.update({
        "updated_on": datetime.utcnow(),
        "updated_by": updated_by
    })
    
    return data

def soft_delete_document(
    data: Dict[str, Any], 
    deleted_by: Optional[PyObjectId] = None
) -> Dict[str, Any]:
    """
    Soft delete a document by setting status and dels fields
    
    Args:
        data: Document data dictionary
        deleted_by: ID of user deleting the document
    
    Returns:
        Document with soft delete fields set
    """
    data.update({
        "status": Status.INACTIVE,
        "dels": DeletionStatus.DELETED,
        "updated_on": datetime.utcnow(),
        "updated_by": deleted_by
    })
    
    return data

def restore_document(
    data: Dict[str, Any], 
    restored_by: Optional[PyObjectId] = None
) -> Dict[str, Any]:
    """
    Restore a soft-deleted document
    
    Args:
        data: Document data dictionary
        restored_by: ID of user restoring the document
    
    Returns:
        Document with restore fields set
    """
    data.update({
        "status": Status.ACTIVE,
        "dels": DeletionStatus.NOT_DELETED,
        "updated_on": datetime.utcnow(),
        "updated_by": restored_by
    })
    
    return data

def get_active_documents_filter() -> Dict[str, Any]:
    """
    Get MongoDB filter for active (non-deleted) documents
    
    Returns:
        Filter dictionary for active documents
    """
    return {
        "status": Status.ACTIVE,
        "dels": DeletionStatus.NOT_DELETED
    }

def get_deleted_documents_filter() -> Dict[str, Any]:
    """
    Get MongoDB filter for soft-deleted documents
    
    Returns:
        Filter dictionary for deleted documents
    """
    return {
        "dels": DeletionStatus.DELETED
    }

def get_inactive_documents_filter() -> Dict[str, Any]:
    """
    Get MongoDB filter for inactive documents
    
    Returns:
        Filter dictionary for inactive documents
    """
    return {
        "status": Status.INACTIVE
    } 