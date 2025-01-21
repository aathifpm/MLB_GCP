from functools import lru_cache
from ..services.text_to_speech_service import TextToSpeechService
from ..data.mlb_data_fetcher import MLBDataFetcher
from ..story_engine.story_generator import StoryGenerator
from ..cache.redis_service import RedisService
import os

def get_text_to_speech_service() -> TextToSpeechService:
    """Get a new instance of TextToSpeechService with proper error handling."""
    try:
        # Get credentials path from environment
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        # Convert to absolute path if relative
        if not os.path.isabs(credentials_path):
            # Get the project root directory (where .env is located)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            abs_path = os.path.join(project_root, credentials_path)
            
            if not os.path.exists(abs_path):
                raise Exception(f"Google Cloud credentials file not found at: {abs_path}")
                
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = abs_path
            print(f"Updated credentials path to absolute: {abs_path}")
        
        return TextToSpeechService()
    except Exception as e:
        print(f"Failed to initialize TextToSpeechService: {str(e)}")
        raise

@lru_cache()
def get_mlb_data_fetcher() -> MLBDataFetcher:
    return MLBDataFetcher()

@lru_cache()
def get_story_generator() -> StoryGenerator:
    return StoryGenerator()

@lru_cache()
def get_redis_service() -> RedisService:
    return RedisService() 