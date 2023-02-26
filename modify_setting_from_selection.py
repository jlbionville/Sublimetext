import sublime
import sublime_plugin

class ModifySettingFromSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get selected text
        selected_text = self.view.substr(self.view.sel()[0])

        # Set the new value of the setting
        settings =  sublime.load_settings('alfaco.sublime-settings')
        settings.set('alfaco_delimiter', selected_text)
        #sublime.save_settings("Preferences.sublime-settings")
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), settings.get('alfaco_delimiter'))