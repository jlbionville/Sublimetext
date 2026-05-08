# Configuration

Chaque plugin lit ses propres `.sublime-settings`. La résolution est gérée par `AlfacoLib.config.Configuration` :

1. **Runtime** (`config.set()` en mémoire — perdu au redémarrage).
2. **Settings layers** passés au constructeur, dans l'ordre.
3. **Default** explicite passé à `get(key, default=...)`.

## `AlfacoAtlassian/alfaco-atlassian.sublime-settings`

Fichier livré (vide par défaut) :

```json
{
    "api_rest_version": "3",
    "tls_verify": true,
    "path_json_files_folder": "",
    "jira_login": "",
    "jira_password": "",
    "default_organisation": "",
    "atlassian": {
        "organisations": {
            "business projects": { "url_key": "business-projects", "jira": true, "confluence": true }
        }
    }
}
```

À surcharger dans `User/alfaco-atlassian.sublime-settings`.

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `jira_login` | string | `""` | Email du compte Atlassian. |
| `jira_password` | string | `""` | **Token API** (pas le mot de passe du compte). |
| `default_organisation` | string | `""` | URL key de l'organisation `https://<X>.atlassian.net/`. Posée en runtime par `select_organisation`. |
| `api_rest_version` | string | `"3"` | `"2"` ou `"3"`. |
| `tls_verify` | bool | `true` | Désactiver pour proxy d'entreprise qui ré-émet les certificats. |
| `path_json_files_folder` | string | `""` | Dossier où `create_jira_issue` écrit la réponse + le payload. Doit exister. |
| `headers` | object | `{Content-type: application/json, Accept: application/json}` | Headers HTTP par défaut. |
| `atlassian.organisations` | object | (catalogue exemple) | Catalogue des organisations pour le popup `select_organisation`. |
| `debug` | bool | `false` | Active les `print` debug du logger. |

## `AlfacoEditing/alfaco-editing.sublime-settings`

```json
{
    "alfaco_delimiter": "##"
}
```

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `alfaco_delimiter` | string | `"##"` | Délimiteur utilisé par `modify_setting_from_selection` et certains snippets. |

## `AlfacoLib` et `AlfacoCompletion`

Aucun settings dédié.

## Sécurité

- **Ne JAMAIS commiter `User/alfaco-atlassian.sublime-settings`** contenant un token. Par défaut, Sublime stocke le `User/` hors du dépôt (dans `<Packages>/User/`), donc pas de risque automatique. Mais si vous gérez des dotfiles/`User/` versionné, ajouter `alfaco-atlassian.sublime-settings` à votre `.gitignore` perso.
- Le token est stocké en clair côté Sublime. Pour un usage en équipe, envisager :
  - Variable d'environnement lue dans `plugin_loaded()`.
  - Gestionnaire de secrets (1Password CLI, `pass`, `keyring`).
- La commande `open_jira_projects` n'imprime plus le password (bug du legacy corrigé).
- `tls_verify` peut être passé à `false` mais ce n'est pas recommandé en dehors d'un contexte proxy d'entreprise.

## Modification dynamique

Quelques clés sont mutées en mémoire pendant la session via `config.set()` et **ne sont pas persistées** :

| Clé | Posée par |
|---|---|
| `default_organisation` | `select_organisation` |
| `project_key` | `select_jira_project` |

Au prochain redémarrage de Sublime, ces valeurs sont reperdues — c'est attendu.
