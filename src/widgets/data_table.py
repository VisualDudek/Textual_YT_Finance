from textual.widgets import DataTable
from textual.binding import Binding
from textual import on
from rich.text import Text
from datetime import date, timedelta
from typing import List
from models.models import Video
from database import DatabaseService
from appConfig import app_config
from utils import is_today, is_within_last_two_days
from youtube import get_video_duration
from widgets.summary_modalscreen import SummaryScreen
from google_ai import get_summary_url
from textual.worker import Worker, WorkerState
from database import DatabaseService, MongoDBAsyncClient


class CustomDataTable(DataTable):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor up", show=True),
        Binding("j", "cursor_down", "Cursor down", show=True),
        Binding("t", "style_row", "Toggle row", show=True),
        Binding("i", "get_video_info", "Get video info", show=True),
        Binding("s", "display_summary", "Display summary", show=True),
        Binding("a", "get_ai_summary", "Get AI summary", show=True),
        Binding("w", "show_worker_status", "Worker status", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.videos: List[Video] = []
        self.key = ""


    async def action_get_ai_summary(self):
        """Get detailed information about the current row's video"""
        if not self.videos:
            return
            
        row = self.cursor_row
        if row >= len(self.videos):
            return
            
        video = self.videos[row]
        # summary = await get_summary_url(video.url)
        self.app.notify(f"Generating AI summary...\n{video.title}", title="Processing")
        self.worker = self.run_worker(
            get_summary_url(video.url, video),
            group="ai_summary",
            exclusive=False,
            )

        # ----
        # video.summary = summary
        # video.has_summary = True

        # # Refresh the table with updated duration
        # self.update_cell(
        #     row_key=video.video_id,
        #     column_key="has_summary",
        #     value=video.has_summary)

    @on(Worker.StateChanged)
    def worker_state_changed(self, event: Worker.StateChanged):
        if event.worker.group != "ai_summary":
            return
        """Handle state changes of the AI summary worker"""
        if event.state == WorkerState.SUCCESS:
            summary, video = event.worker.result
            self.app.notify(f"AI summary fetched successfully!\n{video.title}\nGroup: {event.worker.group}", title="Success")
            
            db_service = DatabaseService()
            db_service.update_video_summary(video.video_id, summary)

        elif event.state == WorkerState.ERROR:
            self.app.notify("Failed to fetch AI summary.", title="Error")


    def action_display_summary(self):
        """Display a summary of the current video"""
        if not self.videos:
            return
            
        row = self.cursor_row
        if row >= len(self.videos):
            return
            
        video = self.videos[row]

        self.app.push_screen(
            SummaryScreen(
                text=video.summary if video.has_summary else "No summary available.",
            )
        )

    def on_mount(self) -> None:
        self.cursor_type = "row"
        # self.add_columns(*config.column_headers)
        self.add_column("Published At", key="published_at")
        self.add_column("Title", key="title")
        self.add_column("Duration", key="duration")
        self.add_column("Has summary", key="has_summary")
        self.cursor_foreground_priority = 'renderable'

    def update_table(self, key: str, videos: List[Video]):
        """Update the table with videos for a specific channel"""
        self.clear()
        self.videos = videos
        self.key = key

        for video in videos:
            # Color coding based on publish date
            if is_today(video.published_at):
                title = Text(video.title, style="bold red")
            elif is_within_last_two_days(video.published_at):
                title = Text(video.title, style="bold green")
            else:
                title = video.title

            # Dim if already seen
            if video.seen:
                title = Text(video.title, style="dim")
            row = (video.published_at, title, video.duration, video.has_summary)
            self.add_row(*row, key=video.video_id)

    def action_get_video_info(self):
        """Get detailed information about the current row's video"""
        if not self.videos:
            return
            
        row = self.cursor_row
        if row >= len(self.videos):
            return
            
        video = self.videos[row]
        video.duration = get_video_duration(video)


        # Refresh the table with updated duration
        self.update_cell(
            row_key=video.video_id,
            column_key="duration",
            value=video.duration)

        # db_service = DatabaseService()
        async_db_service = MongoDBAsyncClient()

        self.run_worker(
            async_db_service.update_video_duration(video.video_id, video.duration),
            exclusive=False,
        )

        self.app.notify("Updated duration", title="Video Information")


    def action_style_row(self):
        """Toggle the seen status of the current row's video"""
        if not self.videos:
            return

        row = self.cursor_row
        if row >= len(self.videos):
            return

        video = self.videos[row]
        video.seen = not video.seen

        # Update in database
        db_service = DatabaseService()
        db_service.update_video_seen_status(video.video_id, video.seen)

        # Refresh the table
        self.update_table(self.key, self.videos)

        # Restore cursor position
        self.move_cursor(row=row)

    def action_show_worker_status(self):
        """Show status of all workers, especially AI summary workers"""
        # Get all workers
        all_workers = list(self.app.workers)

        # Filter AI summary workers
        ai_workers = [
            worker for worker in all_workers
            if worker.group == "ai_summary"
        ]

        # Count states for AI workers
        ai_pending = sum(1 for w in ai_workers if w.state == WorkerState.PENDING)
        ai_running = sum(1 for w in ai_workers if w.state == WorkerState.RUNNING)
        ai_success = sum(1 for w in ai_workers if w.state == WorkerState.SUCCESS)
        ai_error = sum(1 for w in ai_workers if w.state == WorkerState.ERROR)
        ai_cancelled = sum(1 for w in ai_workers if w.state == WorkerState.CANCELLED)

        # Count total workers by state
        total_pending = sum(1 for w in all_workers if w.state == WorkerState.PENDING)
        total_running = sum(1 for w in all_workers if w.state == WorkerState.RUNNING)

        # Build notification message
        message = f"AI Summary Workers:\n"
        message += f"  Pending: {ai_pending}\n"
        message += f"  Running: {ai_running}\n"
        message += f"  Success: {ai_success}\n"
        message += f"  Error: {ai_error}\n"
        message += f"  Cancelled: {ai_cancelled}\n"
        message += f"\nTotal Workers:\n"
        message += f"  Pending: {total_pending}\n"
        message += f"  Running: {total_running}\n"
        message += f"  Total Active: {len(all_workers)}"

        self.app.notify(message, title="Worker Status")

    @on(DataTable.RowSelected)
    def open_url_in_browser(self, event: DataTable.RowSelected):
        """Open the selected video in browser"""
        video_id = event.row_key.value
        self.app.open_url(f"https://www.youtube.com/watch?v={video_id}")