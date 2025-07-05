# Menu Master API Usage Examples

## Authentication

All menu endpoints require authentication. Use the cookie-based authentication system:

```bash
# Login first to get authentication cookie
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  -c cookies.txt
```

## Menu Management Examples

### 1. Create a New Menu Item

```bash
curl -X POST "http://localhost:8000/api/v1/menu/" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "menu_name": "UI.NEW_FEATURE",
    "menu_value": "new_feature",
    "menu_type": 2,
    "menu_order": 1,
    "fk_parent_id": "PARENT_MENU_ID",
    "can_show": 1,
    "router_url": "/new-feature",
    "menu_icon": "material-symbols:new-feature",
    "active_urls": [
      "/new-feature-view",
      "/new-feature-edit/:id"
    ],
    "mobile_access": 1,
    "can_view": 1,
    "can_add": 1,
    "can_edit": 1,
    "can_delete": 0,
    "description": "New feature menu item",
    "module": "new_module"
  }'
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "menu_name": "UI.NEW_FEATURE",
  "menu_value": "new_feature",
  "menu_type": 2,
  "menu_order": 1,
  "fk_parent_id": "PARENT_MENU_ID",
  "can_show": 1,
  "router_url": "/new-feature",
  "menu_icon": "material-symbols:new-feature",
  "active_urls": [
    "/new-feature-view",
    "/new-feature-edit/:id"
  ],
  "mobile_access": 1,
  "can_view": 1,
  "can_add": 1,
  "can_edit": 1,
  "can_delete": 0,
  "description": "New feature menu item",
  "module": "new_module",
  "created_on": "2024-01-15T10:30:00Z",
  "updated_on": "2024-01-15T10:30:00Z",
  "created_by": "507f1f77bcf86cd799439012",
  "updated_by": null,
  "status": 1,
  "dels": 1
}
```

### 2. Get Menu by ID

```bash
curl -X GET "http://localhost:8000/api/v1/menu/507f1f77bcf86cd799439011" \
  -b cookies.txt
```

### 3. Get Menu by Value

```bash
curl -X GET "http://localhost:8000/api/v1/menu/value/dashboard" \
  -b cookies.txt
```

### 4. Update Menu Item

```bash
curl -X PUT "http://localhost:8000/api/v1/menu/507f1f77bcf86cd799439011" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "menu_name": "UI.UPDATED_FEATURE",
    "menu_order": 2,
    "can_edit": 0
  }'
```

### 5. Delete Menu Item

```bash
curl -X DELETE "http://localhost:8000/api/v1/menu/507f1f77bcf86cd799439011" \
  -b cookies.txt
```

**Response:**
```json
{
  "message": "Menu deleted successfully"
}
```

### 6. Get Menus by Type

```bash
# Get all main menu items (type 1)
curl -X GET "http://localhost:8000/api/v1/menu/type/1" \
  -b cookies.txt

# Get all sub menu items (type 2)
curl -X GET "http://localhost:8000/api/v1/menu/type/2" \
  -b cookies.txt
```

### 7. Get Menu Tree (Hierarchical Structure)

```bash
curl -X GET "http://localhost:8000/api/v1/menu/tree/hierarchy" \
  -b cookies.txt
```

**Response:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "menu_name": "UI.DASHBOARD",
    "menu_value": "dashboard",
    "menu_type": 1,
    "menu_order": 1,
    "fk_parent_id": null,
    "can_show": 1,
    "router_url": "",
    "menu_icon": "solar:home-smile-angle-outline",
    "active_urls": [],
    "mobile_access": 1,
    "can_view": 1,
    "can_add": 0,
    "can_edit": 0,
    "can_delete": 0,
    "description": "Main dashboard menu item",
    "module": "dashboard",
    "children": []
  },
  {
    "id": "507f1f77bcf86cd799439012",
    "menu_name": "UI.USERMANAGEMENT",
    "menu_value": "user_management",
    "menu_type": 1,
    "menu_order": 2,
    "fk_parent_id": null,
    "can_show": 1,
    "router_url": "",
    "menu_icon": "flowbite:users-group-outline",
    "active_urls": [],
    "mobile_access": 1,
    "can_view": 1,
    "can_add": 0,
    "can_edit": 0,
    "can_delete": 0,
    "description": "User management main menu item",
    "module": "user_management",
    "children": [
      {
        "id": "507f1f77bcf86cd799439013",
        "menu_name": "UI.USER",
        "menu_value": "user",
        "menu_type": 2,
        "menu_order": 1,
        "fk_parent_id": "507f1f77bcf86cd799439012",
        "can_show": 1,
        "router_url": "/hr-management/hrmanagement/user",
        "menu_icon": "",
        "active_urls": [
          "/hr-management/hrmanagement/user-view",
          "/hr-management/hrmanagement/user-edit/:id",
          "/hr-management/hrmanagement/user-add",
          "/hr-management/hrmanagement/user-delete/:id"
        ],
        "mobile_access": 1,
        "can_view": 1,
        "can_add": 1,
        "can_edit": 1,
        "can_delete": 1,
        "description": "User management sub-menu",
        "module": "user_management",
        "children": []
      }
    ]
  }
]
```

### 8. Get Child Menus

```bash
curl -X GET "http://localhost:8000/api/v1/menu/parent/507f1f77bcf86cd799439012" \
  -b cookies.txt
```

### 9. List Menus with Pagination and Filters

```bash
# Basic pagination
curl -X GET "http://localhost:8000/api/v1/menu/?page=1&size=10" \
  -b cookies.txt

# With filters
curl -X GET "http://localhost:8000/api/v1/menu/?menu_type=1&search=dashboard&include_inactive=false" \
  -b cookies.txt
```

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439011",
      "menu_name": "UI.DASHBOARD",
      "menu_value": "dashboard",
      "menu_type": 1,
      "menu_order": 1,
      "fk_parent_id": null,
      "can_show": 1,
      "router_url": "",
      "menu_icon": "solar:home-smile-angle-outline",
      "active_urls": [],
      "mobile_access": 1,
      "can_view": 1,
      "can_add": 0,
      "can_edit": 0,
      "can_delete": 0,
      "description": "Main dashboard menu item",
      "module": "dashboard",
      "created_on": "2024-01-15T10:30:00Z",
      "updated_on": "2024-01-15T10:30:00Z",
      "created_by": "507f1f77bcf86cd799439012",
      "updated_by": null,
      "status": 1,
      "dels": 1
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

### 10. Get Main Menu Items

```bash
curl -X GET "http://localhost:8000/api/v1/menu/main-menu" \
  -b cookies.txt
```

### 11. Get Menu Permissions

```bash
curl -X GET "http://localhost:8000/api/v1/menu/permissions/user_management" \
  -b cookies.txt
```

**Response:**
```json
{
  "menu_id": "507f1f77bcf86cd799439012",
  "menu_value": "user_management",
  "can_view": true,
  "can_add": false,
  "can_edit": false,
  "can_delete": false,
  "active_urls": []
}
```

### 12. Reorder Menu Items

```bash
curl -X POST "http://localhost:8000/api/v1/menu/reorder" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '[
    {
      "menu_id": "507f1f77bcf86cd799439011",
      "menu_order": 2
    },
    {
      "menu_id": "507f1f77bcf86cd799439012",
      "menu_order": 1
    }
  ]'
```

**Response:**
```json
{
  "message": "Menus reordered successfully"
}
```

## JavaScript/Frontend Examples

### Get Menu Tree

```javascript
const getMenuTree = async () => {
  try {
    const response = await fetch('/api/v1/menu/tree/hierarchy', {
      credentials: 'include' // Include cookies
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch menu tree');
    }
    
    const menuTree = await response.json();
    return menuTree;
  } catch (error) {
    console.error('Error fetching menu tree:', error);
    throw error;
  }
};

// Usage
getMenuTree().then(menuTree => {
  console.log('Menu tree:', menuTree);
  // Render menu in your UI
});
```

### Check Menu Permissions

```javascript
const checkMenuPermission = async (menuValue) => {
  try {
    const response = await fetch(`/api/v1/menu/permissions/${menuValue}`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch menu permissions');
    }
    
    const permissions = await response.json();
    return permissions;
  } catch (error) {
    console.error('Error checking menu permissions:', error);
    return null;
  }
};

// Usage
checkMenuPermission('user_management').then(permissions => {
  if (permissions) {
    console.log('Can view:', permissions.can_view);
    console.log('Can add:', permissions.can_add);
    console.log('Can edit:', permissions.can_edit);
    console.log('Can delete:', permissions.can_delete);
  }
});
```

### Create Menu Item

```javascript
const createMenuItem = async (menuData) => {
  try {
    const response = await fetch('/api/v1/menu/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify(menuData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create menu item');
    }
    
    const newMenu = await response.json();
    return newMenu;
  } catch (error) {
    console.error('Error creating menu item:', error);
    throw error;
  }
};

// Usage
const newMenuData = {
  menu_name: "UI.NEW_FEATURE",
  menu_value: "new_feature",
  menu_type: 2,
  menu_order: 1,
  fk_parent_id: "PARENT_MENU_ID",
  can_show: 1,
  router_url: "/new-feature",
  menu_icon: "material-symbols:new-feature",
  active_urls: ["/new-feature-view", "/new-feature-edit/:id"],
  mobile_access: 1,
  can_view: 1,
  can_add: 1,
  can_edit: 1,
  can_delete: 0,
  description: "New feature menu item",
  module: "new_module"
};

createMenuItem(newMenuData).then(newMenu => {
  console.log('Created menu item:', newMenu);
});
```

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Menu with value 'dashboard' already exists"
}
```

**404 Not Found:**
```json
{
  "detail": "Menu not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

### Error Handling in JavaScript

```javascript
const handleApiError = (response) => {
  if (!response.ok) {
    return response.json().then(error => {
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    });
  }
  return response.json();
};

// Usage in fetch calls
fetch('/api/v1/menu/tree/hierarchy', { credentials: 'include' })
  .then(handleApiError)
  .then(data => {
    console.log('Success:', data);
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

## Testing with curl

### Test Menu Tree Endpoint

```bash
# First login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  -c cookies.txt

# Then get menu tree
curl -X GET "http://localhost:8000/api/v1/menu/tree/hierarchy" \
  -b cookies.txt \
  -H "Accept: application/json"
```

### Test Menu Permissions

```bash
curl -X GET "http://localhost:8000/api/v1/menu/permissions/dashboard" \
  -b cookies.txt \
  -H "Accept: application/json"
```

### Test Menu Creation

```bash
curl -X POST "http://localhost:8000/api/v1/menu/" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "menu_name": "UI.TEST_MENU",
    "menu_value": "test_menu",
    "menu_type": 1,
    "menu_order": 5,
    "can_show": 1,
    "router_url": "/test",
    "menu_icon": "test-icon",
    "active_urls": [],
    "mobile_access": 1,
    "can_view": 1,
    "can_add": 0,
    "can_edit": 0,
    "can_delete": 0,
    "description": "Test menu item",
    "module": "test"
  }'
``` 