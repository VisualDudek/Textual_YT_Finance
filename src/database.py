from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import DuplicateKeyError
from dataclasses import fields
from typing import Dict, List
from models.models import Video, VideoYT
from appConfig import app_config as config
import logging
from textual.logging import TextualHandler

from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError, BulkWriteError

logging.basicConfig(
    level=logging.INFO,
    handlers=[TextualHandler()],
    )

class MongoDBAsyncClient:
    def __init__(self):
        self.client = None

    async def connect(self) -> AsyncMongoClient:
        """Establish asynchronous MongoDB connection"""
        logging.info(f"Connecting to MongoDB at {config.mongo_uri}...")
        self.client = AsyncMongoClient(
            config.mongo_uri, 
            serverSelectionTimeoutMS=config.connection_timeout_ms, 
            server_api=ServerApi('1')
        )
        await self.client.admin.command('ping')
        logging.info("Successfully connected to MongoDB.")
        return self.client

    async def disconnect(self):
        """Close asynchronous MongoDB connection"""
        if self.client:
            await self.client.close()
            logging.info("MongoDB connection closed.")

    async def update_video_duration(self, video_id: str, duration: str):
        """Update the duration of a video asynchronously"""
        await self.connect()
        
        db = self.client[config.mongo_database_name]
        video_collection = db[config.mongo_collection_name]

        await video_collection.update_one(
            {"video_id": video_id},
            {"$set": {"duration": duration}},
        )

        await self.disconnect()

class DatabaseService:
    def __init__(self):
        self.client = None
        
    def connect(self) -> MongoClient:
        """Establish MongoDB connection"""
        logging.info(f"Connecting to MongoDB at {config.mongo_uri}...")
        self.client = MongoClient(
            config.mongo_uri, 
            serverSelectionTimeoutMS=config.connection_timeout_ms, 
            server_api=ServerApi('1')
        )
        self.client.admin.command('ping')
        logging.info("Successfully connected to MongoDB.")
        return self.client
        
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")
            
    def load_videos(self) -> Dict[str, List[VideoYT]]:
        """Load video data from MongoDB"""
        self.connect()
        
        db = self.client[config.mongo_database_name]
        # TODO: Make view name configurable in appConfig
        loaded_data = list(db.latest_20.find())

        data: dict[str, List[VideoYT]] = {}
        field_names = {f.name for f in fields(VideoYT)}

        for item in loaded_data:
            channel_name: str = item["_id"]
            videos: List[VideoYT] = []

            for video in item["latest_videos"]:
                filtered_data = {k: v for k, v in video.items() if k in field_names}
                videos.append(VideoYT(**filtered_data))

            data[channel_name] = videos
            
        self.disconnect()
        return data
        
    def update_video_seen_status(self, video_id, seen_status: bool):
        """Update the seen status of a video"""
        self.connect()
        
        db = self.client[config.mongo_database_name]
        video_collection = db[config.mongo_collection_name]
        
        video_collection.update_one(
            {"video_id": video_id},
            {"$set": {"seen": seen_status}},
        )
        self.disconnect()

    async def update_video_duration(self, video_id, duration: str):
        """Update the duration of a video"""
        self.connect()
        
        db = self.client[config.mongo_database_name]
        video_collection = db[config.mongo_collection_name]

        video_collection.update_one(
            {"video_id": video_id},
            {"$set": {"duration": duration}},
        )
        self.disconnect()

    def update_video_summary(self, video_id, summary: str):
        """Update the summary of a video"""
        self.connect()
        
        db = self.client[config.mongo_database_name]
        video_collection = db[config.mongo_collection_name]
        
        update_result = video_collection.update_one(
            {"video_id": video_id},
            {"$set": {
                "summary": summary,
                "has_summary": True
                }},
        )
        self.disconnect()

    def save_videos(self, videos: list[VideoYT]):
        """Save video data to MongoDB"""
        self.connect()

        db = self.client[config.mongo_database_name]
        video_collection = db[config.mongo_collection_name]

        for video in videos:
            try:
                video_collection.insert_one(video.to_dict())
                print(f"Successfully saved video to MongoDB: {video.title} (ID: {video.video_id})")
            except DuplicateKeyError:
                print(f"Video already exists in MongoDB (ID: {video.video_id}). Skipping.")
            except Exception as e:
                print(f"An error occurred while saving video {video.title} to MongoDB: {e}")

        self.disconnect()


    def save_videos_bulk(self, videos: list[VideoYT]):
        """Save video data to MongoDB using bulk insert"""
        self.connect()
    
        db = self.client[config.mongo_database_name]
        video_collection = db[config.mongo_collection_name]
    
        if not videos:
            logging.info("No videos to save.")
            self.disconnect()
            return
    
        # Convert videos to dictionaries
        video_docs = [video.to_dict() for video in videos]
        
        try:
            # Use insert_many with ordered=False to continue on duplicates
            result = video_collection.insert_many(video_docs, ordered=False)
            logging.info(f"Successfully saved {len(result.inserted_ids)} videos to MongoDB")
            
        except BulkWriteError as e:
            # Handle bulk write errors (including duplicates)
            successful_inserts = e.details.get('nInserted', 0)
            write_errors = e.details.get('writeErrors', [])
            duplicate_errors = len([err for err in write_errors if err.get('code') == 11000])
            
            logging.info(f"Bulk insert completed: {successful_inserts} new videos saved, "
                        f"{duplicate_errors} duplicates skipped")
            
            # Log other errors if any
            other_errors = len(write_errors) - duplicate_errors
            if other_errors > 0:
                logging.warning(f"{other_errors} other write errors occurred")
                
        except Exception as e:
            logging.error(f"An error occurred during bulk insert: {e}")
            
        self.disconnect()