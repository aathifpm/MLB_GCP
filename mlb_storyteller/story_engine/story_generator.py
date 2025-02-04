import google.generativeai as genai
from typing import Dict
import os
from dotenv import load_dotenv
import json

load_dotenv()

class StoryGenerator:
    """Generate baseball stories using Gemini AI."""
    
    def __init__(self):
        """Initialize the story generator with Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        

    async def generate_quiz(self, game_data: Dict, user_preferences: Dict) -> Dict:
        """Generate interactive quiz based on game data"""
        quiz_prompt = await self._construct_quiz_prompt(game_data, user_preferences)
        response = self.model.generate_content(quiz_prompt)
        return self._parse_quiz_response(response.text)

    async def _construct_quiz_prompt(self, game_data: Dict, user_preferences: Dict) -> str:
        """Construct quiz generation prompt"""
        base_prompt = await self._construct_prompt(game_data, user_preferences, "analytical")
        
        # Create a simplified game data structure
        simplified_game = {
            'summary': game_data.get('summary', {}),
            'teams': {
                'home': game_data.get('summary', {}).get('home_team'),
                'away': game_data.get('summary', {}).get('away_team'),
                'score': {
                    'home': game_data.get('summary', {}).get('home_score'),
                    'away': game_data.get('summary', {}).get('away_score')
                }
            }
        }

        return f"""
        Based on this baseball game data, generate a quiz with 5 multiple-choice questions.
        
        Game Data:
        {json.dumps(simplified_game, indent=2)}

        Create 5 engaging quiz questions:
        - 2 questions about key moments or plays from this game
        - 1 question about player statistics 
        - 1 baseball history/trivia question
        - 1 prediction/analysis question about future implications

        Format your response EXACTLY as a JSON object with this structure:
        {{
            "questions": [
                {{
                    "question": "What was the final score of the game?",
                    "options": ["4-2", "3-1", "5-3", "2-1"],
                    "correct_answer": "4-2",
                    "explanation": "The game ended with a score of 4-2 in favor of the home team."
                }},
                // ... more questions ...
            ]
        }}

        Requirements:
        1. Each question must have exactly 4 options
        2. The correct_answer must match one of the options exactly
        3. Include a brief explanation for each answer
        4. Make questions engaging and specific to this game
        5. Ensure all JSON formatting is correct
        """

    def _parse_quiz_response(self, response_text: str) -> Dict:
        """Parse the quiz response from Gemini."""
        try:
            # Clean up the response text to ensure valid JSON
            # Remove any text before the first {
            start_idx = response_text.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            
            # Remove any text after the last }
            end_idx = response_text.rfind('}')
            if end_idx == -1:
                raise ValueError("No JSON object found in response")
            
            json_str = response_text[start_idx:end_idx + 1]
            
            # Remove any comments
            json_str = '\n'.join(line for line in json_str.split('\n') 
                               if not line.strip().startswith('//'))
            
            # Parse the JSON
            quiz_data = json.loads(json_str)
            
            # Validate the structure
            if not isinstance(quiz_data, dict):
                raise ValueError("Response is not a JSON object")
            
            if 'questions' not in quiz_data:
                raise ValueError("Missing 'questions' array in response")
            
            if not isinstance(quiz_data['questions'], list):
                raise ValueError("'questions' is not an array")
            
            # Process each question
            for i, question in enumerate(quiz_data['questions']):
                # Validate required fields
                required_fields = ['question', 'options', 'correct_answer', 'explanation']
                for field in required_fields:
                    if field not in question:
                        raise ValueError(f"Question {i+1} is missing required field: {field}")
                
                # Validate options
                if not isinstance(question['options'], list):
                    raise ValueError(f"Question {i+1}: options must be an array")
                
                if len(question['options']) != 4:
                    raise ValueError(f"Question {i+1}: must have exactly 4 options")
                
                # Convert all values to strings
                question['options'] = [str(opt).strip() for opt in question['options']]
                question['correct_answer'] = str(question['correct_answer']).strip()
                
                # Validate correct answer is in options
                if question['correct_answer'] not in question['options']:
                    raise ValueError(f"Question {i+1}: correct_answer must match one of the options exactly")
                
                # Add index for client-side handling
                question['index'] = i
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            print(f"Response text: {response_text}")
            raise ValueError(f"Failed to parse quiz response as JSON: {str(e)}")
        except Exception as e:
            print(f"Error processing quiz response: {str(e)}")
            print(f"Response text: {response_text}")
            raise ValueError(f"Error processing quiz response: {str(e)}")

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
        Strictly avoid mentioning the style in the story.
        
        Make the story personal and engaging, highlighting moments that would interest this specific fan.
        """
        
        return prompt 