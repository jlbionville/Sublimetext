# AlfacoAtlassian

Pilotage des API REST Atlassian (Jira / Confluence) depuis Sublime Text.

## Commandes Sublime

| Commande | Effet |
|---|---|
| `select_organisation` | Choisit une organisation Atlassian dans la config runtime (popup). |
| `select_jira_project` | `GET /project/`, popup `KEY-Nom`, stocke la `project_key`. |
| `create_jira_issue` | POST le buffer JSON entier vers `…/issue/`, sauvegarde réponse + payload. |
| `init_json_jira` | Ouvre un buffer scratch + insère le snippet Jira pré-rempli (avec `project_key` courante). |
| `set_jira_project_in_snippet` | Remplace `"key": ""` par `"key": "<X>"` dans le buffer. |
| `open_jira_projects` | Affiche le login Jira en console (debug). |

## Configuration

Voir [../configuration.md](../configuration.md). Fichier : `User/alfaco-atlassian.sublime-settings`.

Clés requises pour le workflow Jira complet :

```json
{
    "jira_login": "votre.email@domaine.tld",
    "jira_password": "ATATT3xFfGF0…",
    "default_organisation": "votre-org",
    "api_rest_version": "3",
    "tls_verify": true,
    "path_json_files_folder": "/chemin/absolu/dossier/jira",
    "atlassian": {
        "organisations": {
            "Mon org": { "url_key": "votre-org", "jira": true, "confluence": true }
        }
    }
}
```

## Snippets

| Fichier | tabTrigger | Cible |
|---|---|---|
| `snippets/jira/jira.sublime-snippet` | `issue` | Payload Jira REST `POST /issue` (avec variables `${selection}`, `${description}`, `${duedate}`, `${jira_key}`). |
| `snippets/confluence/page.sublime-snippet` | `confluencepage` | Page Confluence (POST /content). |
| `snippets/confluence/childPage.sublime-snippet` | `childpage` | Page Confluence enfant (avec ancestors). |
| `snippets/confluence/space.sublime-snippet` | `confluencespace` | Création d'espace Confluence. |

## Macro

| Fichier | Effet |
|---|---|
| `macros/addjira.sublime-macro` | Sélectionne la ligne, insère snippet jira, ajoute `,\n` en fin de fichier. Lié à `F2` sous Linux. |

## Raccourcis clavier

| Touches | OS | Commande |
|---|---|---|
| `Ctrl+J` | Linux | `insert_snippet` (jira) |
| `F2` | Linux | `addjira` macro |
| `Ctrl+Alt+J` | Windows | `pretty_json` (package externe) |
| `Ctrl+J+L` | Windows | `select_jira_project` |
| `Super+N` | Windows | `init_json_jira` |
| `Ctrl+Alt+W` | Windows | snippet `{"fields": ...}` |
| `Alt+J` | Windows | `create_jira_issue` |

## Bugs corrigés depuis le legacy

| Bug | Statut |
|---|---|
| Login Jira codé en dur (`jlbionville@alfaco.fr`) | Résolu — lit `jira_login` |
| `setSetting("organisation", …)` mutait Preferences au démarrage | Résolu — `config.set()` runtime seul |
| `verify=False` codé en dur | Résolu — `tls_verify` configurable |
| Pas de timeout HTTP | Résolu — `(5, 30)` par défaut |
| `\\` Windows codés en dur dans paths | Résolu — `pathlib.Path` partout |
| `print(jira_password)` dans `OpenJiraProjectsCommand` | Résolu — masqué |
| Headers HTTP réécrits dans `create_jira_issue` | Résolu — préservés |

## Version

`0.2.0`.
