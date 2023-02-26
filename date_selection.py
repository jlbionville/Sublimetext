import sublime
import sublime_plugin
from datetime import datetime, timedelta

class DateSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get current date and time
        current_time = datetime.now().strftime("%Y-%m-%d")

        # Get selected text and calculate number of days


        # Round up to nearest whole number
        num_days = int(self.view.substr(self.view.sel()[0]))

        # Add number of days to current time
        future_time = (datetime.now() + timedelta(days=num_days)).strftime("%Y-%m-%d")

        # Format output string
        output = "##dt: {} ".format( future_time)

        # Display output in a new buffer
        new_view = self.view.window().new_file()
        new_view.run_command("insert", {"characters": output})
