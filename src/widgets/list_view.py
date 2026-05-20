from textual.widgets import ListView, ListItem, Label
from textual.binding import Binding
from models.models import Video
from utils import count_new_videos
from textual.message import Message

class MyListItem(ListItem):
    def __init__(self, channel_name, videos):
        self.data = channel_name
        label = channel_name
        number = count_new_videos(videos)
        if number > 0:
            label = f"{channel_name} ({number})"
        super().__init__(Label(label))

class CustomListView(ListView):
    BINDINGS = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("k", "cursor_up", "Cursor up", show=False),
        Binding("j", "cursor_down", "Cursor down", show=False),
        Binding("r", "load_data_from_db", "Load data from DB", show=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data: dict[str, list[Video]] = {}

    def set_data(self, data: dict[str, list[Video]]):
        """
        Set the data for the list view.
        
        Args:
            data (dict): A dictionary mapping channel names (str) to lists of videos.
        
        Side Effects:
            - Updates the internal `data` attribute with the provided dictionary.
            - Calls `update_data` to refresh the list view with the new data.
        """
        self.data: dict[str, list[Video]] = data
        self.update_data()
        
    def update_data(self):
        self.clear()
        for channel_name, videos in self.data.items():
            self.append(MyListItem(channel_name, videos))
            
    def action_load_data_from_db(self):
        from database import DatabaseService
        db_service = DatabaseService()
        new_data = db_service.load_videos()
        self.set_data(new_data)
        # Emit event to update main app data
        self.post_message(self.DataUpdated(new_data))

    class DataUpdated(Message):
        def __init__(self, data) -> None:
            self.data = data
            super().__init__()