# Configuration

## Résolution des settings

Chaque plugin lit ses propres `.sublime-settings`. La résolution est gérée par `AlfacoLib.config.Configuration` :

1. **Runtime** (`config.set()` en mémoire — perdu au redémarrage).
2. **Settings layers** passés au constructeur, dans l'ordre.
3. **Default** explicite passé à `get(key, default=...)`.

## Initialisation depuis les templates

Chaque plugin qui a une config livre un template sous `plugins/<X>/templates/User/<setting>.sublime-settings`. La cible Makefile `init-config` les copie vers `<Packages>/User/` :

```bash
make init-config                          # tous les plugins
make init-config PLUGIN=AlfacoAtlassian   # un seul
make init-config-force                    # écrase un fichier existant
```

`init-config` **ne remplace pas** un fichier déjà présent — utile pour relancer sans craindre d'effacer une config remplie. Sortie typique :

```
  [copied ] AlfacoAtlassian: alfaco-atlassian.sublime-settings
  [skipped] AlfacoEditing: alfaco-editing.sublime-settings
init-config : 1 copié(s), 1 ignoré(s) (déjà présent — utiliser --force pour écraser).
```

## Plugins avec configuration

| Plugin | Fichier User | Template |
|---|---|---|
| AlfacoAtlassian | `<Packages>/User/alfaco-atlassian.sublime-settings` | [`plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings`](../plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings) |
| AlfacoEditing | `<Packages>/User/alfaco-editing.sublime-settings` | [`plugins/AlfacoEditing/templates/User/alfaco-editing.sublime-settings`](../plugins/AlfacoEditing/templates/User/alfaco-editing.sublime-settings) |
| AlfacoLib | — | aucune config |
| AlfacoCompletion | — | aucune config |

## `AlfacoAtlassian/alfaco-atlassian.sublime-settings`

Référence complète des clés dans [plugins/alfaco-atlassian.md](plugins/alfaco-atlassian.md#configuration). Résumé :

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `jira_login` | string | `""` | Email du compte Atlassian. |
| `jira_password` | string | `""` | **Token API** (pas le mot de passe du compte). |
| `default_organisation` | string | `""` | URL key de `https://<X>.atlassian.net/`. Mutée en runtime par `select_organisation`. |
| `api_rest_version` | string | `"3"` | `"2"` ou `"3"`. |
| `tls_verify` | bool | `true` | Désactiver derrière proxy d'entreprise. |
| `path_json_files_folder` | string | `""` | Dossier de sauvegarde des payloads/réponses. Doit exister. |
| `headers` | object | `{Content-type: application/json, Accept: application/json}` | Headers HTTP par défaut. |
| `atlassian.organisations` | object | (catalogue exemple) | Catalogue pour le popup `select_organisation`. |
| `debug` | bool | `false` | Active les logs `debug`/`info` du logger. |

## `AlfacoEditing/alfaco-editing.sublime-settings`

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `alfaco_delimiter` | string | `"##"` | Délimiteur utilisé par `modify_setting_from_selection`. |

## `AlfacoLib` et `AlfacoCompletion`

Aucun settings dédié.

## Modification dynamique (runtime, non persistée)

| Clé | Plugin | Posée par |
|---|---|---|
| `default_organisation` | AlfacoAtlassian | `select_organisation` |
| `project_key` | AlfacoAtlassian | `select_jira_project` |
| `alfaco_delimiter` | AlfacoEditing | `modify_setting_from_selection` |

Au redémarrage de Sublime, ces valeurs reviennent à celles du fichier — c'est attendu.

## Sécurité

- **Ne JAMAIS commiter `User/alfaco-atlassian.sublime-settings`** contenant un vrai token. Par défaut, Sublime stocke `User/` hors du dépôt (dans `<Packages>/User/`), donc pas de risque automatique. Si vous gérez `User/` en dotfiles, ajouter `alfaco-atlassian.sublime-settings` à votre `.gitignore` perso.
- Les templates versionnés (`plugins/<X>/templates/User/*`) ne contiennent **que des placeholders** — jamais de vrai secret.
- Le token est stocké en clair côté Sublime. Pour un usage en équipe, envisager :
  - Variable d'environnement lue dans `plugin_loaded()`.
  - Gestionnaire de secrets (1Password CLI, `pass`, `keyring`).
- `open_jira_projects` n'imprime plus le password (bug du legacy corrigé).
- `tls_verify=false` n'est recommandé qu'en contexte proxy d'entreprise qui ré-émet les certificats.
