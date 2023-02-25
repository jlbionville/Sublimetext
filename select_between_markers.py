import sublime
import sublime_plugin

class SelectBetweenMarkersCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Récupère les positions des marqueurs de début et de fin
        start = self.view.find('<start>', 0)
        end = self.view.find('<end>', 0)
        
        # Sélectionne le texte entre les marqueurs
        region = sublime.Region(start.end(), end.begin())
        self.view.sel().clear()
        self.view.sel().add(region)

        # Récupère le texte sélectionné
        selected_text = self.view.substr(region)

        # Insère le texte sélectionné à la fin du document
        self.view.insert(edit, self.view.size(), '\n' + selected_text)
