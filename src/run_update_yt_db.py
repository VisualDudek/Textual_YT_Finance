from youtube import get_last_videos
from database import DatabaseService
from appConfig import app_config as config
from models.models import YTConfig, YTChannel


def main():
    ytconfig = YTConfig.from_yaml(config.yt_config_file)
    dbservice = DatabaseService()

    for channel_data in ytconfig.channels:

        channel = YTChannel.from_dict(channel_data)
        videos = get_last_videos(channel, max_results=ytconfig.results)
        # dbservice.save_videos(videos)
        dbservice.save_videos_bulk(videos)


if __name__ == "__main__":
    main()