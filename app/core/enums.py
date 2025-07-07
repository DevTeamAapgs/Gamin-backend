from enum import IntEnum

class Status(IntEnum):
    """Status enum for active/inactive records"""
    INACTIVE = 0
    ACTIVE = 1

class DeletionStatus(IntEnum):
    """Deletion status enum for soft delete functionality"""
    DELETED = 0
    NOT_DELETED = 1 
    
class PlayerType(IntEnum):
    """PlayerType enum for superadmin/admin employee/player records"""
    SUPERADMIN = 0
    ADMINEMPLOYEE = 1
    PLAYER = 2
    