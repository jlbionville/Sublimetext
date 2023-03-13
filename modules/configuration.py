# -*- coding: utf-8 -*-

import sublime


class Configuration(object):
	"""docstring for Configuration"""
	# __organisation__=""
	# __jira_project__=""
	dictionnary={
	    "jira":
	    {
	        "organisation_key": "",
	        "project_key": "",
	        "password": "",
	        "login": ""
	    },
	    "organisations":{},"api_rest_version":"2",

	    "headers": {"Content-type": "application/json;charset=utf-8","Accept": "application/json"},

	}
	listeKeyJiraProject=[]
	def __init__(self):
		super(Configuration, self).__init__()
	# def __init__(self,dictionnaire):
	# 	super(Configuration, self).__init__()	
	# 	dictionnary=dictionnaire
	# def __init__(self,organisation,project):
	# 	super(Configuration, self).__init__()	
	# 	dictionnary=dictionnaire
	# 	__organisation__=organisation
	# 	__jira_project__=project
	def setKeyValue(self,key,value):
		self.dictionnary[key]=value
	def getKeyValue(self,key):
		return self.dictionnary[key]
	def setJiraAuthorisation(self,login,password):
		self.dictionnary["jira"]["login"]=login
		self.dictionnary["jira"]["password"]=password
	def getJiraAuthorisation(self,):
		return (self.dictionnary["jira"]["login"], self.dictionnary["jira"]["password"])
	def getBaseUrlForRESTApi(self,):
		return 'https://{}.atlassian.net/rest/api/{}/'.format(self.getKeyValue("default_organisation"),
			self.getKeyValue("api_rest_version"))
	def setListKeyJiraProject(self,liste):
		self.listeKeyJiraProject=liste
	def getListKeyJiraProject(self):
		return self.listeKeyJiraProject
	def setOrganisation(organisation,organisationProjects={}):
		self.dictionnary[organisation]=organisationProjects
	def getOrganisationJiraProjects(organisation):
		return self.dictionnary[organisation]

	
