from enum import IntEnum

class Status(IntEnum):
    """Status enum for active/inactive records"""
    INACTIVE = 0
    ACTIVE = 1

class DeletionStatus(IntEnum):
    """Deletion status enum for soft delete functionality"""
    DELETED = 0
    NOT_DELETED = 1 