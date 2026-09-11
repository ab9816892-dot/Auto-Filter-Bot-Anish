import logging
import time
from motor.motor_asyncio import AsyncIOMotorClient
import info

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(info.DATABASE_URI)
db = client[info.DATABASE_NAME]

col = db["files_collection"]
users_col = db["verified_users"]

async def save_file(media):
    file_id = getattr(media, "file_id", None)
    if not file_id:
        return False

    file_name = getattr(media, "file_name", "Unknown")
    file_size = getattr(media, "file_size", 0)
    mime_type = getattr(media, "mime_type", "video/mp4")

    file_doc = {
        "_id": file_id,
        "file_name": file_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "timestamp": time.time()
    }
    try:
        await col.update_one({"_id": file_id}, {"$set": file_doc}, upsert=True)
        return True
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False

async def get_search_results(query, max_results=info.MAX_RESULTS):
    query = query.strip()
    regex_pattern = f".*{query}.*"
    filter_query = {"file_name": {"$regex": regex_pattern, "$options": "i"}}
    try:
        cursor = col.find(filter_query, {"_id": 1, "file_name": 1, "file_size": 1}).limit(max_results)
        return await cursor.to_list(length=max_results)
    except Exception as e:
        logger.error(f"Search query error: {e}")
        return []

async def is_user_verified(user_id):
    if not info.USE_SHORTLINK:
        return True
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        return False
    return (time.time() - user.get("verified_time", 0)) < info.VERIFY_EXPIRE

async def set_user_verified(user_id):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"verified_time": time.time()}},
        upsert=True
    )
