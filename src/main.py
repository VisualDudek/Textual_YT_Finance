from textual.app import App
from textual.widgets import Footer
from textual.binding import Binding
from textual.containers import Horizontal
from textual import on

from widgets.list_view import CustomListView
from widgets.data_table import CustomDataTable
from utils import get_initial_data, pickle_data

class MyApp(App):
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "exit", "Exit"),
        Binding("l", "focus_datatable", show=False)
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs) # Does it need to be here?
        self.data = get_initial_data() # Load initial data from pickle file or database
    
    def compose(self):
        yield Footer()
        with Horizontal():
            yield CustomListView()
            yield CustomDataTable()
            
    def on_mount(self):
        list_view = self.query_one(CustomListView)
        list_view.set_data(self.data)
        list_view.focus()
        list_view.index = 0

    def action_exit(self):
        # pickle_data(self.data)
        self.exit()

    def action_focus_datatable(self):
        list_view = self.query_one(CustomListView)
        data_table = self.query_one(CustomDataTable)
        
        if list_view.has_focus:
            data_table.focus()
        else:
            list_view.focus()

    @on(CustomListView.Highlighted)
    def update_data_table(self, event):
        if event.item is not None:
            data_table = self.query_one(CustomDataTable)
            data_table.update_table(event.item.data, self.data[event.item.data])

    @on(CustomListView.DataUpdated) 
    def data_updated(self, event):
        self.data = event.data

def main():
    app = MyApp()
    app.run()

if __name__ == "__main__":
    main()