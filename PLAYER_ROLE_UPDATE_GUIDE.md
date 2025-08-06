# Player Creation Role Name Update

This document explains the changes made to the player creation API to use role names instead of role IDs.

## Overview

The player creation endpoint has been updated to accept a `role` name instead of `fk_role_id`. This makes the API more user-friendly and reduces the need to know internal role IDs.

## Changes Made

### 1. Schema Updates

#### PlayerCreate Schema
- **Before**: `fk_role_id: str`
- **After**: `role: str`

#### PlayerUpdate Schema  
- **Before**: `fk_role_id: Optional[str]`
- **After**: `role: Optional[str]`

### 2. API Endpoint Updates

#### POST `/api/v1/player/` - Create User
- **Request Body Before**:
```json
{
  "username": "string",
  "email": "user@example.com", 
  "password": "string",
  "fk_role_id": "string",
  "status": 1
}
```

- **Request Body After**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string", 
  "role": "string",
  "status": 1
}
```

#### PUT `/api/v1/player/{user_id}` - Update User
- Now accepts `role` instead of `fk_role_id` in the request body

### 3. Backend Logic Updates

#### Role Lookup Process
1. When creating or updating a user, the system looks up the role ID from the roles collection using the role name
2. If the role name is not found, returns a 400 error with a descriptive message
3. The role ID is then stored in the `fk_role_id` field in the database

#### Example Role Lookup
```python
# Look up role ID from role name
role_doc = await db.roles.find_one({"role": data.role})
if not role_doc:
    raise HTTPException(status_code=400, detail=f"Role '{data.role}' not found")

# Use the role ID for database storage
doc["fk_role_id"] = role_doc["_id"]
```

## Usage Examples

### Creating an Admin User
```bash
curl -X POST "http://localhost:8000/api/v1/player/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "email": "admin@example.com",
    "password": "secure_password",
    "role": "admin",
    "status": 1
  }'
```

### Creating a Regular Player
```bash
curl -X POST "http://localhost:8000/api/v1/player/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "regular_player",
    "email": "player@example.com",
    "password": "player_password",
    "role": "player",
    "status": 1
  }'
```

### Updating User Role
```bash
curl -X PUT "http://localhost:8000/api/v1/player/{user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "moderator"
  }'
```

## Error Handling

### Role Not Found
If a role name is provided that doesn't exist in the roles collection:
```json
{
  "detail": "Role 'invalid_role' not found"
}
```

### Email Already Exists
If the email is already registered:
```json
{
  "detail": "Email already exists"
}
```

## Database Schema

The database structure remains the same. The `fk_role_id` field still stores the ObjectId reference to the roles collection. The change is only in the API interface.

### Players Collection
```json
{
  "_id": ObjectId("..."),
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "wallet_address": "string",
  "fk_role_id": ObjectId("..."),  // Still stores role ID
  "role": "string",               // Computed field for response
  "status": 1,
  "is_active": true,
  "created_at": ISODate("..."),
  "last_login": ISODate("...")
}
```

### Roles Collection
```json
{
  "_id": ObjectId("..."),
  "role": "admin",        // Role name used for lookup
  "description": "string",
  "permissions": ["..."]
}
```

## Testing

You can test the new functionality using the provided test script:

```bash
python scripts/test_player_creation.py
```

This will verify that:
- The PlayerCreate schema accepts role names
- The request body format is correct
- Example requests are properly formatted

## Migration Notes

- **Backward Compatibility**: This is a breaking change. Existing clients using `fk_role_id` will need to be updated to use `role`
- **Role Names**: Ensure that the role names in your roles collection match what clients will send
- **Validation**: The system validates role names against the roles collection before creating users

## Benefits

1. **User-Friendly**: Clients don't need to know internal role IDs
2. **Self-Documenting**: Role names are more descriptive than IDs
3. **Flexible**: Easy to change role names without affecting existing data
4. **Consistent**: Matches the pattern used in other parts of the system 