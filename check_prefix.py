import asyncio
from app.db.mongo import connect_to_mongo, get_database, close_mongo_connection

async def check_prefix():
    try:
        # Connect to database first
        await connect_to_mongo()
        
        db = get_database()
        result = await db.prefix.find_one({'module': 'player'})
        print('Prefix record:', result)
        
        # Check all prefix records
        all_prefixes = await db.prefix.find({}).to_list(length=10)
        print('All prefix records:', all_prefixes)
        
    except Exception as e:
        print('Error:', e)
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check_prefix()) 