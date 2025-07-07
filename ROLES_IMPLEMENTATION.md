# Roles Management Implementation

This document describes the implementation of the roles management system adapted from Flask RESTX to FastAPI.

## Overview

The roles management system provides:
- Role creation, updating, and deletion
- Permission management with hierarchical menu structure
- Grid-based data display with pagination and search
- Form dependency management for role creation/editing

## File Structure

```
app/
├── models/
│   ├── roles.py          # Roles and permissions models
│   └── menu.py           # Menu structure models
├── routes/
│   └── roles.py          # Roles API endpoints
└── scripts/
    └── init_roles_db.py  # Database initialization script
```

## Models

### RolesModel (app/models/roles.py)

The main roles model with the following structure:
- `fk_company_id`: Company identifier
- `role_name`: Name of the role
- `permissions`: List of permission details
- Standard audit fields (created_on, updated_on, created_by, updated_by)
- Status fields (status, dels)

### MenuModel (app/models/menu.py)

Menu structure model with hierarchical organization:
- `menu_type`: 1=module, 2=submenu, 3=permission
- `menu_model`: Grouping identifier
- `fk_parent_id`: Parent menu reference
- `menu_order`: Display order

## API Endpoints

### GET /api/v1/roles/grid-data
Get roles data for grid display with pagination and search.

**Query Parameters:**
- `data`: JSON string containing `page`, `count`, and `searchString`

**Response:**
```json
{
  "data": [
    {
      "id": "role_id",
      "role_name": "Admin",
      "status": 1
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 10
}
```

### GET /api/v1/roles/get-form-dependency
### GET /api/v1/roles/get-form-dependency/{menu_id}
Get form dependencies for role creation/editing.

**Response:** Menu structure with permissions hierarchy

### POST /api/v1/roles
Create a new role.

**Request Body:**
```json
{
  "role_name": "New Role",
  "permissions": {
    "module_id": {
      "menu_id": true
    }
  }
}
```

### PUT /api/v1/roles
Update an existing role.

**Request Body:**
```json
{
  "id": "role_id",
  "role_name": "Updated Role",
  "permissions": {
    "module_id": {
      "menu_id": true
    }
  }
}
```

### PATCH /api/v1/roles
Update role status.

**Request Body:**
```json
{
  "id": "role_id",
  "status": 1
}
```

### GET /api/v1/roles/{role_id}
Get a single role by ID.

### DELETE /api/v1/roles/{role_id}
Delete a role.

### DELETE /api/v1/roles/bulk-delete/{role_ids}
Bulk delete roles.

## Database Setup

### Collections

1. **roles**: Stores role definitions and permissions
2. **menu_master**: Stores menu structure and hierarchy

### Indexes

**roles collection:**
- `fk_company_id`
- `role_name`
- `created_on`
- `updated_on`
- `status`

**menu_master collection:**
- `menu_type`
- `menu_model`
- `fk_parent_id`
- `menu_order`
- `menu_value` (unique)

### Initialization

Run the database initialization script:

```bash
python scripts/init_roles_db.py
```

This script will:
- Create necessary collections
- Create indexes
- Insert sample menu structure
- Insert sample roles

## Authentication

All endpoints require admin authentication using the existing cookie-based authentication system.

## Usage Examples

### Creating a Role

```python
import requests

# Create a new role
role_data = {
    "role_name": "Content Manager",
    "permissions": {
        "1": {  # User Management module
            "view_users": True,
            "create_user": True,
            "edit_user": True,
            "delete_user": False
        },
        "2": {  # Role Management module
            "view_roles": True,
            "create_role": False,
            "edit_role": False,
            "delete_role": False
        }
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/roles",
    json=role_data,
    cookies={"access_token": "your_token"}
)
```

### Getting Roles Grid Data

```python
import requests

# Get roles with pagination and search
grid_data = {
    "page": 1,
    "count": 10,
    "searchString": "admin"
}

response = requests.get(
    "http://localhost:8000/api/v1/roles/grid-data",
    params={"data": json.dumps(grid_data)},
    cookies={"access_token": "your_token"}
)
```

## Migration from Flask RESTX

Key changes made during the migration:

1. **Framework**: Flask RESTX → FastAPI
2. **Authentication**: JWT → Cookie-based auth
3. **Database**: MongoDB with Motor (async)
4. **Validation**: Marshmallow → Pydantic
5. **Error Handling**: Custom exception handler → FastAPI HTTPException
6. **Async Support**: Added async/await throughout

## Security Considerations

1. **Authentication**: All endpoints require admin authentication
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic models ensure data integrity
4. **SQL Injection**: MongoDB aggregation pipelines are safe
5. **XSS Protection**: Input sanitization and output encoding

## Performance Considerations

1. **Indexing**: Proper indexes on frequently queried fields
2. **Pagination**: Grid data supports pagination to limit result size
3. **Aggregation**: Efficient MongoDB aggregation pipelines
4. **Caching**: Consider implementing Redis caching for menu structure

## Future Enhancements

1. **Role Hierarchy**: Support for role inheritance
2. **Dynamic Permissions**: Runtime permission updates
3. **Audit Trail**: Detailed logging of permission changes
4. **Bulk Operations**: Enhanced bulk role management
5. **API Rate Limiting**: Implement rate limiting for role operations 