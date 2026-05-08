# Configuration

Le plugin lit ses paramètres dans **trois fichiers de settings empilés**, agrégés par la fonction `getSetting(key)` de `AlfacoPlugins.py`.

## Ordre de résolution

`getSetting(key)` cherche la première valeur trouvée, dans cet ordre :

1. `alfaco.sublime-settings` (variables fonctionnelles du plugin)
2. `Preferences.sublime-settings` (préférences globales Sublime — c'est là qu'écrit `setSetting()`)
3. `alfaco-atlassian.sublime-settings` (catalogue Atlassian)

Cela signifie qu'une clé définie dans `alfaco.sublime-settings` **masque** celle de `alfaco-atlassian.sublime-settings`. Les valeurs `User/...` fournies par l'utilisateur sont automatiquement fusionnées par Sublime au-dessus des fichiers du package.

## `alfaco.sublime-settings`

Valeurs fonctionnelles du plugin. Le fichier livré dans le package contient :

```json
{
    "alfaco_delimiter": "##",
    "path_json_files_folder": "H:\\Mon Drive\\jira"
}
```

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `alfaco_delimiter` | string | `"##"` | Délimiteur générique utilisé par `modify_setting_from_selection` (et par les snippets futurs). |
| `path_json_files_folder` | string (path) | `"H:\\Mon Drive\\jira"` | Dossier où `appel_rest_api` écrit la réponse HTML et le payload JSON envoyé. **Doit exister**. Backslashes Windows codés en dur — voir [troubleshooting.md](troubleshooting.md#chemin-windows-coden-dur). |

### Clés également lues par le plugin (à définir dans `User/alfaco.sublime-settings`)

| Clé | Type | Lecture | Rôle |
|---|---|---|---|
| `jira_login` | string | `Configuration.setJiraAuthorisation` | Email du compte Atlassian. **Note** : `plugin_loaded()` code en dur `jlbionville@alfaco.fr` — voir [troubleshooting.md](troubleshooting.md#login-jira-coden-dur). |
| `jira_password` | string | `Configuration.setJiraAuthorisation` | **Token API Atlassian**, pas le mot de passe du compte. À générer sur https://id.atlassian.com/manage-profile/security/api-tokens. |
| `api_rest_version` | string (`"2"` ou `"3"`) | `Configuration.setKeyValue` | Version d'API Atlassian utilisée dans l'URL. Défaut interne : `"2"`. |
| `organisation` | string | `setSetting()` initial | Forcée à `"business-projects"` par `plugin_loaded()` — ne pas considérer comme persistante. |

## `alfaco-atlassian.sublime-settings`

Catalogue déclaratif des organisations et leurs URL keys. Structure :

```json
{
    "jira": { … paramètres globaux Jira … },
    "atlassian": {
        "organisations": {
            "<libellé affiché>": {
                "url_key": "<sous-domaine .atlassian.net>",
                "jira": true,
                "confluence": true
            }
        }
    },
    "path_json_files_folder": "H:\\Mon Drive\\jira"
}
```

### Bloc `jira` (par défaut)

```json
{
    "default_organisation": "business-projects",
    "default_project": "BUS",
    "default_tags": "alfaco",
    "default_date_end": "10",
    "default_priority": "normal",
    "default_category": "normal",
    "login": "jlbionville@alfaco.fr",
    "requests": {
        "searchJiraProject": "project/search"
    }
}
```

> **Statut** : ces clés sont déclaratives mais peu/pas relues par le code actuel. Elles sont conservées comme référence pour de futures commandes (recherche de projet, valeurs par défaut d'un nouveau ticket).

### Bloc `atlassian.organisations` (livré)

Chaque entrée représente une organisation Atlassian accessible par le plugin :

| Libellé | `url_key` | Jira | Confluence |
|---|---|:-:|:-:|
| `business projects` | `business-projects` | ✓ | ✓ |
| `e-commerce` | `cloud-shopping` | ✓ | ✗ |
| `mes projets personnels` | `myproject2020` | ✓ | ✓ |
| `mon agence immo` | `nana-immobilier` | ✓ | ✗ |
| `mes projets immobiliers ` | `projets-immobilier` | ✓ | ✗ |
| `alfaco-applications` | `alfaco-applications` | ✓ | ✗ |
| `mes auto formations` | `trainings-projects` | ✓ | ✓ |
| `le cercle des investisseurs` | `cercleimmobilier` | ✓ | ✓ |
| `mes missions alfaco` | `alfaco-missions` | ✓ | ✗ |

L'`url_key` est utilisée pour construire les URL `https://<url_key>.atlassian.net/rest/api/<version>/`.

> **Adaptation à votre contexte** : remplacer ces organisations dans `User/alfaco-atlassian.sublime-settings` (Sublime fusionnera) pour ne lister que les vôtres. Les flags `jira` / `confluence` ne sont pas encore exploités par le code mais documentent l'intention.

## `Preferences.sublime-settings`

C'est le fichier global de Sublime. Le plugin :
- y **lit** toute clé non trouvée dans `alfaco.sublime-settings` (couche intermédiaire) ;
- y **écrit** via `setSetting()` (utilisé une seule fois pour `organisation`).

Aucune action particulière n'est requise sauf si vous voulez surcharger globalement une clé.

## Exemple complet de `User/alfaco.sublime-settings`

```json
{
    "jira_login": "votre.email@domaine.tld",
    "jira_password": "ATATT3xFfGF0…", // token API Atlassian
    "api_rest_version": "3",
    "alfaco_delimiter": "##",
    "path_json_files_folder": "/home/votre-user/jira-payloads"
}
```

## Sécurité

- **Ne jamais committer** `User/alfaco.sublime-settings` contenant un token. Le `.gitignore` du dépôt couvre les artefacts Python mais pas les settings de Sublime.
- Le token API est stocké en clair dans `User/alfaco.sublime-settings`. Pour un usage en équipe, envisager :
  - Variable d'environnement lue dans `plugin_loaded()` au lieu d'un fichier.
  - Récupération via un gestionnaire de secrets (1Password CLI, `pass`, `keyring`) au démarrage du plugin.
- La commande `open_jira_projects` **affiche le token dans la console Sublime** (`print(getSetting('jira_password'))`) — utile en debug, à proscrire en démo ou enregistrement d'écran.
- Tous les appels HTTP désactivent la vérification TLS (`verify=False`). Voir [architecture.md](architecture.md#appels-http) pour le contexte.

## Modification dynamique de la configuration

Quelques clés sont mutées en mémoire pendant la session via `Configuration.setKeyValue()` et **ne sont pas persistées** :

| Clé runtime | Source | Posée par |
|---|---|---|
| `default_organisation` | `url_key` choisie | `GetListOrganisationCommand.on_done` |
| `project_key` | clé Jira choisie | `GetJiraListForOrganisationCommand.on_done` |
| `api_rest_version` | `getSetting("api_rest_version")` | `plugin_loaded` |
| `headers` | dict statique | défaut `Configuration.dictionnary` |

Au prochain rechargement de Sublime, ces valeurs sont reperdues — c'est attendu : on choisit l'organisation et le projet à chaque session.
