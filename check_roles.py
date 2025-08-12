import asyncio
from app.db.mongo import get_database

async def check_roles():
    try:
        db = get_database()
        roles = await db.roles.find({}).to_list(length=10)
        print("Available roles:")
        for role in roles:
            print(f"- {role['role']}")
        if not roles:
            print("No roles found in database")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_roles()) 