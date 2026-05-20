from textual.screen import ModalScreen
from textual.widgets import Markdown
from textual.binding import Binding


class SummaryScreen(ModalScreen):
    """
    A modal screen that displays a summary of the application state.
    """
    BINDINGS = [
        Binding("q", "exit", "Exit", show=True),
    ]

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def compose(self):
        yield Markdown(
            f"# Summary\n\n{self.text}"
        )

    def action_exit(self):
        """Exit the modal screen."""
        self.app.pop_screen()