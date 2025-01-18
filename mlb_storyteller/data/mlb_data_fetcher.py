import requests
import pandas as pd
from typing import Dict, List, Optional, Union
import os
from dotenv import load_dotenv
from mlb_storyteller.cache.redis_service import RedisService
import json

load_dotenv()

class MLBDataFetcher:
    """Handles fetching and processing MLB data from the official Stats API."""
    
    def __init__(self):
        """Initialize the MLB data fetcher."""
        self.base_url = "https://statsapi.mlb.com/api"
        self.version = "v1.1"
        self.cache = RedisService()
        self.sport_id = 1  # MLB
    
    def _process_endpoint_url(self, endpoint_url: str, pop_key: Optional[str] = None) -> pd.DataFrame:
        """
        Process MLB Stats API endpoint results.
        
        Args:
            endpoint_url: The URL to fetch data from
            pop_key: Optional key to pop from response JSON
            
        Returns:
            Processed data as pandas DataFrame
        """
        try:
            response = requests.get(endpoint_url)
            response.raise_for_status()
            data = json.loads(response.content)
            
            if pop_key:
                df_result = pd.json_normalize(data.pop(pop_key), sep='_')
            else:
                df_result = pd.json_normalize(data)
            
            return df_result
        except Exception as e:
            print(f"Error processing endpoint {endpoint_url}: {str(e)}")
            return pd.DataFrame()

    async def get_schedule(self, season: int, game_type: str = "R") -> Dict:
        """
        Fetch MLB schedule for a specific season.
        
        Args:
            season: The year to fetch schedule for
            game_type: Game type (R = Regular Season, P = Postseason, S = Spring Training)
            
        Returns:
            Dict containing schedule data
        """
        cache_key = f"schedule_{season}_{game_type}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        endpoint = f"{self.base_url}/v1/schedule"
        params = {
            "sportId": self.sport_id,
            "season": season,
            "gameType": game_type,
            "hydrate": "team,venue,probablePitcher"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            schedule_data = response.json()
            
            # Cache for 1 hour
            await self.cache.set(cache_key, schedule_data, expire=3600)
            
            return schedule_data
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch schedule: {str(e)}")

    async def get_game_data(self, game_pk: str) -> Dict:
        """
        Fetch detailed game data from MLB Stats API with caching.
        
        Args:
            game_pk: The game ID to fetch data for
            
        Returns:
            Dict containing processed game data
        """
        # Try to get from cache first
        cached_data = await self.cache.get_game_data(game_pk)
        if cached_data:
            return cached_data
            
        # If not in cache, fetch from API
        endpoint = f"{self.base_url}/{self.version}/game/{game_pk}/feed/live"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            game_data = response.json()
            
            # Process the raw game data
            processed_data = self._process_game_data(game_data)
            
            # Cache the processed data
            await self.cache.set_game_data(game_pk, processed_data)
            
            return processed_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Try to get schedule data for this game
                schedule_data = await self._get_game_schedule(game_pk)
                if schedule_data:
                    return schedule_data
                raise Exception(f"Game ID {game_pk} not found")
            raise Exception(f"Failed to fetch game data: {str(e)}")

    async def _get_game_schedule(self, game_pk: str) -> Optional[Dict]:
        """Get schedule data for a game."""
        endpoint = f"{self.base_url}/v1/schedule"
        params = {
            "gamePk": game_pk,
            "hydrate": "probablePitcher,venue,weather,flags"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('dates') or not data['dates'][0].get('games'):
                return None
                
            game = data['dates'][0]['games'][0]
            return {
                'summary': {
                    'home_team': game['teams']['home']['team']['name'],
                    'away_team': game['teams']['away']['team']['name'],
                    'home_score': game['teams']['home'].get('score'),
                    'away_score': game['teams']['away'].get('score'),
                    'status': game['status']['detailedState'],
                    'venue': game['venue']['name'],
                    'game_date': game['gameDate'],
                    'game_pk': game['gamePk']
                },
                'teams': {
                    'home': game['teams']['home'],
                    'away': game['teams']['away']
                },
                'venue': game['venue'],
                'weather': game.get('weather', {}),
                'probable_pitchers': {
                    'home': game['teams']['home'].get('probablePitcher'),
                    'away': game['teams']['away'].get('probablePitcher')
                }
            }
        except Exception as e:
            print(f"Error getting game schedule: {e}")
            return None

    def _extract_player_info(self, player: Dict) -> Dict:
        """Extract relevant player information from roster data."""
        person = player.get("person", {})
        position = player.get("position", {})
        stats = player.get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
        
        return {
            "id": person.get("id"),
            "fullName": person.get("fullName"),
            "primaryNumber": person.get("primaryNumber"),
            "birthDate": person.get("birthDate"),
            "currentAge": person.get("currentAge"),
            "height": person.get("height"),
            "weight": person.get("weight"),
            "position": position.get("abbreviation"),
            "status": player.get("status", {}).get("description"),
            "stats": stats
        }

    async def get_team_roster(self, team_id: str, season: Optional[int] = None) -> List[Dict]:
        """
        Fetch team roster from MLB Stats API.
        
        Args:
            team_id: The team ID to fetch roster for
            season: Optional season year (defaults to current year)
            
        Returns:
            List of player information dictionaries
        """
        if not season:
            season = pd.Timestamp.now().year
            
        cache_key = f"roster_{team_id}_{season}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        endpoint = f"{self.base_url}/v1/teams/{team_id}/roster"
        params = {
            "season": season,
            "rosterType": "active",
            "hydrate": "person(stats(type=season,season={season}))"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            roster_data = response.json()
            
            if not roster_data.get("roster"):
                raise Exception(f"No roster data found for team ID {team_id}")
            
            # Process roster data
            processed_roster = []
            for player in roster_data["roster"]:
                person = player.get("person", {})
                position = player.get("position", {})
                stats = person.get("stats", [])
                
                # Find season stats if available
                season_stats = {}
                for stat in stats:
                    if stat.get("type", {}).get("displayName") == "statsSingleSeason":
                        season_stats = stat.get("splits", [{}])[0].get("stat", {})
                        break
                
                player_info = {
                    "id": person.get("id"),
                    "fullName": person.get("fullName"),
                    "jerseyNumber": player.get("jerseyNumber"),
                    "position": {
                        "code": position.get("code"),
                        "name": position.get("name"),
                        "type": position.get("type"),
                        "abbreviation": position.get("abbreviation")
                    },
                    "status": player.get("status", {}).get("description"),
                    "stats": season_stats,
                    "batSide": person.get("batSide", {}).get("code"),
                    "pitchHand": person.get("pitchHand", {}).get("code"),
                    "primaryNumber": person.get("primaryNumber"),
                    "birthDate": person.get("birthDate"),
                    "currentAge": person.get("currentAge"),
                    "birthCity": person.get("birthCity"),
                    "birthCountry": person.get("birthCountry"),
                    "height": person.get("height"),
                    "weight": person.get("weight"),
                    "active": person.get("active", True)
                }
                processed_roster.append(player_info)
                
            # Cache for 1 hour
            await self.cache.set(cache_key, processed_roster, expire=3600)
            
            return processed_roster
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch team roster: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing roster data: {str(e)}")

    async def get_player_stats(self, player_id: str, season: Optional[int] = None) -> Dict:
        """
        Fetch player statistics from MLB Stats API.
        
        Args:
            player_id: The player ID to fetch stats for
            season: Optional season year (defaults to current year)
            
        Returns:
            Dict containing player statistics
        """
        if not season:
            season = pd.Timestamp.now().year
            
        cache_key = f"player_stats_{player_id}_{season}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        endpoint = f"{self.base_url}/v1/people/{player_id}"
        params = {
            "hydrate": f"stats(group=[hitting,pitching,fielding],type=season,season={season})"
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            player_data = response.json()
            
            if "people" not in player_data or not player_data["people"]:
                raise Exception(f"Player ID {player_id} not found")
                
            player = player_data["people"][0]
            stats_data = player.get("stats", [])
            
            # Process stats data
            processed_stats = self._process_player_stats({"stats": stats_data})
            
            # Add player info
            processed_stats["player_info"] = {
                "id": player.get("id"),
                "fullName": player.get("fullName"),
                "primaryNumber": player.get("primaryNumber"),
                "currentTeam": player.get("currentTeam", {}).get("name"),
                "primaryPosition": player.get("primaryPosition", {}).get("abbreviation")
            }
            
            # Cache for 1 hour
            await self.cache.set(cache_key, processed_stats, expire=3600)
            
            return processed_stats
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch player stats: {str(e)}")

    def _process_game_data(self, raw_data: Dict) -> Dict:
        """Process raw MLB game data into a storytelling-friendly format."""
        try:
            linescore = raw_data.get('liveData', {}).get('linescore', {})
            boxscore = raw_data.get('liveData', {}).get('boxscore', {})
            game_info = raw_data.get('gameData', {})
            plays = raw_data.get('liveData', {}).get('plays', {})
            
            # Core game narrative elements
            game_data = {
                'summary': {
                    'home_team': game_info.get('teams', {}).get('home', {}).get('name'),
                    'away_team': game_info.get('teams', {}).get('away', {}).get('name'),
                    'home_score': linescore.get('teams', {}).get('home', {}).get('runs', 0),
                    'away_score': linescore.get('teams', {}).get('away', {}).get('runs', 0),
                    'status': game_info.get('status', {}).get('detailedState'),
                    'venue': game_info.get('venue', {}).get('name'),
                    'game_date': game_info.get('datetime', {}).get('dateTime')
                }
            }

            # Special game situations that add drama
            flags = game_info.get('flags', {})
            if any([flags.get('noHitter'), flags.get('perfectGame')]):
                game_data['special_alert'] = {
                    'no_hitter': flags.get('noHitter', False),
                    'perfect_game': flags.get('perfectGame', False)
                }

            # Current game situation (only if game is live)
            if game_info.get('status', {}).get('abstractGameState') == 'Live':
                game_data['current_action'] = {
                    'inning': f"{linescore.get('inningState', '')} {linescore.get('currentInning', '')}",
                    'count': f"{linescore.get('balls', 0)}-{linescore.get('strikes', 0)}, {linescore.get('outs', 0)} out(s)",
                    'bases': self._get_runners_narrative(plays.get('currentPlay', {}))
                }

            # Key plays that shaped the game
            key_plays = self._extract_narrative_moments(plays.get('allPlays', []))
            if key_plays:
                game_data['key_plays'] = key_plays

            # Standout performances
            hitting = self._extract_notable_hitting(boxscore)
            pitching = self._extract_notable_pitching(boxscore)
            if hitting or pitching:
                game_data['standouts'] = {}
                if hitting:
                    game_data['standouts']['hitting'] = hitting
                if pitching:
                    game_data['standouts']['pitching'] = pitching

            # Game result (if complete)
            if game_info.get('status', {}).get('abstractGameState') == 'Final':
                decisions = raw_data.get('liveData', {}).get('decisions', {})
                game_data['result'] = {
                    'winner': self._determine_winner(linescore.get('teams', {})),
                    'winning_pitcher': decisions.get('winner', {}).get('fullName'),
                    'save': decisions.get('save', {}).get('fullName') if decisions.get('save') else None
                }
            
            return game_data
            
        except Exception as e:
            raise Exception(f"Failed to process game data: {str(e)}")

    def _extract_narrative_moments(self, plays: List) -> List[Dict]:
        """Extract only the most significant moments from the game."""
        key_moments = []
        
        for play in plays:
            if not isinstance(play, dict):
                continue
                
            about = play.get('about', {})
            result = play.get('result', {})
            
            # Only include truly significant plays
            if (about.get('isScoringPlay', False) or
                'home_run' in result.get('event', '').lower() or
                result.get('rbi', 0) >= 2 or
                (about.get('inning') >= 7 and about.get('isComplete') and about.get('hasOut'))):  # Late-game crucial outs
                
                key_moments.append({
                    'inning': f"{about.get('halfInning', '').title()} {about.get('inning')}",
                    'description': result.get('description'),
                    'score': f"{about.get('awayScore', 0)}-{about.get('homeScore', 0)}"
                })
        
        return key_moments

    def _extract_notable_hitting(self, boxscore: Dict) -> List[Dict]:
        """Extract only exceptional hitting performances."""
        standouts = []
        
        for team_type in ['home', 'away']:
            team_batters = boxscore.get('teams', {}).get(team_type, {}).get('batters', [])
            for batter_id in team_batters:
                batter = boxscore.get('teams', {}).get(team_type, {}).get('players', {}).get(f'ID{batter_id}', {})
                stats = batter.get('stats', {}).get('batting', {})
                
                # Only truly notable performances
                if (stats.get('hits', 0) >= 3 or
                    stats.get('homeRuns', 0) >= 1 or
                    stats.get('rbi', 0) >= 3):
                    
                    standouts.append({
                        'name': batter.get('person', {}).get('fullName'),
                        'highlight': f"{stats.get('hits')}-{stats.get('atBats')}, {stats.get('homeRuns')} HR, {stats.get('rbi')} RBI"
                    })
        
        return standouts

    def _extract_notable_pitching(self, boxscore: Dict) -> List[Dict]:
        """Extract only exceptional pitching performances."""
        standouts = []
        
        for team_type in ['home', 'away']:
            team_pitchers = boxscore.get('teams', {}).get(team_type, {}).get('pitchers', [])
            for pitcher_id in team_pitchers:
                pitcher = boxscore.get('teams', {}).get(team_type, {}).get('players', {}).get(f'ID{pitcher_id}', {})
                stats = pitcher.get('stats', {}).get('pitching', {})
                
                # Only truly notable performances
                ip = float(stats.get('inningsPitched', '0.0'))
                if (ip >= 6.0 and stats.get('earnedRuns', 0) <= 2) or stats.get('strikeOuts', 0) >= 8:
                    standouts.append({
                        'name': pitcher.get('person', {}).get('fullName'),
                        'highlight': f"{stats.get('inningsPitched')} IP, {stats.get('strikeOuts')} K, {stats.get('earnedRuns')} ER"
                    })
        
        return standouts

    def _get_runners_narrative(self, current_play: Dict) -> str:
        """Create a concise description of runners on base."""
        if not current_play or 'matchup' not in current_play:
            return "Bases empty"
            
        matchup = current_play['matchup']
        bases = []
        
        for base in ['first', 'second', 'third']:
            if matchup.get(f'postOn{base.capitalize()}'):
                bases.append(base[0].upper())  # Just use F, S, T for bases
                
        return "Bases: " + ("-".join(bases) if bases else "empty")

    def _format_weather_narrative(self, weather: Dict) -> str:
        """Convert weather data into a narrative-friendly format."""
        if weather.get('condition') == 'Dome':
            return "Game played indoors"
        
        conditions = []
        if temp := weather.get('temp'):
            conditions.append(f"{temp}°F")
        if wind := weather.get('wind'):
            conditions.append(f"winds {wind}")
            
        return ", ".join(conditions) if conditions else "Weather information unavailable"

    def _get_batter_narrative(self, current_play: Dict) -> str:
        """Create a narrative description of the current batter."""
        if not current_play or 'matchup' not in current_play:
            return "No batter data available"
            
        batter = current_play.get('matchup', {}).get('batter', {})
        stats = current_play.get('matchup', {}).get('batterHotColdZones', [])
        
        name = batter.get('fullName', 'Unknown batter')
        if not stats:
            return name
            
        # Add relevant batting stats if available
        batting_line = []
        if avg := stats[0].get('avg'):
            batting_line.append(f"batting {avg}")
        if hr := stats[0].get('homeRuns'):
            batting_line.append(f"{hr} HR")
            
        return f"{name} ({', '.join(batting_line)})" if batting_line else name

    def _get_pitcher_narrative(self, current_play: Dict) -> str:
        """Create a narrative description of the current pitcher."""
        if not current_play or 'matchup' not in current_play:
            return "No pitcher data available"
            
        pitcher = current_play.get('matchup', {}).get('pitcher', {})
        stats = current_play.get('matchup', {}).get('pitcherHotColdZones', [])
        
        name = pitcher.get('fullName', 'Unknown pitcher')
        if not stats:
            return name
            
        # Add relevant pitching stats if available
        pitching_line = []
        if era := stats[0].get('era'):
            pitching_line.append(f"ERA {era}")
        if ip := stats[0].get('inningsPitched'):
            pitching_line.append(f"{ip} IP")
            
        return f"{name} ({', '.join(pitching_line)})" if pitching_line else name

    def _format_player_name(self, player: Dict) -> str:
        """Format player name for narrative purposes."""
        return player.get('fullName', 'Unknown player')

    def _determine_winner(self, teams: Dict) -> str:
        """Determine the winning team name."""
        if not teams:
            return "Unknown"
            
        home_score = teams.get('home', {}).get('runs', 0)
        away_score = teams.get('away', {}).get('runs', 0)
        
        if home_score > away_score:
            return teams.get('home', {}).get('team', {}).get('name', 'Home Team')
        return teams.get('away', {}).get('team', {}).get('name', 'Away Team')

    def _process_player_stats(self, stats_data: Dict) -> Dict:
        """Process player statistics data."""
        processed_stats = {
            "hitting": {},
            "pitching": {},
            "fielding": {}
        }
        
        for stat_group in stats_data.get("stats", []):
            group_name = stat_group.get("group", {}).get("displayName", "").lower()
            if group_name in processed_stats:
                splits = stat_group.get("splits", [])
                if splits:
                    processed_stats[group_name] = splits[0].get("stat", {})
        
        return processed_stats 