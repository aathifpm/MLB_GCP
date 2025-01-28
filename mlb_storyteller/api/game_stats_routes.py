from fastapi import APIRouter, HTTPException
from ..services.mlb_stats_service import MLBStatsService
from ..data.home_runs_fetcher import HomeRunsFetcher
from typing import Dict, List
import pandas as pd

router = APIRouter()
mlb_stats_service = MLBStatsService()
home_runs_fetcher = HomeRunsFetcher()

@router.get("/api/games/{game_pk}/feed", response_model=Dict)
async def get_game_feed(game_pk: str):
    """Get complete game feed data."""
    try:
        feed_data = mlb_stats_service.get_game_feed(game_pk)
        if not feed_data:
            raise HTTPException(status_code=404, detail="Game feed not found")
        return feed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/games/{game_pk}/content", response_model=Dict)
async def get_game_content(game_pk: str):
    """Get game content including highlights."""
    try:
        content_data = mlb_stats_service.get_game_content(game_pk)
        if not content_data:
            raise HTTPException(status_code=404, detail="Game content not found")
        return content_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/games/{game_pk}/highlights", response_model=List[Dict])
async def get_game_highlights(game_pk: str):
    """Get game highlights including home runs."""
    try:
        highlights = mlb_stats_service.get_game_highlights(game_pk)
        return highlights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/teams/{team_id}/logo")
async def get_team_logo(team_id: str):
    """Get team logo URL."""
    try:
        logo_url = mlb_stats_service.get_team_logo(team_id)
        if not logo_url:
            raise HTTPException(status_code=404, detail="Team logo not found")
        return {"logo_url": logo_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/players/{player_id}/photo")
async def get_player_photo(player_id: str):
    """Get player photo URL."""
    try:
        photo_url = mlb_stats_service.get_player_photo(player_id)
        if not photo_url:
            raise HTTPException(status_code=404, detail="Player photo not found")
        return {"photo_url": photo_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/home-runs", response_model=List[Dict])
async def get_all_home_runs():
    """Get all home runs data across available seasons."""
    try:
        df = home_runs_fetcher.fetch_all_home_runs()
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/home-runs/{season}", response_model=List[Dict])
async def get_home_runs_by_season(season: str):
    """Get home runs data for a specific season."""
    try:
        df = home_runs_fetcher.fetch_home_runs_by_season(season)
        return df.to_dict('records')
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
