import sublime
def addSetting(settings):
	'''
	charge les différents fichiers settings nécessaires pour le package
	renvoie un setting qui est une aggrégation des différents fichiers
	'''
	print('dans le addSetting {}'.format(settings.get('jira')))

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

	
