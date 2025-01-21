import asyncio
import aiohttp
import json
from typing import Any, Dict, Union
import sys
import os
import tempfile
import subprocess
from datetime import datetime

async def make_request(session: aiohttp.ClientSession, method: str, url: str, expect_binary: bool = False, **kwargs) -> Union[Dict[str, Any], bytes]:
    """Make HTTP request and handle errors."""
    try:
        async with session.request(method, url, **kwargs) as response:
            if response.status >= 400:
                error_text = await response.text()
                print(f"Error ({response.status}): {error_text}")
                return {"error": error_text}
                
            if expect_binary:
                return await response.read()
            else:
                return await response.json()
    except Exception as e:
        print(f"Request failed: {type(e).__name__}: {str(e)}")
        return {"error": str(e)}

def play_audio(audio_data: bytes) -> None:
    """Save audio data to downloads folder and optionally play it."""
    try:
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"story_narration_{timestamp}.mp3"
        file_path = os.path.join(downloads_dir, filename)
        
        # Save audio data
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        print(f"\nSaved audio to: {file_path}")
        
        # Optionally play the audio based on platform
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)  # Windows
            elif sys.platform == 'darwin':
                subprocess.run(['open', file_path])  # macOS
            else:
                subprocess.run(['xdg-open', file_path])  # Linux
                
            print("Playing audio... (Press Ctrl+C to stop)")
        except Exception as e:
            print(f"Note: Could not auto-play audio: {str(e)}")
            print("The audio file has been saved and can be played manually.")
            
    except Exception as e:
        print(f"Error handling audio: {str(e)}")

async def test_api():
    """Test the MLB Storyteller API endpoints."""
    base_url = "http://localhost:8000"  # Local FastAPI server
    mlb_api_url = "https://statsapi.mlb.com/api/v1"
    
    async with aiohttp.ClientSession() as session:
        print("\n=== MLB Storyteller API Tests ===\n")
        
        # 1. Test Health Check
        print("1. Testing Health Check...")
        result = await make_request(session, "GET", f"{base_url}/health")
        print(json.dumps(result, indent=2))

        # 2. Test Schedule API
        print("\n2. Testing Schedule API...")
        result = await make_request(
            session,
            "GET",
            f"{base_url}/schedule",
            params={"season": 2024, "game_type": "R"}
        )
        
        if "error" in result:
            print("Error accessing schedule API")
            return
            
        print("Schedule data retrieved successfully")
        if result.get('dates'):
            print(f"Found {len(result['dates'])} game dates")
            # Get first available game for further testing
            game_id = result['dates'][0]['games'][0]['gamePk']
            print(f"Using game ID: {game_id}")
        else:
            print("No games found in schedule")
            return

        # 3. Test Game Data API
        print("\n3. Testing Game Data API...")
        result = await make_request(
            session,
            "GET",
            f"{base_url}/games/{game_id}"
        )
        
        if result and "error" not in result:
            print("\nGame Summary:")
            if 'summary' in result:
                print(json.dumps(result['summary'], indent=2))
                
            if 'current_action' in result:
                print("\nCurrent Situation:")
                print(json.dumps(result['current_action'], indent=2))
                
            if 'key_plays' in result:
                print("\nKey Plays:")
                print(json.dumps(result['key_plays'][:2], indent=2))
                
            if 'standouts' in result:
                print("\nStandout Performances:")
                print(json.dumps(result['standouts'], indent=2))
                
            if 'special_alert' in result:
                print("\nSpecial Game Situations:")
                print(json.dumps(result['special_alert'], indent=2))
                
            if 'result' in result:
                print("\nGame Result:")
                print(json.dumps(result['result'], indent=2))

        # 4. Test Story Generation
        print("\n4. Testing Story Generation...")
        story_request = {
            "game_id": str(game_id),
            "preferences": {
                "style": "dramatic",
                "focus": ["key_plays", "standout_performances"],
                "length": "medium"
            }
        }
        
        result = await make_request(
            session,
            "POST",
            f"{base_url}/generate-story",
            json=story_request
        )
        
        if result and "error" not in result:
            print("\nGenerated Story:")
            if isinstance(result, str):
                story_text = result
                print(result)
            else:
                print(json.dumps(result, indent=2))
                story_text = result

        # 5. Test Audio Generation
        print("\n5. Testing Audio Generation...")
        if not story_text:
            print("No story text available for audio generation")
            return

        # Remove markdown formatting if present
        story_text = story_text.replace('**Dramatic Narrative:**\n\n', '')
        story_text = story_text.strip()
            
        print(f"Processing story text ({len(story_text)} characters)...")
                
        # Prepare audio request with proper parameters
        audio_request = {
            "text": story_text,
            "voice": "en-US-Studio-O",
            "language_code": "en-US",
            "speaking_rate": 1.0,
            "pitch": 0.0
        }
                
        # Make the request with proper headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
                
        try:
            # Use make_request with expect_binary=True for audio content
            audio_content = await make_request(
                session,
                "POST",
                f"{base_url}/api/audio/generate-audio",
                json=audio_request,
                headers=headers,
                expect_binary=True
            )
                    
            if isinstance(audio_content, dict) and "error" in audio_content:
                error_text = audio_content.get("error")
                if isinstance(error_text, dict):
                    error_detail = error_text.get("detail", str(error_text))
                else:
                    error_detail = str(error_text)
                print(f"Audio generation failed: {error_detail}")
            elif isinstance(audio_content, bytes):
                print(f"\nAudio generation successful!")
                print(f"Received {len(audio_content)} bytes of audio data")
                
                # Save and play the audio
                if len(audio_content) > 0:
                    play_audio(audio_content)
                else:
                    print("Warning: Received empty audio content")
            else:
                print(f"Unexpected response format from audio generation: {type(audio_content)}")
        except Exception as e:
            print(f"Error during audio generation: {str(e)}")

        # 6. Test Team Roster
        print("\n6. Testing Team Roster API...")
        result = await make_request(
            session,
            "GET",
            f"{base_url}/teams/119/roster",  # LA Dodgers
            params={"season": 2024}
        )
        
        if result and "error" not in result:
            print(f"\nRoster size: {len(result)}")
            if result:
                print("Sample player:")
                print(json.dumps(result[0], indent=2))

        # 7. Test Player Stats
        print("\n7. Testing Player Stats API...")
        result = await make_request(
            session,
            "GET",
            f"{base_url}/players/660271/stats",  # Shohei Ohtani
            params={"season": 2024}
        )
        
        if result and "error" not in result:
            print("\nPlayer Stats:")
            print(json.dumps(result, indent=2))

        # 8. Test User Preferences
        print("\n8. Testing User Preferences API...")
        test_preferences = {
            "favorite_team": "Los Angeles Dodgers",
            "favorite_players": ["Shohei Ohtani", "Mookie Betts"],
            "preferred_style": "dramatic"
        }
        
        result = await make_request(
            session,
            "POST",
            f"{base_url}/users/test_user/preferences",
            json=test_preferences
        )
        
        if "error" not in result:
            print("User preferences saved successfully")
            
            # Get preferences back
            result = await make_request(
                session,
                "GET",
                f"{base_url}/users/test_user/preferences"
            )
            
            if result and "error" not in result:
                print("\nRetrieved Preferences:")
                print(json.dumps(result, indent=2))

        # 9. Test User History
        print("\n9. Testing User History API...")
        result = await make_request(
            session,
            "GET",
            f"{base_url}/users/test_user/history"
        )
        
        if result and "error" not in result:
            print("\nUser Story History:")
            print(json.dumps(result, indent=2))

        # 10. Test Available Styles
        print("\n10. Testing Available Styles API...")
        result = await make_request(
            session,
            "GET",
            f"{base_url}/styles"
        )
        
        if result and "error" not in result:
            print("\nAvailable Storytelling Styles:")
            print(json.dumps(result, indent=2))

def main():
    """Run the API tests."""
    try:
        asyncio.run(test_api())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTests failed: {str(e)}")
        sys.exit(1)
if __name__ == "__main__":
    main() 