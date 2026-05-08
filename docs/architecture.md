# Architecture

## Vue d'ensemble

Le plugin est une collection de commandes Sublime Text qui partagent un état centralisé (`Configuration`) et accèdent à l'API REST Atlassian via un mince wrapper `requests`.

```
                   ┌────────────────────────────────────────────┐
                   │            Sublime Text plugin host         │
                   │                                             │
   plugin_loaded() │  ┌───────────────────────────────────────┐  │
   ───────────────►│  │ AlfacoPlugins.py                      │  │
                   │  │   • settings_alfaco                   │  │
                   │  │   • settings_sublime                  │  │
                   │  │   • settings_atlassian                │  │
                   │  │   • configuration  (Configuration)    │  │
                   │  └───────────────────┬───────────────────┘  │
                   │                      │ utilise               │
                   │  ┌───────────────────▼───────────────────┐  │
                   │  │ modules/configuration.py              │  │
                   │  │   class Configuration                 │  │
                   │  │     dictionnary{ jira, headers, … }   │  │
                   │  │     listeKeyJiraProject               │  │
                   │  └───────────────────┬───────────────────┘  │
                   │                      │ injectée comme       │
                   │                      │ "configu" pour       │
                   │  ┌───────────────────▼───────────────────┐  │
                   │  │ modules/tools.py                      │  │
                   │  │   callApiRest(body, conf, verb)       │  │
                   │  │   getUrlToGetJiraProjects(conf)       │  │
                   │  │   saveFichier / readFichier           │  │
                   │  └───────────────────┬───────────────────┘  │
                   └──────────────────────┼────────────────────  ┘
                                          │ HTTPS (verify=False)
                                          ▼
                          https://<org>.atlassian.net/rest/api/<v>/
```

## Cycle de vie

### Démarrage (`plugin_loaded()`)

Sublime appelle automatiquement `plugin_loaded()` après le chargement du package. La fonction :

1. Charge les **trois fichiers settings** dans des globales du module (`settings_alfaco`, `settings_sublime`, `settings_atlassian`).
2. Force `organisation = "business-projects"` dans `Preferences.sublime-settings` via `setSetting()` (effet de bord persistant — voir [troubleshooting.md](troubleshooting.md#mutation-des-prefs-au-chargement)).
3. Instancie un singleton `configuration = Configuration()`.
4. Pose le couple `(login, password)` Jira dans la configuration. **Note** : `jlbionville@alfaco.fr` est codé en dur, seul le password vient des settings — voir [troubleshooting.md](troubleshooting.md#login-jira-coden-dur).
5. Pose `api_rest_version` depuis les settings.

```python
def plugin_loaded():
    global settings_alfaco, settings_sublime, settings_atlassian, configuration
    settings_alfaco    = sublime.load_settings('alfaco.sublime-settings')
    settings_sublime   = sublime.load_settings('Preferences.sublime-settings')
    settings_atlassian = sublime.load_settings('alfaco-atlassian.sublime-settings')
    setSetting("organisation","business-projects")
    configuration = Configuration()
    configuration.setJiraAuthorisation("jlbionville@alfaco.fr", getSetting('jira_password'))
    configuration.setKeyValue("api_rest_version", getSetting("api_rest_version"))
```

### Exécution d'une commande

Toutes les commandes héritent de `sublime_plugin.TextCommand` (ou `WindowCommand`). Sublime instancie une commande par invocation, lui passe l'`edit` en cours, et la commande lit/mute :
- la **vue active** (`self.view` ou `sublime.active_window().active_view()`) ;
- la **configuration globale** (`configuration.getKeyValue(...)`).

## Structure du dépôt

```
.
├── AlfacoPlugins.py            # Entry point — toutes les commandes Jira/Atlassian + utilitaires
├── AlfacoCompletion.py         # Listener d'autocomplétion (Python uniquement) — squelette démo
├── text_to_table.py            # Une commande isolée (text_to_table)
├── modules/
│   ├── __init__.py             # Vide — fait de "modules" un package Python
│   ├── configuration.py        # Classe Configuration (état partagé)
│   ├── tools.py                # Wrapper requests (callApiRest, getUrlToGetJiraProjects)
│   └── atlassian.py            # Squelette vide
├── snippets/
│   ├── *.sublime-snippet       # Snippets racine (jira, page, childPage, space, alfaco-key)
│   ├── jira/
│   │   └── jira.sublime-snippet
│   └── confluence/
│       ├── page.sublime-snippet
│       ├── childPage.sublime-snippet
│       └── space.sublime-snippet
├── macros/
│   ├── addjira.sublime-macro
│   └── replace.sublime-macro
├── alfaco.sublime-settings              # Settings fonctionnels du plugin
├── alfaco-atlassian.sublime-settings    # Catalogue des organisations
├── Default (Linux).sublime-keymap       # Keybindings — divergent par OS (cf. usage.md)
├── Default (Windows).sublime-keymap
├── Default (OSX).sublime-keymap
├── Main.sublime-menu                    # Tools → Alfaco + Preferences → Package Settings
├── Context.sublime-menu                 # Clic droit dans l'éditeur
├── Side Bar.sublime-menu                # Clic droit dans la sidebar
├── Default.sublime-commands             # Palette de commandes
├── package-metadata.json                # Métadonnées Package Control
├── README.md                            # Stub (à remplir)
├── CLAUDE.md                            # Guide pour assistants IA
└── docs/                                # Cette documentation
```

## Modules

### `AlfacoPlugins.py`

Point d'entrée. Définit toutes les classes de commandes Jira/Atlassian + utilitaires. Voir [usage.md](usage.md#référence-des-commandes) pour la liste complète.

Conventions Sublime appliquées :
- Classe `XxxCommand` (suffixe `Command`) → nom de commande `xxx` (snake_case sans le suffixe).
- `TextCommand` → opère sur une vue (a un `edit` token).
- `WindowCommand` → opère sur la fenêtre (pas de buffer requis).
- `EventListener` → `AlfacoCompletion` (dans son propre fichier).

### `modules/configuration.py`

Classe `Configuration` — singleton manuel instancié dans `plugin_loaded()`.

```python
class Configuration:
    dictionnary = {
        "jira": { "organisation_key": "", "project_key": "", "password": "", "login": "" },
        "organisations": {},
        "api_rest_version": "2",
        "headers": { "Content-type": "application/json;charset=utf-8",
                     "Accept": "application/json" }
    }
    listeKeyJiraProject = []

    def setKeyValue(self, key, value): …
    def getKeyValue(self, key): …
    def setJiraAuthorisation(self, login, password): …
    def getJiraAuthorisation(self): return (login, password)  # tuple pour requests.auth
    def getBaseUrlForRESTApi(self):
        return f'https://{default_organisation}.atlassian.net/rest/api/{api_rest_version}/'
    def setListKeyJiraProject(self, liste): …
    def getListKeyJiraProject(self): …
```

> **Attention** : `dictionnary` et `listeKeyJiraProject` sont des **attributs de classe** (pas d'instance). Si plusieurs `Configuration()` étaient instanciées, ils seraient partagés. Dans le code actuel un seul singleton existe, donc OK.

> **Méthodes incomplètes** : `setOrganisation` et `getOrganisationJiraProjects` sont déclarées sans `self` — elles lèveront `TypeError` si appelées. Voir [troubleshooting.md](troubleshooting.md#configuration-méthodes-cassées).

### `modules/tools.py`

Helpers HTTP et fichiers.

| Fonction | Rôle |
|---|---|
| `getOrganisationUrl(org)` | Retourne `https://{org}.atlassian.net/rest/api/latest/`. **Non utilisée** par le code actif — `Configuration.getBaseUrlForRESTApi()` est préférée. |
| `saveFichier(contenu, nomFichier)` | `open(file, 'w')` simple. Pas d'encodage explicite, pas de gestion d'erreur. |
| `readFichier(nomFichier)` | Lecture inverse. |
| `callApiRest(contenu, configuration, http_verb="GET")` | `requests.request(verb, url, headers, auth, data, verify=False)`. Retourne soit un message formaté (sur 200), soit `response.text`. |
| `getUrlToGetJiraProjects(configuration)` | `GET` la liste des projets, retourne `(["KEY-Nom", …], status_code, content_brut)`. |

### `modules/atlassian.py`

Fichier squelette (header `# -*- coding: utf-8 -*-` seul). Réservé pour de futures fonctions Atlassian découplées de `tools.py`.

### `text_to_table.py`

Commande isolée — n'appartient pas à `AlfacoPlugins.py` pour des raisons historiques. Pourrait être déplacée dans `AlfacoPlugins.py` ou un `modules/editing.py` dédié.

### `AlfacoCompletion.py`

`EventListener` qui propose une autocomplétion statique (`def`, `class`, `None`, `True`, `False`) en scope `source.python`. Démonstration plus qu'utilité réelle (Sublime fournit déjà ces complétions).

## Modèle de données

### `Configuration.dictionnary` à l'exécution

Après `plugin_loaded()` puis sélection d'une organisation et d'un projet :

```python
{
    "jira": {
        "organisation_key": "",
        "project_key": "",
        "password": "<token>",
        "login": "jlbionville@alfaco.fr"
    },
    "organisations": {},
    "api_rest_version": "3",
    "headers": {"Content-type": "application/json;charset=utf-8", "Accept": "application/json"},
    "default_organisation": "business-projects",  # posé par GetListOrganisationCommand
    "project_key": "BUS"                          # posé par GetJiraListForOrganisationCommand
}
```

### Format `configu` passé à `callApiRest`

```python
configu = {
    "url":     configuration.getBaseUrlForRESTApi() + "issue/",
    "headers": {"Content-type": "application/json", "Accept": "application/json"},
    "auth":    (login, password)
}
```

> Note : les `headers` reposés dans `AppelRestApiCommand` **écrasent** ceux de la `Configuration` (`charset=utf-8` perdu).

## Flux d'un `appel_rest_api`

```
1. Utilisateur édite le buffer JSON.
2. Utilisateur invoque alt+j → AppelRestApiCommand.run(edit)
3. Capture du buffer entier (région 0..size).
4. Construction de configu (url + headers + auth).
5. callApiRest(contenu, configu, http_verb="POST")
       └── requests.request("POST", url, …, verify=False)
6. La réponse texte est insérée dans un nouveau buffer.
7. saveFichier(reponse, "<folder>\\error_api_call_<ts>.html")
8. json.loads(reponse) → reponse_json["key"]
9. saveFichier(payload_envoye, "<folder>\\<key>.json")
```

## Appels HTTP

### TLS désactivé

`verify=False` est passé à toutes les requêtes (`callApiRest`, `getUrlToGetJiraProjects`). Cela :
- évite des erreurs derrière un proxy d'entreprise qui ré-émet les certificats ;
- supprime la protection contre les MITM ;
- génère des `InsecureRequestWarning` dans la console (urllib3).

À traiter : soit conditionner via une clé settings (`tls_verify: true|false`), soit pointer vers un bundle CA d'entreprise.

### Pas de timeout

Aucun `timeout=` n'est passé. Si le serveur Atlassian ne répond pas, Sublime peut bloquer indéfiniment l'UI thread. À ajouter (par exemple `timeout=(5, 30)`).

### Pas de gestion d'erreur sur l'IO disque

`saveFichier` ne gère ni dossier inexistant, ni permission refusée. L'exception remontera dans la console Sublime.

## Diagramme de séquence : création d'un ticket

```
Utilisateur     Sublime            AlfacoPlugins        Configuration       tools.py            Atlassian
    │             │                      │                    │                │                    │
    │ Tools→Jira→ │                      │                    │                │                    │
    │ Select Org  │                      │                    │                │                    │
    │────────────►│ get_list_organisation│                    │                │                    │
    │             │─────────────────────►│  show_popup_menu   │                │                    │
    │             │                      │  on_done(idx) ─────┼────set "default_organisation"       │
    │ Tools→Jira→ │                      │                    │                │                    │
    │ Select Proj │                      │                    │                │                    │
    │────────────►│ get_jira_list_for_…  │                    │                │                    │
    │             │─────────────────────►│  buildBaseUrl ─────►                │                    │
    │             │                      │  callApiRest ──────┼───────────────►│ GET /project/      │
    │             │                      │                    │                │───────────────────►│
    │             │                      │                    │                │◄───────────────────│
    │             │                      │  show_popup_menu   │                │                    │
    │             │                      │  on_done(idx) ─────┼────set "project_key"                │
    │ super+n     │                      │                    │                │                    │
    │────────────►│ init_json_jira       │                    │                │                    │
    │             │─────────────────────►│  insert_snippet (jira.sublime-snippet, jira_key, duedate) │
    │ alt+j       │                      │                    │                │                    │
    │────────────►│ appel_rest_api       │                    │                │                    │
    │             │─────────────────────►│  callApiRest ──────┼───────────────►│ POST /issue        │
    │             │                      │                    │                │───────────────────►│
    │             │                      │                    │                │◄──────── 201 ──────│
    │             │  new_view            │                    │                │                    │
    │             │  saveFichier (réponse)                                                          │
    │             │  saveFichier (payload, KEY.json)                                                │
```
