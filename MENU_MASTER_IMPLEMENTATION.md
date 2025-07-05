# Menu Master System Implementation

## Overview

The Menu Master system provides a hierarchical menu structure for the gaming platform with role-based access control and permission management. This system allows for dynamic menu generation based on user permissions and supports both web and mobile access.

## Architecture

### Menu Types

1. **Main Menu (menu_type = 1)**: Top-level navigation items
2. **Sub Menu (menu_type = 2)**: Child items under main menus
3. **Action Menu (menu_type = 3)**: Action-specific menu items (future use)

### Database Schema

The menu master collection (`menu_master`) contains the following fields:

```javascript
{
  _id: ObjectId,
  menu_name: String,           // Display name (e.g., "UI.DASHBOARD")
  menu_value: String,          // Internal identifier (e.g., "dashboard")
  menu_type: Number,           // 1=Main, 2=Sub, 3=Action
  menu_order: Number,          // Display order
  fk_parent_id: ObjectId,      // Parent menu ID (null for main menus)
  can_show: Number,            // Visibility (1=show, 0=hide)
  router_url: String,          // Router URL
  menu_icon: String,           // Icon class/name
  active_urls: Array,          // URLs that activate this menu
  mobile_access: Number,       // Mobile access (1=allowed, 0=denied)
  can_view: Number,            // View permission (1=allowed, 0=denied)
  can_add: Number,             // Add permission (1=allowed, 0=denied)
  can_edit: Number,            // Edit permission (1=allowed, 0=denied)
  can_delete: Number,          // Delete permission (1=allowed, 0=denied)
  description: String,         // Menu description
  module: String,              // Module name
  created_on: Date,
  updated_on: Date,
  created_by: ObjectId,
  updated_by: ObjectId,
  status: Number,              // 1=Active, 0=Inactive
  dels: Number                 // 1=Not deleted, 0=Deleted
}
```

## Example Menu Structure

Based on your requirements, the system creates the following structure:

### Main Menu Items (menu_type = 1)

1. **Dashboard**
   - menu_name: "UI.DASHBOARD"
   - menu_value: "dashboard"
   - menu_icon: "solar:home-smile-angle-outline"
   - menu_order: 1

2. **User Management**
   - menu_name: "UI.USERMANAGEMENT"
   - menu_value: "user_management"
   - menu_icon: "flowbite:users-group-outline"
   - menu_order: 2

3. **Game Management**
   - menu_name: "UI.GAME"
   - menu_value: "game"
   - menu_icon: "game-icons:gamepad-cross"
   - menu_order: 3

4. **Analytics**
   - menu_name: "UI.ANALYTICS"
   - menu_value: "analytics"
   - menu_icon: "material-symbols:analytics-outline"
   - menu_order: 4

### Sub Menu Items (menu_type = 2)

#### Under User Management:
1. **Users**
   - menu_name: "UI.USER"
   - menu_value: "user"
   - router_url: "/hr-management/hrmanagement/user"
   - active_urls: [
       "/hr-management/hrmanagement/user-view",
       "/hr-management/hrmanagement/user-edit/:id",
       "/hr-management/hrmanagement/user-add",
       "/hr-management/hrmanagement/user-delete/:id"
     ]

2. **Roles**
   - menu_name: "UI.ROLES"
   - menu_value: "roles"
   - router_url: "/hr-management/hrmanagement/roles"
   - active_urls: [
       "/hr-management/hrmanagement/roles-view",
       "/hr-management/hrmanagement/roles-edit/:id",
       "/hr-management/hrmanagement/roles-add",
       "/hr-management/hrmanagement/roles-delete/:id"
     ]

#### Under Game Management:
1. **Game List**
   - menu_name: "UI.GAME_LIST"
   - menu_value: "game_list"
   - router_url: "/game-management/games"

2. **Game Settings**
   - menu_name: "UI.GAME_SETTINGS"
   - menu_value: "game_settings"
   - router_url: "/game-management/settings"

#### Under Analytics:
1. **Player Analytics**
   - menu_name: "UI.PLAYER_ANALYTICS"
   - menu_value: "player_analytics"
   - router_url: "/analytics/players"

2. **Game Analytics**
   - menu_name: "UI.GAME_ANALYTICS"
   - menu_value: "game_analytics"
   - router_url: "/analytics/games"

## API Endpoints

### Menu Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/menu/` | Create a new menu item |
| GET | `/api/v1/menu/{menu_id}` | Get menu by ID |
| GET | `/api/v1/menu/value/{menu_value}` | Get menu by value |
| PUT | `/api/v1/menu/{menu_id}` | Update menu item |
| DELETE | `/api/v1/menu/{menu_id}` | Delete menu item |
| GET | `/api/v1/menu/` | List menus with pagination and filters |
| GET | `/api/v1/menu/type/{menu_type}` | Get menus by type |
| GET | `/api/v1/menu/parent/{parent_id}` | Get child menus |
| GET | `/api/v1/menu/tree/hierarchy` | Get hierarchical menu tree |
| GET | `/api/v1/menu/main-menu` | Get main menu items |
| GET | `/api/v1/menu/permissions/{menu_value}` | Get menu permissions |
| POST | `/api/v1/menu/reorder` | Reorder menu items |

### Query Parameters

- `page`: Page number (default: 1)
- `size`: Page size (default: 10, max: 100)
- `menu_type`: Filter by menu type (1=Main, 2=Sub, 3=Action)
- `parent_id`: Filter by parent menu ID
- `search`: Search in menu name, value, or description
- `include_inactive`: Include inactive menus (default: false)

## Usage Examples

### Creating a Menu Item

```python
from app.schemas.menu import MenuCreate

menu_data = MenuCreate(
    menu_name="UI.NEW_MENU",
    menu_value="new_menu",
    menu_type=2,
    menu_order=1,
    fk_parent_id=parent_menu_id,
    can_show=1,
    router_url="/new-menu",
    menu_icon="icon-class",
    active_urls=["/new-menu-view", "/new-menu-edit/:id"],
    mobile_access=1,
    can_view=1,
    can_add=1,
    can_edit=1,
    can_delete=0,
    description="New menu item",
    module="new_module"
)
```

### Getting Menu Tree

```python
from app.services.menu_service import MenuService

menu_service = MenuService()
menu_tree = await menu_service.get_menu_tree()

# menu_tree will contain hierarchical structure
for root_menu in menu_tree:
    print(f"Main Menu: {root_menu.menu_name}")
    for child in root_menu.children:
        print(f"  Sub Menu: {child.menu_name}")
```

### Checking Permissions

```python
permissions = await menu_service.get_menu_permissions("user_management")
if permissions:
    can_view = permissions["can_view"]
    can_add = permissions["can_add"]
    can_edit = permissions["can_edit"]
    can_delete = permissions["can_delete"]
```

## Initialization

To initialize the menu data, run the initialization script:

```bash
python scripts/init_menu_data.py
```

This script will:
1. Connect to MongoDB
2. Check if menu data already exists
3. Create the complete menu hierarchy
4. Verify the menu tree structure
5. Display the created menu items

## Frontend Integration

### Menu Tree Response Format

The menu tree API returns a hierarchical structure:

```json
[
  {
    "id": "menu_id",
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
    "children": [
      {
        "id": "child_menu_id",
        "menu_name": "UI.USER",
        "menu_value": "user",
        "menu_type": 2,
        "menu_order": 1,
        "fk_parent_id": "parent_menu_id",
        "children": []
      }
    ]
  }
]
```

### Permission Checking

Use the permissions endpoint to check user access:

```javascript
// Frontend example
const checkMenuPermission = async (menuValue) => {
  const response = await fetch(`/api/v1/menu/permissions/${menuValue}`);
  const permissions = await response.json();
  
  return {
    canView: permissions.can_view,
    canAdd: permissions.can_add,
    canEdit: permissions.can_edit,
    canDelete: permissions.can_delete
  };
};
```

## Security Features

1. **Authentication Required**: All menu endpoints require user authentication
2. **Permission-Based Access**: Each menu item has granular permissions
3. **Soft Delete**: Menu items are soft-deleted to maintain referential integrity
4. **Audit Trail**: All changes are tracked with created_by/updated_by fields
5. **Validation**: Menu values must be unique across the system

## Best Practices

1. **Menu Naming**: Use consistent naming conventions (e.g., "UI.MODULE_NAME")
2. **Menu Values**: Use lowercase with underscores for internal values
3. **Icons**: Use consistent icon libraries and naming conventions
4. **URLs**: Use RESTful URL patterns for active_urls
5. **Permissions**: Set appropriate default permissions for different menu types
6. **Ordering**: Use meaningful order numbers (10, 20, 30...) for easy reordering

## Troubleshooting

### Common Issues

1. **Menu not showing**: Check `can_show` and `status` fields
2. **Permission denied**: Verify user has appropriate permissions
3. **Menu tree not loading**: Check for circular references in parent-child relationships
4. **Duplicate menu values**: Ensure menu_value is unique across the system

### Debugging

Enable debug logging to troubleshoot menu issues:

```python
import logging
logging.getLogger('app.services.menu_service').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Role-Based Menu Assignment**: Assign menus to specific user roles
2. **Dynamic Menu Loading**: Load menus based on user context
3. **Menu Caching**: Implement Redis caching for better performance
4. **Menu Analytics**: Track menu usage and user behavior
5. **Multi-language Support**: Support for internationalized menu names 