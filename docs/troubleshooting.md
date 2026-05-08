# Troubleshooting & dette technique

Ce document recense les bugs connus, pièges, comportements surprenants et actions correctives à envisager.

## Bugs connus dans le code

### Bug `show_selected_input`

`AlfacoPlugins.py:251` — typo dans le nom de variable :

```python
class ShowSelectedInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        nput_view = self.window.show_input_panel(...)   # ← « nput_view »
        input_view.add_regions(...)                     # ← référence inexistante → NameError
```

**Symptôme** : invoquer la commande lève `NameError: name 'input_view' is not defined`.
**Correction** : renommer `nput_view` → `input_view`.

### Configuration : méthodes cassées

`modules/configuration.py:50-53` — déclarations sans `self` :

```python
def setOrganisation(organisation, organisationProjects={}):
    self.dictionnary[organisation] = organisationProjects   # ← self n'existe pas
def getOrganisationJiraProjects(organisation):
    return self.dictionnary[organisation]
```

**Symptôme** : appel → `TypeError` (mauvais nombre d'arguments) ou `NameError`.
**Correction** : ajouter `self` en premier paramètre, ou supprimer les méthodes si plus utiles.

### Login Jira codé en dur

`AlfacoPlugins.py:38` :

```python
configuration.setJiraAuthorisation("jlbionville@alfaco.fr", getSetting('jira_password'))
```

**Symptôme** : tout utilisateur autre que `jlbionville` envoie un login qui n'a pas le token associé → `401 Unauthorized` à chaque appel.
**Correction** : remplacer par `getSetting("jira_login")` (la clé existe déjà conceptuellement, voir `OpenJiraProjectsCommand` qui l'imprime).

### Mutation des prefs au chargement

`AlfacoPlugins.py:35` :

```python
setSetting("organisation", "business-projects")
```

Cette ligne **écrit** dans `Preferences.sublime-settings` à chaque démarrage de Sublime. Effets :
- Pollue les préférences globales avec une clé propre au plugin.
- Annule toute valeur que l'utilisateur aurait posée.

**Correction** : poser cette valeur dans `configuration` directement (`configuration.setKeyValue("organisation", "business-projects")`), sans toucher au fichier global.

## Pièges multi-OS

### Chemin Windows codé en dur

`alfaco.sublime-settings` et `alfaco-atlassian.sublime-settings` :

```json
"path_json_files_folder": "H:\\Mon Drive\\jira"
```

Sur Linux / macOS, la valeur n'est pas valide. Pire, `AppelRestApiCommand` construit les noms de fichier avec des **backslashes en dur** :

```python
filename = "{}\\error_api_call_{}.html".format(repertoire, timestamp)
jira_file_name = "{}\\{}.json".format(repertoire, reponse_json["key"])
```

**Symptôme** : l'API Jira est bien appelée, mais `saveFichier` lève `FileNotFoundError` ou crée un fichier au nom bizarre `H:\Mon Drive\jira\error_api_call_….html`.
**Correction** : utiliser `os.path.join(repertoire, "error_api_call_{}.html".format(timestamp))`.

### Keymaps divergentes

Les trois fichiers `Default (Linux|Windows|OSX).sublime-keymap` ne contiennent pas les mêmes commandes. Récap dans [usage.md → Raccourcis clavier](usage.md#raccourcis-clavier).

**Conséquence** : un workflow documenté pour Windows (`super+n` puis `alt+j`) ne fonctionne pas sur Linux (rien n'est lié).
**Correction** : aligner les trois keymaps (au minimum sur les commandes Jira centrales `appel_rest_api`, `init_json_jira`, `get_jira_list_for_organisation`).

## Sécurité

### TLS désactivé

Toutes les requêtes utilisent `verify=False` (`modules/tools.py`).

**Symptôme** : `InsecureRequestWarning` à chaque appel ; les MITM ne sont pas détectés.
**Correction** : conditionner via `getSetting("tls_verify")` (défaut `true`), ou pointer vers un bundle CA d'entreprise (`verify="/chemin/vers/cacert.pem"`).

### Mot de passe imprimé en console

`OpenJiraProjectsCommand.run` :

```python
print(getSetting('jira_password'))
print(getSetting('jira_login'))
```

**Symptôme** : le token API apparaît en clair dans la console Sublime — risque en démo, screenshot, ou enregistrement.
**Correction** : retirer ces `print` ou les remplacer par un masquage (`****`).

## Comportements surprenants

### Pas de timeout

`requests.request(...)` est appelé sans `timeout=`. Si le serveur ne répond pas, l'UI thread Sublime bloque indéfiniment (la fenêtre devient non réactive).

**Correction** : ajouter `timeout=(5, 30)` (5 s connexion, 30 s lecture) dans `callApiRest` et `getUrlToGetJiraProjects`.

### Headers réécrits dans `AppelRestApiCommand`

```python
configu["headers"] = configuration.getKeyValue("headers")
…
configu["headers"] = {"Content-type": "application/json", "Accept": "application/json"}  # ← écrase
```

Le `charset=utf-8` posé dans `Configuration.dictionnary["headers"]` est perdu.

**Symptôme** : sur les payloads contenant des accents non échappés, Atlassian peut rejeter (`400`).
**Correction** : ne pas réassigner `configu["headers"]`.

### Snippets en double

Les fichiers suivants sont des doublons à la racine `snippets/` ET dans le sous-dossier :

- `snippets/jira.sublime-snippet` ≈ `snippets/jira/jira.sublime-snippet` (versions divergentes).
- `snippets/page.sublime-snippet` = `snippets/confluence/page.sublime-snippet`.
- `snippets/childPage.sublime-snippet` = `snippets/confluence/childPage.sublime-snippet`.
- `snippets/space.sublime-snippet` = `snippets/confluence/space.sublime-snippet`.

Comme ils partagent le même `tabTrigger`, Sublime peut prendre l'un ou l'autre selon l'ordre de chargement → comportement non déterministe.

**Correction** : supprimer les doublons à la racine et ne garder que les versions sous-dossiers.

### Snippet Jira racine — `duedate` codée

`snippets/jira.sublime-snippet` :

```json
"duedate": "2022-02-23"
```

**Symptôme** : tous les tickets créés ont une échéance dans le passé.
**Correction** : utiliser `${duedate}` (la version `snippets/jira/jira.sublime-snippet` le fait correctement) ou supprimer ce fichier obsolète.

## Diagnostic des erreurs Atlassian

### `401 Unauthorized`

- Vérifier `jira_login` (et le bug du login codé en dur ci-dessus).
- Vérifier que `jira_password` est bien un **token API** (pas le mot de passe du compte).
- Vérifier `default_organisation` dans la console après `Select Organisation` — l'URL doit correspondre à un sous-domaine `.atlassian.net` valide.

### `404 Not Found` sur `/issue/`

- L'URL est `https://{org}.atlassian.net/rest/api/{version}/issue/`. Vérifier `api_rest_version` (`"2"` ou `"3"`).
- Sous API v3, certains champs (notamment `description`) attendent du **Atlassian Document Format** (`{ "type": "doc", "version": 1, "content": [...] }`) et non une simple string. Si la création échoue : passer `api_rest_version` à `"2"`.

### `400 Bad Request` à la création

- Vérifier la `project.key` (doit exister dans Jira et être accessible).
- Vérifier `issuetype.name` (selon le projet, `Task` peut s'appeler `Tâche` en français → utiliser `issuetype.id`).
- Vérifier `priority.name` (certains projets n'ont pas `High`).
- Le payload doit être encapsulé dans `{ "fields": { … } }` — la version « racine » du snippet `jira/jira.sublime-snippet` le fait, l'ancienne `snippets/jira.sublime-snippet` non.

### Le buffer reste bloqué

Voir [Pas de timeout](#pas-de-timeout) — soit le serveur est lent, soit la connectivité réseau est interrompue. En attendant le fix, fermer Sublime et le relancer.

## Checklist de troubleshooting rapide

```
□ La console Sublime (Ctrl+`) affiche-t-elle une exception ?
□ requests est-il importable ? (Console : `from requests import get`)
□ jira_password est-il défini dans User/alfaco.sublime-settings ?
□ default_organisation est-il bien posé après Select Organisation ?
□ project_key est-il bien posé après Select Jira project ?
□ path_json_files_folder existe-t-il et est-il writable ?
□ api_rest_version est-il cohérent avec le format du payload ?
□ Le buffer envoyé est-il un JSON valide ? (essayer pretty_json avant d'envoyer)
```
