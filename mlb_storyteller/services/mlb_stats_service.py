import requests
import pandas as pd
from typing import Dict, List, Optional
import os
import json
from datetime import datetime

# MLB Home Run datasets
HOME_RUN_DATASETS = {
    '2024': 'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2024-mlb-homeruns.csv',
    '2024_postseason': 'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2024-postseason-mlb-homeruns.csv',
    '2017': 'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2017-mlb-homeruns.csv',
    '2016': 'https://storage.googleapis.com/gcp-mlb-hackathon-2025/datasets/2016-mlb-homeruns.csv'
}

class MLBStatsService:
    """Service for interacting with MLB Stats API."""
    
    def __init__(self):
        """Initialize the MLB Stats service."""
        self.base_url = "https://statsapi.mlb.com/api"
        self.version = "v1"
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache', 'mlb_stats')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Default MLB logo URL (official MLB logo)
        self.default_team_logo = "https://www.mlbstatic.com/mlb.com/images/share/mlb-logo-on-light.jpg"
        
        # Load teams data
        self.teams_data = self._load_teams_data()
        

    def _load_teams_data(self) -> Dict:
        """Load MLB teams data."""
        try:
            endpoint = f"{self.base_url}/{self.version}/teams"
            params = {"sportId": 1}  # 1 for MLB
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Create a mapping of team IDs to team data
            teams = {}
            for team in data.get('teams', []):
                teams[team['id']] = team
            
            return teams
        except Exception as e:
            print(f"Error loading teams data: {str(e)}")
            return {}


    def get_game_feed(self, game_pk: str) -> Dict:
        try:
            # Use proper endpoint structure from notebook
            endpoint = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game feed: {str(e)}")
            return self._create_empty_game_data(game_pk)

    def _create_empty_game_data(self, game_pk: str) -> Dict:
        """Create empty game data structure with default values."""
        return {
            'gameData': {
                'teams': {
                    'home': {'id': None, 'name': 'Home Team'},
                    'away': {'id': None, 'name': 'Away Team'}
                },
                'venue': {'name': 'TBD'},
                'datetime': {'dateTime': None},
                'status': {'detailedState': 'Scheduled'}
            },
            'liveData': {
                'boxscore': {
                    'teams': {
                        'home': {'teamStats': {'batting': {}}},
                        'away': {'teamStats': {'batting': {}}}
                    }
                }
            }
            }

    def get_game_content(self, game_pk: str) -> Dict:
        """Get game content including highlights and media."""
        try:
            endpoint = f"{self.base_url}/{self.version}/game/{game_pk}/content"
            response = requests.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            # Validate the response structure
            if not data or 'highlights' not in data:
                print(f"Invalid game content data structure for game {game_pk}")
                return {'highlights': {'live': {'items': []}, 'highlights': {'items': []}}}
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game content: {str(e)}")
            return {'highlights': {'live': {'items': []}, 'highlights': {'items': []}}}
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing game content data: {str(e)}")
            return {'highlights': {'live': {'items': []}, 'highlights': {'items': []}}}

    def get_team_logo(self, team_id: str) -> str:
        """
        Get team logo URL from MLB static assets.
        
        Args:
            team_id: The team ID
            
        Returns:
            URL to the team's logo
        """
        if not team_id:
            return self.default_team_logo
            
        # Get team data from loaded teams
        team = self.teams_data.get(int(team_id))
        if not team:
            return self.default_team_logo
            
        return f'https://www.mlbstatic.com/team-logos/{team_id}.svg'

    def get_player_photo(self, player_id: str) -> str:
        """
        Get player photo URL from MLB static assets.
        
        Args:
            player_id: The player ID
            
        Returns:
            URL to the player's photo
        """
        return f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{player_id}/headshot/67/current'

    def get_game_highlights(self, game_pk: str) -> List[Dict]:
        try:
            endpoint = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/content"
            response = requests.get(endpoint)
            response.raise_for_status()
            content = response.json()
            
            # Process highlights as shown in notebook
            highlights = []
            if 'highlights' in content and 'highlights' in content['highlights']:
                for item in content['highlights']['highlights'].get('items', []):
                    highlight = {
                        'title': item.get('title'),
                        'description': item.get('description'),
                        'playbacks': item.get('playbacks', []),
                        'thumbnail': item.get('thumbnail', {}).get('href', '')
                    }
                    highlights.append(highlight)
            return highlights
        except Exception as e:
            print(f"Error getting highlights: {str(e)}")
            return []

    def get_home_run_stats(self, game_pk: str) -> List[Dict]:
        """Get detailed home run statistics for a game."""
        try:
            game_hrs = self.home_runs_df[self.home_runs_df['game_pk'] == game_pk]
            return game_hrs.to_dict('records')
        except Exception as e:
            print(f"Error getting home run stats: {str(e)}")
            return []

    def _get_best_thumbnail(self, cuts: List[Dict]) -> Optional[str]:
        """Get the best quality thumbnail URL from available cuts."""
        if not cuts:
            return None
        
        # Sort cuts by width to get the highest quality
        sorted_cuts = sorted(cuts, key=lambda x: x.get('width', 0), reverse=True)
        return sorted_cuts[0].get('src')

    def _get_playback_urls(self, playbacks: List[Dict]) -> List[Dict]:
        """Get playback URLs sorted by quality."""
        valid_playbacks = []
        
        for playback in playbacks:
            if playback.get('url') and playback.get('name'):
                valid_playbacks.append({
                    'url': playback['url'],
                    'name': playback['name']
                })
        
        # Sort by quality (assuming higher quality has larger names)
        return sorted(valid_playbacks, key=lambda x: len(x['name']), reverse=True)

    def get_home_run_moments(self, game_pk: str) -> List[Dict]:
        """Get all home run moments from a game."""
        game_data = self.get_game_feed(game_pk)
        home_runs = []
        
        if 'allPlays' in game_data:
            for play in game_data['allPlays']:
                if self._is_home_run(play):
                    home_run = {
                        'inning': play.get('about', {}).get('inning'),
                        'halfInning': play.get('about', {}).get('halfInning'),
                        'description': play.get('result', {}).get('description'),
                        'batter': {
                            'id': play.get('matchup', {}).get('batter', {}).get('id'),
                            'fullName': play.get('matchup', {}).get('batter', {}).get('fullName'),
                            'photo': self.get_player_photo(str(play.get('matchup', {}).get('batter', {}).get('id')))
                        }
                    }
                    home_runs.append(home_run)
        
        return home_runs

    def _is_home_run(self, play: Dict) -> bool:
        """Check if a play is a home run."""
        return play.get('result', {}).get('event') == 'Home Run'

    def _extract_game_stats(self, game_data: Dict) -> Dict:
        """Properly extract nested game stats"""
        try:
            live_data = game_data.get('liveData', {})
            plays = live_data.get('plays', {}).get('allPlays', [])
            boxscore = live_data.get('boxscore', {})
            
            return {
                'allPlays': plays,
                'boxscore': boxscore,
                # Rest of the extraction logic...
            }
        except Exception as e:
            print(f"Error extracting game stats: {str(e)}")
            return {}

    def get_historical_events(self, team_id: str) -> List:
        """Get notable historical events for a team"""
        try:
            endpoint = f"{self.base_url}/v1/teams/{team_id}/history"
            response = requests.get(endpoint)
            return response.json().get('events', [])
        except Exception as e:
            print(f"Error fetching history: {str(e)}")
            return [] 
