# AlfacoAtlassian

## Présentation

Pilotage des API REST Atlassian (Jira / Confluence) depuis Sublime Text :
- Sélection interactive de l'organisation et du projet Jira.
- Initialisation d'un buffer JSON pré-rempli (snippet `issue`).
- Création d'un ticket via `POST /issue` à partir du buffer courant.
- Snippets Confluence (page, sous-page, espace).

Le plugin s'appuie sur `AlfacoLib` pour la configuration, l'auth Basic, l'appel HTTP et les chemins de sauvegarde.

## Prérequis

- `AlfacoLib` déployé (`make status` doit afficher `link` ou `copy`).
- Un compte Atlassian Cloud avec un **token API** :
  https://id.atlassian.com/manage-profile/security/api-tokens
  ⚠️ Le token API n'est **pas** le mot de passe du compte.
- Un dossier writable sur disque pour archiver payloads et réponses (clé `path_json_files_folder`).

## Configuration

### Initialiser depuis le template

```bash
make init-config PLUGIN=AlfacoAtlassian
```

Copie [`plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings`](../../plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings) vers `<Packages>/User/alfaco-atlassian.sublime-settings`. La cible **n'écrase pas** un fichier existant — relancer avec `make init-config-force` pour forcer.

Ensuite : `Preferences → Package Settings → AlfacoAtlassian → Settings – User`, remplir les valeurs.

### Template inline

```jsonc
{
    "jira_login": "votre.email@domaine.tld",
    "jira_password": "ATATT3xFfGF0…",            // token API, PAS le mdp
    "default_organisation": "votre-org",
    "api_rest_version": "3",                       // "2" ou "3"
    "tls_verify": true,                            // false uniquement derrière proxy d'entreprise
    "path_json_files_folder": "/chemin/dossier/jira",
    "atlassian": {
        "organisations": {
            "Mon org": { "url_key": "votre-org", "jira": true, "confluence": true }
        }
    },
    "debug": false
}
```

### Référence des clés

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `jira_login` | string | `""` | Email du compte Atlassian. |
| `jira_password` | string | `""` | Token API Atlassian. |
| `default_organisation` | string | `""` | `url_key` initial. Modifié en runtime par `select_organisation`. |
| `jira_startdate_field` | string | `"customfield_10015"` | Custom field Jira pour Start date (varie selon l'instance ; vide = désactivé). |
| `jira_parent_types` | array | `["Epic", "Story"]` | Types d'issues proposés par `select_jira_parent` comme parent possible. |
| `api_rest_version` | string | `"3"` | `"2"` ou `"3"`. v3 attend descriptions au format ADF. |
| `tls_verify` | bool | `true` | Vérification du certificat TLS. |
| `path_json_files_folder` | string | `""` | Dossier de sauvegarde — vide = pas de sauvegarde. |
| `headers` | object | `{Content-type: application/json, Accept: application/json}` | Headers HTTP. |
| `atlassian.organisations` | object | (catalogue exemple) | Organisations affichées par `select_organisation`. |
| `debug` | bool | `false` | Active les logs `debug`/`info`. |

### Clés mutées en runtime (non persistées)

| Clé | Posée par |
|---|---|
| `default_organisation` | `select_organisation` |
| `project_key` | `select_jira_project` |

Au redémarrage, ces valeurs reviennent à celles du fichier — c'est attendu.

## Utilisation

### Workflow Jira

1. **Sélectionner l'organisation** : `Tools → Alfaco → Atlassian → Sélectionner organisation`, ou commande palette `select_organisation`.
2. **Sélectionner le projet** : `select_jira_project` (popup `KEY-Nom`). Linux `Ctrl+J L` / Windows `Ctrl+J L`.
3. **Initialiser un buffer JSON** : `init_json_jira` (Windows `Super+N`). Ouvre un buffer scratch avec le snippet `issue` pré-rempli (`project.key` courante, `duedate` à J+10).
4. **Éditer le payload** dans le buffer.
5. **POST** : `create_jira_issue` (Windows `Alt+J`). La réponse s'ouvre dans un nouveau buffer ; le payload et la réponse sont archivés sous `<path_json_files_folder>/<KEY>.json` et `<KEY>_response_<timestamp>.json`.

### Workflow Confluence

Pas de commande dédiée à la création — utiliser les snippets via tabTrigger dans un buffer JSON, puis envoyer manuellement (cURL/Postman) ou réutiliser `create_jira_issue` après avoir adapté l'URL.

### Commandes

| Commande | Effet |
|---|---|
| `select_organisation` | Popup d'organisations (catalogue `atlassian.organisations`). |
| `select_jira_project` | `GET /project/`, popup `KEY-Nom`, stocke `project_key`. |
| `create_jira_issue` | `POST` du buffer JSON vers `/issue/`, sauvegarde réponse + payload. |
| `init_json_jira` | Buffer scratch avec snippet `issue` pré-rempli. |
| `set_jira_project_in_snippet` | Remplace `"key": ""` par `"key": "<courant>"` dans le buffer. |
| `insert_current_project` | Insère le `project_key` courant au curseur (rien + message si non défini). |
| `insert_current_organisation` | Insère l'organisation courante (`default_organisation`) au curseur. |
| `select_jira_issue_type` | Popup des types d'issues du projet courant (`GET /project/{KEY}?expand=issueTypes`, noms dédupliqués) ; à la sélection, ouvre un buffer Markdown pré-rempli avec ce type. |
| `select_jira_parent` | Popup des parents (Epic/Story par défaut, cf. `jira_parent_types`) du projet courant (`search` JQL) ; à la sélection, remplit la section `# Parent` du buffer Markdown. |
| `open_jira_projects` | Affiche le `jira_login` en console (debug). |

### Snippets

| TabTrigger | Cible |
|---|---|
| `issue` | Payload Jira `POST /issue` (avec variables `${selection}`, `${description}`, `${duedate}`, `${jira_key}`). |
| `confluencepage` | Création de page Confluence. |
| `childpage` | Page Confluence enfant (avec `ancestors`). |
| `confluencespace` | Création d'espace Confluence. |

### Macro

`addjira.sublime-macro` (Linux `F2`) — sélectionne la ligne, insère le snippet `jira`, ajoute `,\n` en fin de fichier.

## Workflow Markdown (alternatif au JSON)

Depuis la v0.5.0, un second flux permet de créer un ticket depuis un buffer Markdown au lieu d'un buffer JSON.

`Ctrl+M` (Linux/Win) / `Cmd+M` (Mac) — **uniquement dans un buffer Markdown** (sinon `Ctrl+M` garde son rôle natif « aller au crochet ») — ou via `Tools → Alfaco → Atlassian → Initialiser Markdown Jira` → ouvre un buffer Markdown scratch avec le template (project_key courant + dates auto). Tab navigue summary → description. Une fois rempli, `Alt+M` (Linux/Win) / `Cmd+Shift+M` (Mac) parse, convertit le corps Markdown en ADF (paragraphes, headings, listes, **emphase**, `code`, [liens](url), code blocks) et POST.

Champs réservés : `Summary`, `Organisation`, `Project`, `Type`, `Priority`, `Labels`, `Parent`, `Startdate`, `Duedate`, `Description`. Un `# UnknownField` produit une erreur explicite. `# Parent` (optionnel) rattache l'issue créée à une Epic ou une Story : la clé saisie est envoyée comme `parent` (`{"key": "<KEY>"}`). La commande `select_jira_parent` (`Ctrl+J Ctrl+R`) propose les Epics/Stories du projet et remplit ce champ. `Summary` et `Description` sont obligatoires ; les autres ont des fallbacks (`project_key` courant, today + 10 jours, etc.). `# Organisation` (= `url_key` du site Atlassian) ne fait pas partie du payload : il **route** le POST et l'emporte sur `default_organisation`. `# Startdate` (date du jour pré-remplie, optionnelle) est envoyée sur le custom field `jira_startdate_field` (défaut `customfield_10015`) ; vide ou réglage désactivé → champ non envoyé.

Détails et limites du parser : voir [`plugins/AlfacoLib/markdown_to_adf.py`](../../plugins/AlfacoLib/markdown_to_adf.py) (non supporté MVP : tables, images, blockquotes, listes imbriquées, strikethrough → texte brut).

## Raccourcis

| Touches | OS | Commande |
|---|---|---|
| `Ctrl+Shift+J` | Linux / Windows | `init_json_jira` — nouveau buffer avec snippet `jira` pré-rempli (duedate, project_key) |
| `Cmd+Shift+J` | macOS | `init_json_jira` (idem) |
| `Ctrl+M` | Linux / Windows | `init_markdown_jira` — **contexte Markdown uniquement** (préserve `move_to brackets` ailleurs) |
| `Cmd+M` | macOS | `init_markdown_jira` (contexte Markdown) |
| `Alt+M` | Linux / Windows | `create_jira_from_markdown` — parse + POST |
| `Cmd+Shift+M` | macOS | `create_jira_from_markdown` (idem) |
| `Ctrl+J Ctrl+O` / `Cmd+J Cmd+O` | tous | `select_organisation` (popup choix organisation) |
| `Ctrl+J Ctrl+P` / `Cmd+J Cmd+P` | tous | `select_jira_project` (popup choix projet, basé sur l'org courante) |
| `Ctrl+J O` / `Cmd+J O` | tous | `insert_current_organisation` (insère l'org courante au curseur) |
| `Ctrl+J P` / `Cmd+J P` | tous | `insert_current_project` (insère le projet courant au curseur) |
| `Ctrl+J Ctrl+T` / `Cmd+J Cmd+T` | tous | `select_jira_issue_type` (popup des types du projet, ouvre le buffer Markdown) |
| `Ctrl+J Ctrl+R` / `Cmd+J Cmd+R` | tous | `select_jira_parent` (popup Epic/Story, remplit `# Parent`) |
| `F2` | Linux | macro `addjira` — insère le snippet inline dans le buffer courant (sans dates) |
| `Ctrl+Alt+W` | Windows | snippet `{"fields": ...}` wrapper |
| `Alt+J` | Windows | `create_jira_issue` |
| `Ctrl+Alt+J` | Windows | `pretty_json` (package externe) |

Mnémo des chords `Ctrl+J` : **avec** `Ctrl` sur la 2ᵉ touche = « choisir » (popup), **sans** = « insérer » la valeur courante.

**Navigation dans le snippet** (après `Ctrl+Shift+J` ou tabTrigger `issue`+Tab) : `Tab` saute entre `summary` puis `description` ; sortie par `Esc` ou `$0` (après l'accolade fermante). Les autres champs (`duedate`, `jira_key`) sont remplis automatiquement par `init_json_jira` ; `labels` est préfixé `["important", "urgent"]`.

Voir aussi [`plugins/AlfacoAtlassian/Default (*).sublime-keymap`](../../plugins/AlfacoAtlassian/) pour la liste exhaustive (Linux / Windows / OSX).

## Dépannage

| Erreur | Cause probable | Voir |
|---|---|---|
| `401 Unauthorized` | `jira_login` absent ou token expiré | [troubleshooting.md](../troubleshooting.md#diagnostic-des-erreurs-atlassian) |
| `404` sur `/issue/` | Mauvais `api_rest_version` ou format de description | troubleshooting.md |
| `400 Bad Request` à la création | `project.key` absent, `issuetype.name` mauvaise langue, payload non encapsulé `{"fields": {...}}` | troubleshooting.md |
| `ModuleNotFoundError: requests` | Déploiement obsolète (le code utilise désormais `urllib`) — `make uninstall && make install` | [troubleshooting.md](../troubleshooting.md) |
| Plugins supprimés au démarrage | Package Control les considère orphelins | [installation.md](../installation.md#cohabitation-avec-package-control) |

### Bugs corrigés depuis le legacy

| Bug | Statut |
|---|---|
| Login Jira codé en dur | Résolu — lit `jira_login` |
| `setSetting("organisation", …)` mutait `Preferences` au démarrage | Résolu — `config.set()` runtime |
| `verify=False` codé en dur | Résolu — `tls_verify` configurable |
| Pas de timeout HTTP | Résolu — `(5, 30)` par défaut |
| `\\` Windows codés en dur | Résolu — `pathlib.Path` |
| `print(jira_password)` console | Résolu — masqué |
| Headers HTTP réécrits dans `create_jira_issue` | Résolu — préservés |
| Dépendance `requests` (non livré par ST4) | Résolu — `atlassian_client` réécrit avec `urllib` stdlib |

## Version

`0.2.0`.
