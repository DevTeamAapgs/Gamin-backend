# Standardized Collection Structure

This document describes the standardized collection structure implemented across all database collections in the gaming platform.

## Overview

All collections now include standardized audit fields and status management using enums for consistency and better data management.

## Standard Fields

Every collection includes these standard fields:

### Audit Fields
- `created_on`: `datetime` - When the document was created
- `updated_on`: `datetime` - When the document was last updated
- `created_by`: `PyObjectId` - ID of user who created the document
- `updated_by`: `PyObjectId` - ID of user who last updated the document

### Status Fields
- `status`: `Status` enum - Active/Inactive status (default: ACTIVE)
- `dels`: `DeletionStatus` enum - Soft delete status (default: NOT_DELETED)

## Enums

### Status Enum (`app/core/enums.py`)
```python
class Status(IntEnum):
    INACTIVE = 0
    ACTIVE = 1
```

### DeletionStatus Enum (`app/core/enums.py`)
```python
class DeletionStatus(IntEnum):
    DELETED = 0
    NOT_DELETED = 1
```

## Base Document Model

All models inherit from `BaseDocument` (`app/models/base.py`) which provides:

- Standard audit fields
- Status management
- Soft delete functionality
- Helper methods for audit operations

### BaseDocument Methods

```python
# Update audit fields
document.update_audit_fields(updated_by=user_id)

# Soft delete
document.soft_delete(deleted_by=user_id)

# Restore soft-deleted document
document.restore(restored_by=user_id)
```

## Updated Models

### Player Model
- Inherits from `BaseDocument`
- Removed duplicate `is_active` field (now uses `status`)
- Removed `created_at`/`updated_at` (now uses `created_on`/`updated_on`)

### Game Model
- Inherits from `BaseDocument`
- Renamed `status` to `game_status` to avoid conflict
- Removed duplicate audit fields

### Transaction Model
- Inherits from `BaseDocument`
- Renamed `status` to `transaction_status` to avoid conflict

### Logging Models
- All logging models inherit from `BaseDocument`
- Standardized audit fields for all log entries

## Database Utilities

Utility functions in `app/utils/db_utils.py` for common operations:

### Adding Audit Fields
```python
from app.utils.db_utils import add_audit_fields

document_data = add_audit_fields(
    data={"name": "example"}, 
    created_by=user_id
)
```

### Updating Audit Fields
```python
from app.utils.db_utils import update_audit_fields

document_data = update_audit_fields(
    data=existing_data, 
    updated_by=user_id
)
```

### Soft Delete
```python
from app.utils.db_utils import soft_delete_document

document_data = soft_delete_document(
    data=existing_data, 
    deleted_by=user_id
)
```

### Database Filters
```python
from app.utils.db_utils import get_active_documents_filter

# Get only active documents
filter_query = get_active_documents_filter()
active_docs = await collection.find(filter_query).to_list(None)

# Get soft-deleted documents
filter_query = get_deleted_documents_filter()
deleted_docs = await collection.find(filter_query).to_list(None)
```

## Database Indexes

Updated indexes include the new standard fields:

```python
# Standard indexes for all collections
await collection.create_index("created_on")
await collection.create_index("status")
await collection.create_index("dels")
await collection.create_index("created_by")
await collection.create_index("updated_by")
```

## Migration Notes

### Existing Data
- Existing documents will need migration to add the new fields
- Default values will be applied for missing fields
- `status` will default to `ACTIVE` (1)
- `dels` will default to `NOT_DELETED` (1)

### Code Changes Required
1. Update all database queries to use new field names
2. Replace `created_at` with `created_on`
3. Replace `updated_at` with `updated_on`
4. Use `status` field instead of `is_active`
5. Add soft delete logic using `dels` field

### Example Migration Query
```python
# Update existing documents to include new fields
await db.collection.update_many(
    {"created_on": {"$exists": False}},
    {
        "$set": {
            "created_on": "$created_at",
            "updated_on": "$updated_at",
            "status": 1,  # ACTIVE
            "dels": 1,    # NOT_DELETED
            "created_by": None,
            "updated_by": None
        }
    }
)
```

## Benefits

1. **Consistency**: All collections follow the same structure
2. **Audit Trail**: Complete tracking of who created/modified documents
3. **Soft Delete**: Safe deletion without data loss
4. **Status Management**: Standardized active/inactive status
5. **Query Optimization**: Proper indexing for common queries
6. **Maintainability**: Centralized audit logic

## Usage Examples

### Creating a New Document
```python
from app.utils.db_utils import add_audit_fields

player_data = {
    "username": "newplayer",
    "wallet_address": "0x...",
    "email": "player@example.com"
}

# Add audit fields
player_data = add_audit_fields(player_data, created_by=admin_id)
result = await db.players.insert_one(player_data)
```

### Updating a Document
```python
from app.utils.db_utils import update_audit_fields

update_data = {"username": "updated_username"}
update_data = update_audit_fields(update_data, updated_by=user_id)

await db.players.update_one(
    {"_id": player_id},
    {"$set": update_data}
)
```

### Soft Delete
```python
from app.utils.db_utils import soft_delete_document

delete_data = soft_delete_document({}, deleted_by=admin_id)
await db.players.update_one(
    {"_id": player_id},
    {"$set": delete_data}
)
```

### Querying Active Documents
```python
from app.utils.db_utils import get_active_documents_filter

filter_query = get_active_documents_filter()
active_players = await db.players.find(filter_query).to_list(None)
``` 