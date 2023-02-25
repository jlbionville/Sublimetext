import sublime
import sublime_plugin

class RemoveTagCommand(sublime_plugin.TextCommand):
    def run(self, edit,text):
        # Récupère le mot à supprimer
        word = self.view.substr(self.view.word(self.view.sel()[0].begin()))
        # Crée un objet de recherche pour trouver toutes les occurrences du mot
        print(text)
        tags=text.split(',')
        for tag in tags:
        	print(tag)
	        search = self.view.find_all(tag)
	        # Supprime toutes les occurrences du mot à l'emplacement du curseur
	        for region in reversed(search):
	            self.view.erase(edit, region)
