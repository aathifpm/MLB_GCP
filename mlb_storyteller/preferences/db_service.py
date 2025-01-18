from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from mlb_storyteller.preferences.models import UserPreferencesDB, UserPreferencesUpdate, UserStoryHistory
from mlb_storyteller.config import MONGODB_URI, MONGODB_DB_NAME

class DatabaseService:
    """Database service for MLB Storyteller."""

    def __init__(self):
        """Initialize database connection."""
        self.client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB_NAME]
        self.preferences_collection = self.db.user_preferences
        self.history_collection = self.db.story_history

    async def create_user_preferences(self, user_id: str, preferences: UserPreferencesDB) -> UserPreferencesDB:
        """Create new user preferences."""
        preferences_dict = preferences.model_dump(by_alias=True)
        if "_id" in preferences_dict and preferences_dict["_id"]:
            preferences_dict["_id"] = ObjectId(preferences_dict["_id"])
        else:
            preferences_dict["_id"] = ObjectId()
        
        preferences.user_id = user_id
        result = await self.preferences_collection.insert_one(preferences_dict)
        return await self.get_user_preferences(user_id)

    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferencesDB]:
        """Get user preferences by user ID."""
        preferences = await self.preferences_collection.find_one({"user_id": user_id})
        if preferences:
            preferences["_id"] = str(preferences["_id"])
            return UserPreferencesDB(**preferences)
        return None

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: UserPreferencesUpdate
    ) -> Optional[UserPreferencesDB]:
        """Update user preferences."""
        update_data = preferences.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        result = await self.preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )

        if result.modified_count:
            return await self.get_user_preferences(user_id)
        return None

    async def add_story_history(self, history: UserStoryHistory) -> UserStoryHistory:
        """Add a story generation to user's history."""
        history_dict = history.model_dump(by_alias=True)
        if "_id" in history_dict and history_dict["_id"]:
            history_dict["_id"] = ObjectId(history_dict["_id"])
        else:
            history_dict["_id"] = ObjectId()
            
        result = await self.history_collection.insert_one(history_dict)
        created = await self.history_collection.find_one({"_id": result.inserted_id})
        if created:
            created["_id"] = str(created["_id"])
            return UserStoryHistory(**created)
        raise HTTPException(status_code=500, detail="Failed to create history record")

    async def get_user_story_history(self, user_id: str, limit: int = 10) -> List[UserStoryHistory]:
        """Get user's story generation history."""
        cursor = self.history_collection.find({"user_id": user_id})
        cursor.sort("generated_at", -1).limit(limit)
        
        history = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(UserStoryHistory(**doc))
        
        return history

    async def get_popular_teams(self, limit: int = 5) -> List[dict]:
        """Get most popular favorite teams."""
        pipeline = [
            {"$group": {
                "_id": "$favorite_team",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.preferences_collection.aggregate(pipeline)
        popular_teams = []
        async for doc in cursor:
            if doc["_id"]:  # Exclude None values
                popular_teams.append({
                    "team": doc["_id"],
                    "count": doc["count"]
                })
        
        return popular_teams

    async def get_popular_players(self, limit: int = 5) -> List[dict]:
        """Get most popular favorite players."""
        pipeline = [
            {"$unwind": "$favorite_players"},
            {"$group": {
                "_id": "$favorite_players",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.preferences_collection.aggregate(pipeline)
        popular_players = []
        async for doc in cursor:
            popular_players.append({
                "player": doc["_id"],
                "count": doc["count"]
            })
        
        return popular_players