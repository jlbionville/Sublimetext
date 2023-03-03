import requests

def getOrganisationUrl(organisation):
        return 'https://{}.atlassian.net/rest/api/2/issue/'.format(organisation)

# def getListJiraProjetForOrganisation(organisation):
        

def saveFichier(contenu, nomFichier):
        with open(nomFichier, 'w') as f:
            f.write(contenu)
def readFichier(nomFichier):
        with open(nomFichier, 'w') as f:
            contenu=f.read()
            return contenu

def callApiRest(contenu, configuration):
        # Envoyer la requête POST à JIRA pour créer un ticket
        print(contenu)
        print(configuration)
        response = requests.post(configuration["url"], headers=configuration["headers"], auth=configuration["auth"], data = contenu,verify=False)
        # Vérification de la réponse de la requête
        if response.status_code == 200:
            # Affichage de la réponse de la requête
            print("Le code de statut de la réponse est :", response.status_code)
            print("Les en-têtes de la réponse sont :", response.headers)
            print("Le corps de la réponse est :", response.content)
            return 'Le code de statut de la réponse est :%s\nLes en-têtes de la réponse sont :%s\nLe corps de la réponse est :%s'%(response.status_code,response.headers,response.content)
        else:
            return response.text
