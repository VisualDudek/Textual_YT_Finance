from datetime import datetime
import re
import yaml
import logging

from urllib.parse import parse_qs, urlparse
from config import config
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich.prompt import Prompt
from rich.console import Console
from models import YTChannel, VideoYT

logging.basicConfig(level=logging.INFO)

def load_youtube_config(file_path: str) -> dict:
    """Load YouTube configuration from a YAML file."""
    with open(file_path, "r") as file:
        yt_config = yaml.safe_load(file)
    return yt_config


def save_youtube_config(file_path: str, data: dict):
    """Save YouTube configuration to a YAML file."""
    with open(file_path, "w") as file:
        yaml.dump(data, file, sort_keys=False)

def get_video_duration(video: VideoYT) -> str:
    """Call YouTube API to get the duration of a video."""
    youtube = build(
        config.youtube_api_service_name, 
        config.youtube_api_version, 
        developerKey=config.youtube_api_key,
        )

    try:
        request = youtube.videos().list(
            part="contentDetails",
            id=video.video_id
        )
        response = request.execute()
        duration = response["items"][0]["contentDetails"]["duration"]
        return duration
    except HttpError as e:
        logging.error(f"An error occurred while fetching video duration: {e}")
        return "N/A"


def get_video_id_from_url(url: str) -> str | None:
    """
    Extracts the YouTube video ID from various URL formats.
    Handles:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    """
    if not url:
        return None

    # Parse the URL
    parsed_url = urlparse(url)
    
    # Check for standard youtube.com/watch URLs
    if parsed_url.hostname in ('www.youtube.com', 'm.youtube.com', 'music.youtube.com') and parsed_url.path == '/watch':
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]
    
    # Check for youtu.be short URLs
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]  # Remove the leading '/'
        
    # Check for youtube.com/embed URLs
    if parsed_url.hostname in ('www.youtube.com', 'm.youtube.com') and parsed_url.path.startswith('/embed/'):
        return parsed_url.path.split('/embed/')[1].split('?')[0] # Get part after /embed/ and before any query params

    # Regex for more robust matching if the above simple parsing fails for some edge cases
    # This regex tries to find common patterns for video IDs.
    regex_patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    ]
    for pattern in regex_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    print(f"Could not extract video ID from URL: {url}")
    return None


def get_channel_id_from_video_url(video_url: str) -> tuple[str, str] | None:
    """
    Fetches the YouTube Channel ID for a given video URL.
    """

    video_id = get_video_id_from_url(video_url)
    if not video_id:
        return None

    try:
        # Build the YouTube API service object
        youtube = build(
            config.youtube_api_service_name, 
            config.youtube_api_version, 
            developerKey=config.youtube_api_key,
            )

        # Call the videos.list method to retrieve video info
        request = youtube.videos().list(
            part="snippet,contentDetails",  # 'snippet' contains channelId, title, description, etc.
            id=video_id      # ID of the video to retrieve
        )
        response = request.execute()

        if response.get("items"):
            # Extract the channel ID from the first item in the response
            channel_id = response["items"][0]["snippet"]["channelId"]
            channel_title = response["items"][0]["snippet"]["channelTitle"]
            video_title = response["items"][0]["snippet"]["title"]
            
            print(f"\n--- Video Details ---")
            print(f"Video Title: {video_title}")
            print(f"Channel Title: {channel_title}")
            print(f"Channel ID: {channel_id}")
            return (channel_id, channel_title)
        else:
            print(f"No video found with ID: {video_id}. The video might be private, deleted, or the ID is incorrect.")
            return None

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content.decode()}")
        if e.resp.status == 403:
            print("This might be due to an incorrect API key, exceeded quota, or the API not being enabled.")
        elif e.resp.status == 404:
             print(f"Video with ID '{video_id}' not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def add_channel_to_config(channel_id: str, channel_title: str, config_file: str):
    """
    Adds a new channel ID and title to the YouTube configuration file.
    """
    yt_config = load_youtube_config(config_file)

    # Build list of existing channels list to check for duplicates
    existing_channels = {item.get('channel_id') for item  in yt_config.get('channels', {})}

    # Check if the channel already exists
    if channel_id in existing_channels:
        print(f"Channel ID {channel_id} [{channel_title}] already exists in the configuration.")
        return
    
    # Fetch uploads_id for the new channel
    youtube = build(
        config.youtube_api_service_name, 
        config.youtube_api_version, 
        developerKey=config.youtube_api_key
    )

    channel_request = youtube.channels().list(
        id=channel_id,  # Tutaj jest możliwość podania kilku ID kanału
        part='snippet,contentDetails',
    )
    channel_response = channel_request.execute()

    uploads_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    channel_title = channel_response['items'][0]['snippet']['title']

    # Add the new channel to the existing configuration
    new_channel = {
        'channel_id': channel_id,
        'channel_title': channel_title,
        'uploads_id': uploads_id
    }
    
    # Append to existing channels list
    yt_config['channels'].append(new_channel)

    # Save the updated config back to the YAML file (preserves all existing data)
    save_youtube_config(config.yt_config_file, yt_config)

    # Add the new channel
    print(f"Added new channel: [{channel_title}] with ID: {channel_id}")


def get_last_videos(channel: YTChannel, max_results: int=3) -> list[VideoYT]:

    videos: list[VideoYT] = []

    # Build the YouTube API service object
    youtube = build(
        config.youtube_api_service_name, 
        config.youtube_api_version, 
        developerKey=config.youtube_api_key
        )

    playlist_request = youtube.playlistItems().list(
        playlistId=channel.uploads_id,
        part='snippet',
        maxResults=max_results,  # Limit the number of results
    )
    playlist_response = playlist_request.execute()
    items = playlist_response['items']

    for item in items:
        video_id = item['snippet']['resourceId']['videoId']
        video_title = item['snippet']['title']
        published_at_str = item['snippet']['publishedAt']
        channel_id = item['snippet']['channelId']
        channel_title = item['snippet']['channelTitle']

        # Construct URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        published_at_dt = None
        try:
            # YouTube API returns ISO 8601 format (e.g., "2023-10-26T14:30:00Z")
            # .replace('Z', '+00:00') is robust for Python versions < 3.11 with fromisoformat
            if published_at_str.endswith('Z'):
                published_at_dt = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            else:
                published_at_dt = datetime.fromisoformat(published_at_str)
        except ValueError:
            print(f"Warning: Could not parse date '{published_at_str}' for video ID '{video_id}'. Storing as string.")
            published_at_dt = published_at_str # Fallback

        # Append video details to the list
        # Using VideoYT model for structured data
        video_yt = VideoYT(
            title=video_title,
            video_id=video_id,
            published_at=published_at_dt,
            channel_id=channel_id,
            channel_title=channel_title,
            url=video_url,
            # Duration can be fetched separately if needed
        )
        # Append to the list of videos
        videos.append(video_yt)

        # Print video details
        print(f"Video ID: {video_id}, Title: {video_title}, Published At: {published_at_str}, Channel ID: {channel_id}, Channel Title: {channel_title}")

    return videos


# --- Main Execution ---
if __name__ == '__main__':

    console = Console()

    # --- Main Logic ---
    sample_video_url = Prompt.ask("Enter a YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID): ", default="https://youtu.be/Coot4TFTkN4?si=MTxHahttsNC07ymW")
    if not sample_video_url:
        print("No URL provided. Exiting.")
        exit(1)

    print(f"Attempting to fetch Channel ID for video URL: {sample_video_url}")

    channel_id, channel_title = get_channel_id_from_video_url(sample_video_url)

    if channel_id:
        print(f"\nSuccessfully retrieved Channel ID: {channel_id}")
    else:
        print("\nFailed to retrieve Channel ID.")

    add_channel_to_config(channel_id, channel_title, config.yt_config_file)