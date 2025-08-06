# Prefix Generation System

This document explains how to use the prefix generation system for creating unique identifiers across different modules in the gaming platform.

## Overview

The prefix generation system allows you to create unique, sequential identifiers for different entities (players, games, etc.) by combining a module-specific prefix with an auto-incrementing number.

## Database Schema

The system uses a `prefix` collection in MongoDB with the following structure:

```json
{
  "_id": ObjectId("679b63462adae39e8ff9a010"),
  "key_prefix": "Plr",
  "key_value": 0,
  "module": "Player",
  "application_type": 1,
  "updated_by": "675d4a2c39bdbca09b566864",
  "updated_on": ISODate("2025-01-06T07:20:07.102Z"),
  "module_ui": "UI.PLAYER"
}
```

## Usage

### Basic Usage

```python
from app.common.prefix import generate_prefix

# Generate a prefix for Player module with 3 digits
player_prefix = await generate_prefix("Player", 3)
# Returns: "Plr000" (first call)
# Returns: "Plr001" (second call)
# Returns: "Plr002" (third call)

# Generate a prefix for Player module with 4 digits
player_prefix_4 = await generate_prefix("Player", 4)
# Returns: "Plr0003" (if key_value is 3)

# Generate a prefix for Player module with 2 digits
player_prefix_2 = await generate_prefix("Player", 2)
# Returns: "Plr04" (if key_value is 4)
```

### Function Parameters

- `module` (str): The module name that matches the "module" field in the database
- `value_count` (int): Number of digits to pad the value with (e.g., 3 for "001", 4 for "0001")

### Return Value

Returns a string containing the generated prefix (e.g., "Plr001", "Plr0001", etc.)

## Database Updates

Each time `generate_prefix()` is called:

1. The function finds the prefix record for the specified module
2. Generates the prefix using the current `key_value`
3. Increments the `key_value` by 1 in the database
4. Updates the `updated_on` timestamp

## Integration with User Creation

When creating a new user, you can integrate the prefix generation like this:

```python
from app.common.prefix import generate_prefix

# In your user creation function
async def create_user(user_data):
    # Generate unique prefix for the user
    player_prefix = await generate_prefix("Player", 3)
    
    # Create user document with the prefix
    user_document = {
        "username": user_data["username"],
        "email": user_data["email"],
        "wallet_address": user_data["wallet_address"],
        "password_hash": user_data["password_hash"],
        "player_prefix": player_prefix,  # Add the generated prefix
        "is_admin": user_data.get("is_admin", False),
        "is_verified": user_data.get("is_verified", False),
        "token_balance": 0,
        "total_games_played": 0,
        "total_tokens_earned": 0,
        "created_at": datetime.utcnow(),
        "status": 1,
        "is_active": True,
        "fk_role_id": ObjectId(user_data["role_id"])
    }
    
    # Insert into database
    result = await db.players.insert_one(user_document)
    return result.inserted_id
```

## Error Handling

The function includes comprehensive error handling:

- **Module not found**: Raises `ValueError` if no prefix record exists for the specified module
- **Database update failure**: Raises `Exception` if the key_value cannot be updated
- **General errors**: Logs and re-raises any other exceptions

## Testing

You can test the prefix generation system using the provided test script:

```bash
python scripts/test_prefix_generation.py
```

## Example Output

```
Testing Prefix Generation Functionality
==================================================

1. Testing Player module with 3 digits:
   Generated prefix: Plr000

2. Testing Player module with 4 digits:
   Generated prefix: Plr0001

3. Testing Player module with 2 digits:
   Generated prefix: Plr02

4. Getting prefix info for Player module:
   Prefix info: {'key_prefix': 'Plr', 'key_value': 3, 'module': 'Player', ...}

5. Testing non-existent module:
   Expected error: No prefix record found for module: NonExistent
```

## Best Practices

1. **Consistent module names**: Always use the exact module name as stored in the database
2. **Appropriate digit count**: Choose a digit count that provides enough capacity for your use case
3. **Error handling**: Always handle potential exceptions when calling the function
4. **Logging**: The function includes logging for debugging and monitoring
5. **Atomic operations**: The function ensures atomic updates to prevent race conditions 