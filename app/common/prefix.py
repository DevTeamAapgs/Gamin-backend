from app.db.mongo import get_database
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def generate_prefix(module: str, value_count: int) -> str:
    """
    Generate a unique prefix based on module and value count.
    
    Args:
        module (str): The module name (e.g., "Player", "Game", etc.)
        value_count (int): Number of digits to pad the value with
        
    Returns:
        str: Generated prefix (e.g., "Plr001", "Plr0001", etc.)
    """
    try:
        db = get_database()
        prefix_collection = db.prefix
        
        # Find the prefix record for the given module
        prefix_record = await prefix_collection.find_one({"module": module})
        
        if not prefix_record:
            logger.error(f"No prefix record found for module: {module}")
            raise ValueError(f"No prefix record found for module: {module}")
        
        # Extract prefix and current value
        key_prefix = prefix_record.get("key_prefix", "")
        current_value = prefix_record.get("key_value", 0)
        
        # Generate the formatted value with leading zeros
        formatted_value = str(current_value).zfill(value_count)
        
        # Create the final prefix
        generated_prefix = f"{key_prefix}{formatted_value}"
        
        # Update the key_value in the database (increment by 1)
        new_value = current_value + 1
        update_result = await prefix_collection.update_one(
            {"_id": prefix_record["_id"]},
            {
                "$set": {
                    "key_value": new_value,
                    "updated_on": datetime.utcnow()
                }
            }
        )
        
        if update_result.modified_count == 0:
            logger.error(f"Failed to update prefix value for module: {module}")
            raise Exception(f"Failed to update prefix value for module: {module}")
        
        logger.info(f"Generated prefix '{generated_prefix}' for module '{module}' (value: {current_value} -> {new_value})")
        return generated_prefix
        
    except Exception as e:
        logger.error(f"Error generating prefix for module '{module}': {str(e)}")
        raise

async def get_prefix_info(module: str) -> dict:
    """
    Get prefix information for a module without updating the value.
    
    Args:
        module (str): The module name
        
    Returns:
        dict: Prefix information including key_prefix and key_value
    """
    try:
        db = get_database()
        prefix_collection = db.prefix
        
        prefix_record = await prefix_collection.find_one({"module": module})
        
        if not prefix_record:
            logger.error(f"No prefix record found for module: {module}")
            return None
            
        return {
            "key_prefix": prefix_record.get("key_prefix", ""),
            "key_value": prefix_record.get("key_value", 0),
            "module": prefix_record.get("module", ""),
            "application_type": prefix_record.get("application_type", 1),
            "module_ui": prefix_record.get("module_ui", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting prefix info for module '{module}': {str(e)}")
        raise 