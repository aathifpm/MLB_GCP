import os
from dotenv import load_dotenv

load_dotenv()

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# MLB API Configuration
MLB_STATS_API_BASE_URL = "https://statsapi.mlb.com/api"
MLB_STATS_API_VERSION = "v1"

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'mlb_storyteller')

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # Default 1 hour

# Application Settings
NARRATIVE_STYLES = {
    'dramatic': {
        'description': 'Emotional and engaging storytelling style',
        'prompt_guide': 'Create a dramatic and emotional narrative'
    },
    'analytical': {
        'description': 'Statistical and tactical analysis',
        'prompt_guide': 'Provide a detailed statistical analysis'
    },
    'humorous': {
        'description': 'Light-hearted and entertaining',
        'prompt_guide': 'Tell the story with humor and wit'
    }
}

# Google Cloud Service Configuration
GCP_REGION = os.getenv('GCP_REGION', 'us-central1')
GCP_SERVICES = {
    'cloud_run': True,  # For deploying the API
    'cloud_storage': True,  # For storing cached game data
    'cloud_logging': True,  # For application logging
} 