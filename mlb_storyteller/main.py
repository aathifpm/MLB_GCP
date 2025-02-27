from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from flask import Flask, jsonify
from flask_cors import CORS
from mlb_storyteller.api.game_stats_routes import router as game_stats_router
from pathlib import Path

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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    expose_headers=["*"],
    max_age=3600,
)

# Add custom middleware for additional headers
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response.headers["Access-Control-Max-Age"] = "3600"
        
    return response

# Get the absolute path to the frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

# Add favicon route
@app.get('/favicon.ico', include_in_schema=False)
async def get_favicon():
    """Serve the favicon."""
    try:
        # First try to find the favicon in the static/images directory
        favicon_path = os.path.join(frontend_dir, "static", "images", "favicon.ico")
        if not os.path.exists(favicon_path):
            # If not found, try the static directory
            favicon_path = os.path.join(frontend_dir, "static", "favicon.ico")
            if not os.path.exists(favicon_path):
                # If still not found, use a default baseball icon
                favicon_path = os.path.join(frontend_dir, "static", "images", "baseball.ico")
                if not os.path.exists(favicon_path):
                    # If no favicon found at all, return 404
                    raise HTTPException(status_code=404, detail="Favicon not found")
        
        return FileResponse(
            favicon_path,
            media_type="image/x-icon",
            headers={"Cache-Control": "public, max-age=31536000"}
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error serving favicon: {str(e)}")

# Add OPTIONS endpoint handlers for CORS preflight requests
@app.options("/{path:path}")
async def options_handler(path: str):
    response = JSONResponse(content={"detail": "OK"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Include routers
app.include_router(audio.router, prefix="/api")
app.include_router(game_stats_router)

@app.get("/")
async def serve_index():
    """Serve the index.html file."""
    from fastapi.responses import FileResponse
    index_path = os.path.join(frontend_dir, "templates", "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail=f"Index file not found at {index_path}")
    return FileResponse(index_path)

@app.get("/quiz.html")
async def serve_quiz():
    """Serve the quiz.html file."""
    from fastapi.responses import FileResponse
    quiz_path = os.path.join(frontend_dir, "templates", "quiz.html")
    if not os.path.exists(quiz_path):
        raise HTTPException(status_code=404, detail="Quiz page not found")
    return FileResponse(quiz_path)

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
    
@app.post("/api/game/{game_id}/quiz")
async def get_game_quiz(game_id: str, user_prefs: dict = Body(...)):
    mlb_service = MLBDataFetcher()
    game_data = await mlb_service.get_game_data(game_id)
    processed_data = mlb_service._process_game_data(game_data)  # Use existing processing
    story_generator = StoryGenerator()
    quiz = await story_generator.generate_quiz(processed_data, user_prefs)
    return quiz

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the application in production mode
    uvicorn.run(
        "mlb_storyteller.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable auto-reload for production
        workers=4,     # Use multiple workers for production
        proxy_headers=True,  # Trust proxy headers 
        forwarded_allow_ips='*'  # Allow forwarded IPs
    )