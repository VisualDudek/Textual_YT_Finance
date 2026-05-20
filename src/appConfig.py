import os
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    # MongoDB settings
    mongo_uri: str = os.getenv("MONGO_URI")
    mongo_database_name: str = "youtube_data"
    mongo_collection_name: str = "videos"
    
    # UI settings
    column_headers: tuple = ("Time", "Title", "Duration")
    
    # Data settings
    default_pickle_file: str = "data.pkl"
    connection_timeout_ms: int = 5000

    # YT API settings
    youtube_api_key: str = os.getenv("YT_API_KEY")
    youtube_api_service_name: str = "youtube"
    youtube_api_version: str = "v3"

    # GOOGLE AI API KEY
    google_ai_api_key: str = os.getenv("GOOGLE_AI_API_KEY")

    # YT channel config
    yt_config_file: str = "./src/yt_config.yaml"

    def __post_init__(self):
        if not self.mongo_uri:
            raise ValueError("MONGO_URI environment variable is not set.")
        if not self.youtube_api_key:
            raise ValueError("YT_API_KEY environment variable is not set.")
        if not self.google_ai_api_key:
            raise ValueError("GOOGLE_AI_API_KEY environment variable is not set.")


# Create a global config instance
config = Config()