import asyncio
import json
from mlb_storyteller.data.mlb_data_fetcher import MLBDataFetcher
from datetime import datetime

async def test_mlb_api():
    """Test various MLB API endpoints and data processing."""
    
    fetcher = MLBDataFetcher()
    
    # Test 1: Get current MLB season schedule
    print("\n=== Testing MLB Schedule API ===")
    try:
        response = await fetcher.get_schedule(
            season=2024,
            game_type="R"  # Regular season games
        )
        
        if not response.get('dates'):
            print("No schedule data available")
            return
            
        print(f"Found {len(response['dates'])} game dates")
        
        # Print first game details
        if response['dates']:
            first_game = response['dates'][0]['games'][0]
            print("\nFirst Game Details:")
            print(f"Date: {first_game['officialDate']}")
            print(f"Teams: {first_game['teams']['away']['team']['name']} @ {first_game['teams']['home']['team']['name']}")
            print(f"Game ID: {first_game['gamePk']}")
            print(f"Status: {first_game['status']['detailedState']}")
            
            # Use this game ID for next test
            test_game_pk = first_game['gamePk']
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        test_game_pk = "716463"  # Fallback to a known game ID
    
    # Test 2: Get detailed game data with GUMBO implementation
    print("\n=== Testing Enhanced GUMBO Game Data API ===")
    try:
        game_data = await fetcher.get_game_data(str(test_game_pk))
        
        if not game_data:
            print("No game data available")
            return
            
        # Test basic game information
        if game_data.get('summary'):
            print("\nGame Summary:")
            print(json.dumps(game_data['summary'], indent=2))
        
        # Test current game situation
        if game_data.get('situation'):
            print("\nCurrent Game Situation:")
            print(json.dumps(game_data['situation'], indent=2))
        
        # Test team statistics
        if game_data.get('stats'):
            print("\nTeam Statistics:")
            print("Home Team Batting:")
            print(json.dumps(game_data['stats']['batting']['home'], indent=2))
            print("\nAway Team Pitching:")
            print(json.dumps(game_data['stats']['pitching']['away'], indent=2))
        
        # Test game leaders
        if game_data.get('leaders'):
            print("\nGame Leaders:")
            print(json.dumps(game_data['leaders'], indent=2))
        
        # Test plays information
        if game_data.get('plays', {}).get('all_plays'):
            print("\nKey Plays (first 3):")
            for play in game_data['plays']['all_plays'][:3]:
                print(f"Inning {play['inning']} {play.get('half_inning', '')}: {play['description']}")
            
            if game_data['plays'].get('scoring_plays'):
                print("\nScoring Plays:")
                for index in game_data['plays']['scoring_plays'][:3]:
                    if 0 <= index < len(game_data['plays']['all_plays']):
                        play = game_data['plays']['all_plays'][index]
                        print(f"Inning {play['inning']} {play.get('half_inning', '')}: {play['description']}")
    except Exception as e:
        print(f"Error fetching game data: {e}")
    
    # Test 3: Get team roster with enhanced player info
    print("\n=== Testing Enhanced Team Roster API ===")
    try:
        # Los Angeles Dodgers team ID: 119
        roster = await fetcher.get_team_roster("119", season=2024)
        
        if not roster:
            print("No roster data available")
            return
            
        print("\nDodgers Roster (first 5 players with detailed info):")
        for player in roster[:5]:
            print(f"\nPlayer: {player.get('fullName', 'N/A')}")
            print(f"Position: {player.get('position', 'N/A')}")
            print(f"Jersey #: {player.get('jerseyNumber', 'N/A')}")
            print(f"Status: {player.get('status', 'Active')}")
    except Exception as e:
        print(f"Error fetching roster: {e}")
    
    # Test 4: Get enhanced player stats
    print("\n=== Testing Enhanced Player Stats API ===")
    try:
        # Shohei Ohtani's player ID: 660271
        player_stats = await fetcher.get_player_stats("660271", season=2023)
        
        if not player_stats:
            print("No player stats available")
            return
            
        print("\nShohei Ohtani's 2023 Stats:")
        
        if player_stats.get('hitting'):
            print("\nBatting Stats:")
            print(json.dumps(player_stats['hitting'], indent=2))
        
        if player_stats.get('pitching'):
            print("\nPitching Stats:")
            print(json.dumps(player_stats['pitching'], indent=2))
        
        if player_stats.get('fielding'):
            print("\nFielding Stats:")
            print(json.dumps(player_stats['fielding'], indent=2))
    except Exception as e:
        print(f"Error fetching player stats: {e}")

if __name__ == "__main__":
    asyncio.run(test_mlb_api()) 