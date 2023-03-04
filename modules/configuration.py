import sublime


class Configuration(object):
	"""docstring for Configuration"""
	__organisation__=""
	__jira_project__=""
	dictionnary={
	    "jira":
	    {
	        "organisation_key": "",
	        "project_key": "",
	        "password": "",
	        "login": ""
	    },
	    "headers": {'Content-type': 'application/json;charset=UTF-8','Accept': 'application/json'},

	}
	listeKeyJiraProject=[]
	def __init__(self):
		super(Configuration, self).__init__()
	
		





	
