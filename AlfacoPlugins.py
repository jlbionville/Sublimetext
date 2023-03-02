import sublime
import sublime_plugin
import os
import re
import requests
from datetime import datetime, timedelta
import webbrowser
import time
import sys

from os.path import dirname
sys.path.insert(0, dirname(__file__))
import modules.tools
from modules.configuration import addSetting

settings_alfaco= None
settings_atlassian = None
settings_sublime = None

def plugin_loaded():
    global settings_alfaco
    global settings_sublime
    global settings_atlassian
	# this file contains the tags that will be indented/unindented, etc.
    settings_alfaco =  sublime.load_settings('alfaco.sublime-settings')    
    settings_sublime = sublime.load_settings('Preferences.sublime-settings')
    settings_atlassian = sublime.load_settings('alfaco-atlassian.sublime-settings')
def getSetting(key):
    '''
    charge les différents fichiers settings nécessaires pour le package
    renvoie un setting qui est une aggrégation des différents fichiers
    '''
    if settings_alfaco.has(key):
        return settings_alfaco.get(key)
    if settings_sublime.has(key):
        return settings_sublime.get(key)
    if settings_atlassian.has(key):
        return settings_atlassian.get(key)
class OpenJiraProjectsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selection = self.view.substr(self.view.sel()[0])
        # jira_login=settings_sublime.get("jira_login")
        # settings_sublime = sublime.load_settings('Preferences.sublime-settings')
        # jira_password = settings_sublime.get('jira_password')
        print(getSetting('jira_password'))
        print(getSetting('jira_login'))
		
class DonneNomFichierCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Récupère la vue active
        active_view = sublime.active_window().active_view()

        # Récupère le nom du fichier associé à la vue active
        file_name = active_view.file_name()

        # Si le nom du fichier est disponible, l'affiche dans le widget
        if file_name:
            message = "Le fichier ouvert dans la vue actuelle est : " + file_name
            # message = "Le fichier ouvert dans la vue actuelle est : " + os.path.basename(file_name)
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
class AppelRestApiCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        jira_conf=settings.get("jira")
        settings_sublime = sublime.load_settings('Preferences.sublime-settings')
        jira_password = settings_sublime.get('jira_password')
        # print("login : {} password :{}".format(jira_conf["login"],jira_password))        
        active_view = sublime.active_window().active_view()

        # Récupère le nom du fichier associé à la vue active
        file_name = active_view.file_name()   
        print(file_name)     
        with open(file_name, 'r') as f:
            contenu = f.read()
        url = 'https://business-projects.atlassian.net/rest/api/2/issue/'

        # Définir les en-têtes d'authentification pour JIRA
        headers = {'Content-type': 'application/json'}
        username = jira_conf["login"]
        password = jira_password
        auth = (username, password)

        # Envoyer la requête POST à JIRA pour créer un ticket
        response = requests.post(url, headers=headers, auth=auth, data = contenu,verify=False)
        # response = requests.post(url, headers=headers, auth=auth, files = {'file': open(file_name, 'rb')},verify=False)
        # response = requests.post(url, headers=headers, auth=auth, files = {'file': open(file_name, 'rb')},cert='G:\\Mon Drive\\business\\atlassian.net.crt')
        # Vérification de la réponse de la requête
        if response.status_code == 200:
            # Affichage de la réponse de la requête
            print("Le code de statut de la réponse est :", response.status_code)
            print("Les en-têtes de la réponse sont :", response.headers)
            print("Le corps de la réponse est :", response.content)
        else:
            # print("Erreur lors de la requête : " + response.text)
            new_view = self.view.window().new_file()
            new_view.run_command("insert", {"characters": response.text})  
            # Obtenir l'heure actuelle pour créer un nom de fichier unique  
            timestamp = time.strftime('%Y%m%d-%H%M%S')



            # Définir le nom de fichier à utiliser (avec l'horodatage)
            filename = "error_api_call.html"

            # Écrire le contenu HTML dans le fichier
            with open(filename, 'w') as f:
                f.write(response.text)

            # Ouvrir le fichier dans un navigateur
            webbrowser.open(os.path.abspath(filename))           

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



class MyContextMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.show_popup_menu(['Item 1', 'Item 2', 'Item 3'], self.on_done)

    def on_done(self, index):
        if index == 0:
            self.view.run_command('insert_text', {'args': {'text': 'Item 1'}})
        elif index == 1:
            self.view.run_command('insert_text', {'args': {'text': 'Item 2'}})
        elif index == 2:
            self.view.run_command('insert_text', {'args': {'text': 'Item 3'}})

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, args):
        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)

        pattern = r'"key"\s*:\s*(""|\'\')'
        content = re.sub(pattern, r'"key": "{}"'.format(args['text']), content)

        self.view.replace(edit, region, content)