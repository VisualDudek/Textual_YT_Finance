import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
load_dotenv()

@dataclass
class AppConfig:
    # MongoDB settings
    mongo_uri: Optional[str] = os.getenv("MONGO_URI")
    mongo_database_name: str = "youtube_data"
    mongo_collection_name: str = "videos_finance"
    
    # UI settings
    column_headers: tuple = ("Time", "Title", "Duration")
    
    # Data settings
    default_pickle_file: str = "data.pkl"
    connection_timeout_ms: int = 5000

    # YT API settings
    youtube_api_key: Optional[str] = os.getenv("YT_API_KEY")
    youtube_api_service_name: str = "youtube"
    youtube_api_version: str = "v3"

    # GOOGLE AI API KEY
    google_ai_api_key: Optional[str] = os.getenv("GOOGLE_AI_API_KEY")

    # YT channel config
    yt_config_file: str = "./src/yt_config.yaml"

    def __post_init__(self):
        if self.mongo_uri is None:
            raise ValueError("MONGO_URI environment variable is not set.")
        if self.youtube_api_key is None:
            raise ValueError("YT_API_KEY environment variable is not set.")
        if self.google_ai_api_key is None:
            raise ValueError("GOOGLE_AI_API_KEY environment variable is not set.")


# Create a global config instance
app_config = AppConfig()