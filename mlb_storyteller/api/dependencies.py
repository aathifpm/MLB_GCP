from functools import lru_cache
from ..services.text_to_speech_service import TextToSpeechService
from ..data.mlb_data_fetcher import MLBDataFetcher
from ..story_engine.story_generator import StoryGenerator
from ..cache.redis_service import RedisService

@lru_cache()
def get_text_to_speech_service() -> TextToSpeechService:
    return TextToSpeechService()

@lru_cache()
def get_mlb_data_fetcher() -> MLBDataFetcher:
    return MLBDataFetcher()

@lru_cache()
def get_story_generator() -> StoryGenerator:
    return StoryGenerator()

@lru_cache()
def get_redis_service() -> RedisService:
    return RedisService() 