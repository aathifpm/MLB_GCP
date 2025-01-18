import google.generativeai as genai
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class StoryGenerator:
    """Generate baseball stories using Gemini AI."""
    
    def __init__(self):
        """Initialize the story generator with Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    async def generate_story(
        self,
        game_data: Dict,
        user_preferences: Dict,
        style: str = "dramatic"
    ) -> str:
        """
        Generate a baseball story based on game data and user preferences.
        
        Args:
            game_data: Dictionary containing game statistics and events
            user_preferences: User's preferences (favorite team, players, etc.)
            style: Narrative style (dramatic, analytical, humorous)
            
        Returns:
            str: Generated story narrative
        """
        # Construct the prompt based on style and preferences
        prompt = await self._construct_prompt(game_data, user_preferences, style)
        
        try:
            # Generate the story using Gemini (synchronous call)
            response = self.model.generate_content(prompt)
            if not response or not response.text:
                raise Exception("No response generated")
            return response.text
        except Exception as e:
            raise Exception(f"Failed to generate story: {str(e)}")
    
    async def _construct_prompt(
        self,
        game_data: Dict,
        user_preferences: Dict,
        style: str
    ) -> str:
        """Construct a prompt for Gemini based on the game data and preferences."""
        # Extract game summary
        summary = game_data.get('summary', {})
        home_team = summary.get('home_team', 'Unknown Team')
        away_team = summary.get('away_team', 'Unknown Team')
        home_score = summary.get('home_score', 0)
        away_score = summary.get('away_score', 0)
        status = summary.get('status', 'Unknown')
        
        # Get user's favorite team and players
        favorite_team = user_preferences.get('favorite_team')
        favorite_players = user_preferences.get('favorite_players', [])
        
        # Get key plays
        key_plays = game_data.get('key_plays', [])
        play_descriptions = [
            f"- {play['description']}" 
            for play in key_plays
            if 'description' in play
        ]
        
        # Get player stats
        player_stats = game_data.get('player_stats', {})
        
        # Construct the prompt
        prompt = f"""
        As a baseball storyteller, create a {style} narrative about this game:
        
        Game Summary:
        {home_team} vs {away_team}
        Score: {home_team} {home_score}, {away_team} {away_score}
        Status: {status}
        
        Key Plays:
        {chr(10).join(play_descriptions) if play_descriptions else "No key plays available yet"}
        
        Player Statistics:
        """
        
        # Add batting stats if available
        batting_stats = player_stats.get('batting', [])
        if batting_stats:
            prompt += "\nBatting Highlights:\n"
            for stat in batting_stats:
                if stat.get('name') in favorite_players:
                    prompt += (
                        f"- {stat['name']}: {stat.get('hits', 0)} hits, "
                        f"{stat.get('runs', 0)} runs, {stat.get('rbi', 0)} RBIs\n"
                    )
        
        # Add pitching stats if available
        pitching_stats = player_stats.get('pitching', [])
        if pitching_stats:
            prompt += "\nPitching Highlights:\n"
            for stat in pitching_stats:
                if stat.get('name') in favorite_players:
                    prompt += (
                        f"- {stat['name']}: {stat.get('innings_pitched', 0)} IP, "
                        f"{stat.get('earned_runs', 0)} ER, {stat.get('strikeouts', 0)} K\n"
                    )
        
        # Add focus points
        prompt += f"""
        Focus on:
        - {'Your favorite team: ' + favorite_team if favorite_team else 'Both teams equally'}
        - Key players: {', '.join(favorite_players) if favorite_players else 'All notable performances'}
        
        Style Guide:
        - If "dramatic": Create an emotional and engaging narrative that captures the excitement
        - If "analytical": Focus on statistics, strategy, and technical aspects
        - If "humorous": Add wit and light-hearted observations
        
        Make the story personal and engaging, highlighting moments that would interest this specific fan.
        """
        
        return prompt 