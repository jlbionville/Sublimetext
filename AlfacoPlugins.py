# -*- coding: utf-8 -*-

import sublime
import sublime_plugin
import os
import re
import json
from datetime import datetime, timedelta
import webbrowser
import time
import sys

from os.path import dirname
sys.path.insert(0, dirname(__file__))
import modules.tools
from modules.configuration import Configuration
from modules.tools import callApiRest,getOrganisationUrl,saveFichier,getUrlToGetJiraProjects

settings_alfaco= None
settings_atlassian = None
settings_sublime = None
configuration = None

# Faire une init de l'instance configuration

def plugin_loaded():
    global settings_alfaco
    global settings_sublime
    global settings_atlassian
    global configuration
    # this file contains the tags that will be indented/unindented, etc.    
    settings_alfaco =  sublime.load_settings('alfaco.sublime-settings')    
    settings_sublime = sublime.load_settings('Preferences.sublime-settings')
    settings_atlassian = sublime.load_settings('alfaco-atlassian.sublime-settings')
    setSetting("organisation","business-projects")
    configuration = Configuration()
    #TODO: gerer les clefs dans un dictionnaire
    configuration.setJiraAuthorisation("jlbionville@alfaco.fr",getSetting('jira_password'))
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
def setSetting(key,value):
    settings_sublime.set(key,value)
def getConfigurationForApiRestCall():
    # mettre les informations dans l'instance Configuration
    # utiliser l'instance Configuration pour obtenir ses informations
    return {"auth" : (getSetting("jira_login"), getSetting('jira_password')),
    "headers" : {'Content-type': 'application/json;charset=UTF-8','Accept': 'application/json'},
    "url" : 'https://{}.atlassian.net/rest/api/latest/'.format(configuration.__jira_project__)
    }        
class OpenJiraProjectsCommand(sublime_plugin.TextCommand):
    def run(self, edit):

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
        active_view = sublime.active_window().active_view()
        region = sublime.Region(0, self.view.size())
        contenu = self.view.substr(region)
        # configu=getConfigurationForApiRestCall()
        # configu["url"]=configu["url"]+"issue/"
        configu={
        "url":configuration.getBaseUrlForRESTApi()+"issue/",
        "headers":configuration.getKeyValue("headers"),
        "auth":(configuration.getJiraAuthorisation())
        }
        print ("AppelRestApiCommand - configu: {}".format(configu))
        texte=callApiRest(contenu,configu)

        ## affichage de la réponse
        new_view = self.view.window().new_file()
        new_view.run_command("insert", {"characters": texte})  

        # Obtenir l'heure actuelle pour créer un nom de fichier unique  
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        # Définir le nom de fichier à utiliser (avec l'horodatage)
        repertoire=getSetting("path_json_files_folder")
        filename = "{}\\error_api_call_{}.html".format(repertoire,timestamp)
        
        # la réponse de l'appel REST
        saveFichier(texte,filename)

        reponse_json=json.loads(texte)
        jira_file_name="{}\\{}.json".format(repertoire,reponse_json["key"])
        # le fichier json utilisé pour l'appel REST
        saveFichier(contenu,jira_file_name)
        
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

class GetJiraListForOrganisationCommand(sublime_plugin.TextCommand):
    
    def run(self, edit):
        configu=getConfigurationForApiRestCall()
        # configu["url"]=getOrganisationUrl(configuration.__organisation__)+"project/"
        configu={
        "url":configuration.getBaseUrlForRESTApi()+"project/",
        "headers":configuration.getKeyValue("headers"),
        "auth":(configuration.getJiraAuthorisation())
        }        
        print("GetJiraListForOrganisationCommand :{}".format(configu))
        liste,status_code,headers=getUrlToGetJiraProjects(configu)
        configuration.setListKeyJiraProject(liste)
        self.view.show_popup_menu(liste, self.on_done)

    def on_done(self, index):
        liste=configuration.getListKeyJiraProject()
        print("GetJiraListForOrganisationCommand => la liste des projects : {}".format(liste))
        pattern = re.compile(r'^\w+')
        print("la clef : {}".format(pattern.match(liste[index]).group()))
        configuration.setKeyValue("project_key",pattern.match(liste[index]).group())
        # configuration.setKeyValue("project_key",liste[index])
        #self.view.run_command('insert_text', {'args': {'text': configuration.__jira_project__[index]}})

class GetListOrganisationCommand(sublime_plugin.TextCommand):
    __key__=[]
    def run(self, edit):
        # print(configuration.__organisation__)
        # TODO : utiliser la configuration
        atlassian=getSetting("atlassian")
        #self.__keys__ = [list(org.keys())[0] for org in organisations['organisations']]
        # print( atlassian['organisations'].keys())
        liste=[project for project in atlassian['organisations'].keys()]
        self.view.show_popup_menu(liste, self.on_done)

    def on_done(self, index):
        #self.view.run_command('insert_text', {'args': {'text': self.__keys__[index]}})
        
        atlassian=getSetting("atlassian")
        print("GetListOrganisationCommand \n ==> {}".format(atlassian))
        liste=[project for project in atlassian['organisations'].keys()]
        organisation=atlassian['organisations']
        configuration.setKeyValue("default_organisation",organisation[liste[index]]["url_key"])
        print("GetListOrganisationCommand \n ==> la clef pour l'url {} ".format(configuration.getKeyValue("default_organisation")))
        

class SetJiraProjectInSnippetCommand(sublime_plugin.TextCommand):
    def run(self, edit, args):
        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)
        pattern = r'"key"\s*:\s*(""|\'\')'
        content = re.sub(pattern, r'"key": "{}"'.format(args['text']), content)
        self.view.replace(edit, region, content)

class InitJsonJiraCommand(sublime_plugin.TextCommand):
    def run(self, edit,**args):
        current_line = self.view.substr(self.view.line(self.view.sel()[0]))
        new_view = self.view.window().new_file()
        new_view.set_name("Init new Jira")
        new_view.set_scratch(True)
        print(current_line)
        # Insère le contenu du snippet dans la nouvelle vue
  
        args["selection"]=current_line.strip()
        args['jira_key']=configuration.getKeyValue('project_key')
        print(args)
        new_view.run_command("insert_snippet", args)
        # new_view.run_command("insert", {"content":current_line})
class ShowSelectedInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Récupère le texte sélectionné dans la vue active
        # selection = self.view.substr(self.view.sel()[0])
        nput_view = self.window.show_input_panel(caption="Example", initial_text="Example", on_done = None, on_change = None, on_cancel = None)
        input_view.add_regions("example", [sublime.Region(0, 7)], scope = "region.redish", flags = sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SQUIGGLY_UNDERLINE)

        # Affiche le texte sélectionné dans un panneau de sortie
        #sublime.active_window().run_command("show_panel", {"panel": "output.show_selected_text"})
        # output_view = sublime.active_window().get_input_panel("show_selected_text")
        # output_view.set_read_only(False)
        # output_view.run_command("append", {"characters": selection})
        # output_view.set_read_only(True)