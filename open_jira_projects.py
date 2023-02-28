import sublime
import sublime_plugin
import os

from datetime import datetime, timedelta

settings = None
def plugin_loaded():
	global settings
	# this file contains the tags that will be indented/unindented, etc.
	settings =  sublime.load_settings('alfaco.sublime-settings')
class OpenJiraProjectsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
	# Récupère la sélection de l'utilisateur
		selection = self.view.substr(self.view.sel()[0])
		jira_conf=settings.get("jira")
		print(jira_conf)
		#sublime.message_dialog()
		# for region in self.view.sel():
		# 	self.view.insert(edit, region.begin(), settings.get('alfaco_delimiter'))
		
class DonneNomFichierCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Récupère la vue active
        active_view = sublime.active_window().active_view()

        # Récupère le nom du fichier associé à la vue active
        file_name = active_view.file_name()

        # Si le nom du fichier est disponible, l'affiche dans le widget
        if file_name:
            message = "Le fichier ouvert dans la vue actuelle est : " + os.path.basename(file_name)
        else:
            message = "Aucun fichier ouvert dans la vue actuelle"
        print(message)
        # Ouvre le widget et y affiche le message
        # sublime.active_window().run_command("show_panel", {"panel": "console", "toggle": False})
        # panel = sublime.active_window().find_output_panel("console")
        # panel.run_command("append", {"characters": message})
class InsertTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        # Récupère l'emplacement du curseur
        
        pos = self.view.sel()[0].begin()
        # Insère le texte à l'emplacement du curseur
        self.view.insert(edit, pos, text)
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