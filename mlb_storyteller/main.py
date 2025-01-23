from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mlb_storyteller.api.routes import audio
from mlb_storyteller.data.mlb_data_fetcher import MLBDataFetcher
from mlb_storyteller.story_engine.story_generator import StoryGenerator
from mlb_storyteller.cache.redis_service import RedisService
from mlb_storyteller.preferences.db_service import DatabaseService
from mlb_storyteller.preferences.models import UserPreferencesDB, UserStoryHistory
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Load environment variables
load_dotenv()

# Pydantic models for request/response validation
class UserPreferences(BaseModel):
    favorite_team: str
    favorite_players: List[str]
    preferred_style: str

class StoryRequest(BaseModel):
    game_id: str
    preferences: dict

# Initialize FastAPI app
app = FastAPI(
    title="MLB Storyteller",
    description="An AI-powered baseball storytelling platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:8000",  # FastAPI server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Mount static files (for production build)
static_dir = os.path.join(os.path.dirname(__file__), "frontend", "build")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Include routers
app.include_router(audio.router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check the health of the application and its dependencies."""
    try:
        # Check Redis connection
        redis_service = RedisService()
        redis_health = await redis_service.health_check()

        # Check MLB API connection
        mlb_service = MLBDataFetcher()
        schedule = await mlb_service.get_schedule(2024, "R")
        mlb_health = bool(schedule)

        return {
            "status": "healthy",
            "dependencies": {
                "redis": redis_health,
                "mlb_api": mlb_health
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Game data endpoints
@app.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get detailed game data."""
    try:
        mlb_service = MLBDataFetcher()
        game_data = await mlb_service.get_game_data(game_id)
        if not game_data:
            raise HTTPException(status_code=404, detail=f"Game ID {game_id} not found")
        return game_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule")
async def get_schedule(season: int, game_type: str = "R"):
    """Get MLB schedule."""
    mlb_service = MLBDataFetcher()
    return await mlb_service.get_schedule(season, game_type)

@app.get("/teams/{team_id}/roster")
async def get_team_roster(team_id: str, season: int = None):
    """Get team roster."""
    mlb_service = MLBDataFetcher()
    return await mlb_service.get_team_roster(team_id, season)

@app.get("/players/{player_id}/stats")
async def get_player_stats(player_id: str, season: int = None):
    """Get player statistics."""
    mlb_service = MLBDataFetcher()
    return await mlb_service.get_player_stats(player_id, season)

# Additional endpoints required by test_api.py

@app.get("/")
async def get_api_info():
    """Get API information and documentation."""
    return {
        "name": "MLB Storyteller API",
        "version": "1.0.0",
        "description": "An AI-powered baseball storytelling platform"
    }

@app.get("/styles")
async def get_available_styles():
    """Get available storytelling styles."""
    return {
        "styles": [
            "dramatic",
            "analytical",
            "casual",
            "humorous"
        ]
    }

@app.post("/users/{user_id}/preferences")
async def create_user_preferences(user_id: str, preferences: UserPreferences):
    """Create or update user preferences."""
    try:
        db_service = DatabaseService()
        # Convert to UserPreferencesDB model
        db_preferences = UserPreferencesDB(
            user_id=user_id,
            favorite_team=preferences.favorite_team,
            favorite_players=preferences.favorite_players,
            preferred_style=preferences.preferred_style,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        result = await db_service.create_user_preferences(user_id, db_preferences)
        return {"status": "success", "message": "Preferences saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user preferences."""
    try:
        db_service = DatabaseService()
        preferences = await db_service.get_user_preferences(user_id)
        if not preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/history")
async def get_user_history(user_id: str):
    """Get user's story generation history."""
    try:
        db_service = DatabaseService()
        # Ensure user_id is valid before querying
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user ID")
            
        history = await db_service.get_user_story_history(user_id)
        # Convert history items to dict and handle ObjectId
        history_list = []
        for item in history:
            item_dict = item.model_dump()
            if "_id" in item_dict:
                item_dict["_id"] = str(item_dict["_id"])
            history_list.append(item_dict)
        return {"history": history_list}
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            return {"history": []}  # Return empty history for new users
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/popular-teams")
async def get_popular_teams():
    """Get popular teams based on user preferences."""
    try:
        db_service = DatabaseService()
        teams = await db_service.get_popular_teams()
        return {"teams": teams or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update the generate-story endpoint to match test requirements
@app.post("/generate-story")
async def generate_story(story_request: StoryRequest, user_id: Optional[str] = None):
    """Generate a story for a game with user preferences."""
    try:
        story_generator = StoryGenerator()
        mlb_service = MLBDataFetcher()
        
        # Validate game ID format
        if not story_request.game_id or not story_request.game_id.isdigit():
            raise HTTPException(status_code=400, detail="Invalid game ID format")
        
        # Get game data - let MLBDataFetcher handle the validation and preview data
        try:
            game_data = await mlb_service.get_game_data(story_request.game_id)
            if not game_data:
                raise HTTPException(status_code=404, detail=f"Game ID {story_request.game_id} not found")
            
            # Generate story
            story = await story_generator.generate_story(game_data, story_request.preferences)
            
            # Save to user history if user_id provided
            if user_id:
                try:
                    db_service = DatabaseService()
                    history_entry = UserStoryHistory(
                        user_id=user_id,
                        game_id=story_request.game_id,
                        story=story,
                        generated_at=datetime.utcnow()
                    )
                    await db_service.add_story_history(history_entry)
                except Exception as e:
                    # Log the error but don't fail the story generation
                    print(f"Failed to save story history: {str(e)}")
            
            return story
            
        except Exception as e:
            if "Game ID" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "mlb_storyteller.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload during development
        workers=1     # Use single worker for development
    ) 