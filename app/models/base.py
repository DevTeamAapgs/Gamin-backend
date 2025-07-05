from datetime import datetime
from typing import Optional, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId
from app.core.enums import Status, DeletionStatus

def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId string")
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class BaseDocument(BaseModel):
    """Base document with standardized audit fields for all collections"""
    
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")
    
    # Audit fields
    created_on: datetime = Field(default_factory=datetime.utcnow)
    updated_on: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = None
    updated_by: Optional[PyObjectId] = None
    
    # Status fields
    status: Status = Field(default=Status.ACTIVE)
    dels: DeletionStatus = Field(default=DeletionStatus.NOT_DELETED)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
    
    def update_audit_fields(self, updated_by: Optional[PyObjectId] = None):
        """Update audit fields when document is modified"""
        self.updated_on = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
    
    def soft_delete(self, deleted_by: Optional[PyObjectId] = None):
        """Soft delete the document"""
        self.dels = DeletionStatus.DELETED
        self.status = Status.INACTIVE
        self.update_audit_fields(deleted_by)
    
    def restore(self, restored_by: Optional[PyObjectId] = None):
        """Restore a soft-deleted document"""
        self.dels = DeletionStatus.NOT_DELETED
        self.status = Status.ACTIVE
        self.update_audit_fields(restored_by) 