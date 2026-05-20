import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from appConfig import app_config
from models.models import VideoYT

def is_within_last_two_days(dt: datetime) -> bool:
    """Check if datetime is within the last two days"""
    now = datetime.now()
    # WARNING: days do not reflect fn. name
    two_days_ago = now - timedelta(days=7)
    return two_days_ago.date() <= dt.date()

def is_today(dt: datetime) -> bool:
    """Check if datetime is today"""
    return dt.date() == datetime.now().date()

def count_new_videos(videos: List[Any]) -> int:
    """Count videos published within the last two days"""
    return sum(1 for video in videos if is_within_last_two_days(video.published_at))

def pickle_data(data: Dict[str, List[Any]]):
    """Save data to pickle file"""
    with open(app_config.default_pickle_file, "wb") as f:
        pickle.dump(data, f)

def load_pickle_data() -> Dict[str, List[Any]]:
    """Load data from pickle file"""
    with open(app_config.default_pickle_file, "rb") as f:
        return pickle.load(f)

def get_initial_data() -> Dict[str, List[VideoYT]]:
    """Get initial data from pickle file or database"""
    from database import DatabaseService

    # Load data from pickle file is disabled
    # as it is not used in the current implementation.
    db_service = DatabaseService()
    return db_service.load_videos()

    # file_path = Path(app_config.default_pickle_file)
    # if file_path.exists():
    #     return load_pickle_data()
    # else:
    #     db_service = DatabaseService()
    #     return db_service.load_videos()