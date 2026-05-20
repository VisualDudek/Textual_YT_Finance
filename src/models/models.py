from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from typing import Dict
import yaml

@dataclass
class Video:
    _id: ObjectId
    title: str
    video_id: str
    published_at: datetime
    url: str = field(default="N/A")
    duration: str = field(default="N/A")
    seen: bool = field(default=False)
    has_summary: bool = field(default=False)
    summary: str = field(default="")

@dataclass
class VideoYT:
    title: str
    video_id: str
    published_at: datetime
    channel_id: str
    channel_title: str
    url: str = field(default="N/A")
    duration: str = field(default="N/A")
    seen: bool = field(default=False)
    has_summary: bool = field(default=False)
    summary: str = field(default="")

    def to_dict(self) -> Dict[str, str]:
        """Convert VideoYT instance to dictionary using field names"""
        return {field: getattr(self, field) for field in self.__dataclass_fields__}

@dataclass
class YTConfig:
    channels: Dict[str, str]
    results: int
    
    @classmethod
    def from_yaml(cls, file_path: str) -> 'YTConfig':
        """Load configuration from YAML file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return cls(**data)
    
@dataclass
class YTChannel:
    channel_id: str
    channel_title: str
    uploads_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'YTChannel':
        """Create a YTChannel instance from a dictionary"""
        return cls(
            channel_id=data.get('channel_id', ''),
            channel_title=data.get('channel_title', ''),
            uploads_id=data.get('uploads_id', '')
        )