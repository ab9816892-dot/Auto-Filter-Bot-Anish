import motor.motor_asyncio
from config import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URI)
        self.db = self.client[DATABASE_NAME]
        self.col = self.db[COLLECTION_NAME]
        self.users = self.db["users"]

    async def save_file(self, media):
        """Save Telegram file to MongoDB"""
        file_data = {
            "file_name": media.file_name,
            "file_id": media.file_id,
            "file_size": media.file_size,
            "file_type": media.file_type,
            "mime_type": media.mime_type,
            "caption": media.caption if hasattr(media, "caption") else None
        }
        await self.col.update_one(
            {"file_id": media.file_id},
            {"$set": file_data},
            upsert=True
        )

    async def get_search_results(self, query, max_results=10, offset=0):
        """Search files using regex keyword matching"""
        keywords = query.split()
        regex_pattern = ".*".join(keywords)
        filter_query = {"file_name": {"$regex": regex_pattern, "$options": "i"}}
        
        cursor = self.col.find(filter_query).skip(offset).limit(max_results)
        results = await cursor.to_list(length=max_results)
        total = await self.col.count_documents(filter_query)
        return results, total

    async def get_file(self, file_id):
        """Retrieve single file by file_id"""
        return await self.col.find_one({"file_id": file_id})

    async def total_files(self):
        """Count total indexed files"""
        return await self.col.count_documents({})

    async def total_users(self):
        """Count total bot users"""
        return await self.users.count_documents({})

    async def add_user(self, user_id, name="User"):
        """Register or update user (safe with optional name)"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name if name else "User"}},
            upsert=True
        )

    async def update_verify(self, user_id, verify_time):
        """Update 24hr verify status"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"verified_until": verify_time}},
            upsert=True
        )

    async def is_verified(self, user_id, current_time):
        """Check if user verification is still valid"""
        user = await self.users.find_one({"user_id": user_id})
        if not user or "verified_until" not in user:
            return False
        return user["verified_until"] > current_time

# Bot.py instances & aliases
db_instance = Database()
db = db_instance
