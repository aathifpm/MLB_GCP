from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from typing import List, Optional, Any, Annotated
from datetime import datetime
from bson import ObjectId

# Custom type for handling MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(lambda x: str(ObjectId(x)) if not isinstance(x, ObjectId) else str(x))]

class UserPreferencesDB(BaseModel):
    """Database model for user preferences."""
    id: PyObjectId = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    favorite_team: Optional[str] = None
    favorite_players: List[str] = []
    preferred_style: str = "dramatic"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "test_user",
                "favorite_team": "New York Yankees",
                "favorite_players": ["Aaron Judge", "Gerrit Cole"],
                "preferred_style": "dramatic"
            }
        }
    )

class UserPreferencesUpdate(BaseModel):
    """Model for updating user preferences."""
    favorite_team: Optional[str] = None
    favorite_players: Optional[List[str]] = None
    preferred_style: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "favorite_team": "New York Yankees",
                "favorite_players": ["Aaron Judge"],
                "preferred_style": "dramatic"
            }
        }
    )

class UserStoryHistory(BaseModel):
    """Model for tracking user's story generation history."""
    id: PyObjectId = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    game_id: str
    narrative_style: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "user_id": "test_user",
                "game_id": "716093",
                "narrative_style": "dramatic"
            }
        }
    )