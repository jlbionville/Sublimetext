import sublime
import sublime_plugin

class TextToTableCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Récupérer la sélection courante
        selection = self.view.sel()[0]

        # Récupérer le contenu de la sélection
        selected_text = self.view.substr(selection)

        # Séparer le texte en lignes
        lines = selected_text.split('\n')

        # Créer un tableau à partir des lignes
        table = [line for line in lines if line.strip()]

        # Insérer le tableau à la fin du fichier
        self.view.insert(edit, self.view.size(), '\n' + '\n'.join(table))
