import sublime
import sublime_plugin

class InsertTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        # Récupère l'emplacement du curseur
        
        pos = self.view.sel()[0].begin()
        # Insère le texte à l'emplacement du curseur
        self.view.insert(edit, pos, text)
