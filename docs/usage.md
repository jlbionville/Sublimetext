# Guide d'utilisation

## Workflow Jira typique

L'objectif principal du plugin est de **créer des tickets Jira depuis Sublime Text** en POSTant un payload JSON édité dans le buffer actif.

### Étapes

1. **Choisir l'organisation Atlassian** : `Tools → Alfaco → Jira → Select Organisation`
   → Une popup liste les organisations définies dans `alfaco-atlassian.sublime-settings`. Le choix met à jour `default_organisation` dans la `Configuration`.

2. **Choisir le projet Jira** : `Tools → Alfaco → Jira → Select Jira project` (ou `ctrl+j+l` sous Windows)
   → Le plugin appelle `GET https://{org}.atlassian.net/rest/api/{version}/project/`, affiche la liste `KEY-Nom` et stocke la clé du projet sélectionné dans `Configuration.project_key`.

3. **Initialiser un fichier JSON pré-rempli** : `super+n` (Windows) ou via la commande `init_json_jira`
   → Ouvre un nouveau buffer scratch « Init new Jira », injecte le snippet `snippets/jira/jira.sublime-snippet`, pré-remplit `summary` (depuis la ligne courante), `duedate` (J+10), `jira_key` (clé projet sélectionnée), `description`.

4. **Éditer le JSON** (ajuster summary, description, labels, priority, assignee…). Voir [Snippets](#snippets) pour les modèles disponibles.

5. **Envoyer le ticket** : `alt+j` (Windows) ou commande `appel_rest_api`
   → POST le contenu intégral du buffer vers `…/rest/api/{version}/issue/`. La réponse s'affiche dans un nouveau buffer.
   → En parallèle, le plugin **sauvegarde deux fichiers** dans `path_json_files_folder` :
     - `error_api_call_<timestamp>.html` : la réponse brute (utile en cas d'erreur).
     - `<JIRA_KEY>.json` : le payload qui a été envoyé (rejouable).

> **Pré-requis** : `path_json_files_folder` doit pointer vers un dossier existant — sinon l'écriture échoue **après** que le ticket a été créé côté Jira.

## Référence des commandes

Les commandes ci-dessous sont enregistrées par les classes de `AlfacoPlugins.py` (sauf `text_to_table` défini dans `text_to_table.py`). Le nom interne (snake_case) est utilisable depuis la palette de commandes ou un keybinding.

### Commandes Jira / Atlassian

| Commande | Classe | Effet |
|---|---|---|
| `get_list_organisation` | `GetListOrganisationCommand` | Affiche les organisations de `alfaco-atlassian.sublime-settings`, stocke la `url_key` choisie. |
| `get_jira_list_for_organisation` | `GetJiraListForOrganisationCommand` | `GET /project/`, popup `KEY-Nom`, stocke la clé projet. |
| `open_jira_projects` | `OpenJiraProjectsCommand` | Affiche `jira_password` et `jira_login` dans la console (debug — ne **pas** utiliser en démo). |
| `appel_rest_api` | `AppelRestApiCommand` | POST le buffer entier vers `…/issue/`, affiche la réponse, sauvegarde réponse + payload. |
| `set_jira_project_in_snippet` | `SetJiraProjectInSnippetCommand` | Remplace `"key": ""` par `"key": "<args.text>"` dans le buffer (utilitaire pour scripter). |
| `init_json_jira` | `InitJsonJiraCommand` | Ouvre un buffer scratch et y insère le snippet Jira pré-rempli. |

### Commandes d'édition

| Commande | Classe | Effet | Raccourci |
|---|---|---|---|
| `text_to_table` | `TextToTableCommand` | Ajoute une copie de la sélection (lignes non vides) à la fin du fichier. | `ctrl+alt+t` (Win/Linux), `ctrl+super+t` (macOS) |
| `select_between_markers` | `SelectBetweenMarkersCommand` | Sélectionne le texte entre `<start>` et `<end>`, l'ajoute à la fin du document. | `ctrl+alt+s+b` (Win/Linux), `ctrl+super+s+b` (macOS) |
| `insert_tag` | `InsertTagCommand` | Insère un tag (`<start>` / `<end>` / autre) à la position du curseur. | `ctrl+alt+t+s` / `ctrl+alt+t+e` |
| `remove_tag` | `RemoveTagCommand` | Supprime toutes les occurrences des tags listés dans `args.text` (séparés par `,`). | `ctrl+alt+d` |
| `date_selection` | `DateSelectionCommand` | Lit un nombre de jours dans la sélection, ouvre un nouveau buffer avec `##dt: <date+N>`. | `ctrl+alt+a` (Windows) |
| `donne_nom_fichier` | `DonneNomFichierCommand` | Affiche dans la console le chemin du fichier ouvert. | — |
| `modify_setting_from_selection` | `ModifySettingFromSelectionCommand` | Stocke la sélection dans `alfaco_delimiter` puis l'insère à la position du curseur. | `ctrl+alt+m` (Windows) |
| `show_selected_input` | `ShowSelectedInputCommand` | Ouvre une input panel « Example ». **Bug connu** — voir [troubleshooting.md](troubleshooting.md#bug-show_selected_input). | — |

### Commandes Sublime utilisées (non définies par le plugin)

- `pretty_json` (du package « Pretty JSON ») — utilisé par les menus et la keymap Windows (`ctrl+alt+j`).
- `insert_snippet`, `insert`, `expand_selection`, `move_to`, `run_macro_file` — natifs Sublime.

## Raccourcis clavier

Les keymaps **divergent** entre les trois OS. La table suivante consolide tout ce qui est défini :

| Touches | Commande | Linux | Windows | macOS |
|---|---|:-:|:-:|:-:|
| `ctrl+alt+t` | `text_to_table` | ✓ | ✓ | — |
| `ctrl+super+t` | `text_to_table` | — | — | ✓ |
| `ctrl+alt+s+b` | `select_between_markers` | ✓ | ✓ | — |
| `ctrl+super+s+b` | `select_between_markers` | — | — | ✓ |
| `ctrl+alt+t+s` | `insert_tag <start>` | ✓ | ✓ | — |
| `ctrl+super+t+s` | `insert_tag <start>` | — | — | ✓ |
| `ctrl+alt+t+e` | `insert_tag <end>` | ✓ | ✓ | — |
| `ctrl+super+t+e` | `insert_tag <end>` | — | — | ✓ |
| `ctrl+alt+d` | `remove_tag` | ✓ | ✓ | — |
| `ctrl+super+d` | `remove_tag` | — | — | ✓ |
| `ctrl+j` | `insert_snippet` (User/jira) | ✓ | — | — |
| `f2` | `run_macro_file` (addjira) | ✓ | — | — |
| `ctrl+alt+j` | `pretty_json` | — | ✓ | — |
| `ctrl+alt+a` | `date_selection` | — | ✓ | — |
| `ctrl+alt+m` | `modify_setting_from_selection` | — | ✓ | — |
| `ctrl+j+l` | `get_jira_list_for_organisation` | — | ✓ | — |
| `ctrl+alt+i` | `insert` (snippet keybinding) | — | ✓ | — |
| `super+n` | `init_json_jira` | — | ✓ | — |
| `ctrl+alt+w` | `insert_snippet` (`{"fields": ...}`) | — | ✓ | — |
| `alt+j` | `appel_rest_api` | — | ✓ | — |

> **Quand on ajoute un binding, mettre à jour les trois fichiers** `Default (Linux|Windows|OSX).sublime-keymap` pour rester cohérent.

## Menus

### Menu principal — `Tools → Alfaco → Jira` (`Main.sublime-menu`)

- `open list projects` → `open_jira_projects`

### Menu principal — `Preferences → Package Settings → Alfaco`

- `Settings – Default` → ouvre `Packages/Alfaco/alfaco.sublime-settings`
- `Settings – User` → ouvre `Packages/User/alfaco.sublime-settings`

### Menu contextuel (`Context.sublime-menu`)

- **Alfaco**
  - `format json` → `pretty_json`
  - `call rest api` → `appel_rest_api`
- **Jira**
  - `Select Jira project` → `get_jira_list_for_organisation`
  - `create jira` → `appel_rest_api`
  - `Select Organisation` → `get_list_organisation`

### Menu de la barre latérale (`Side Bar.sublime-menu`)

- **Alfaco**
  - `format json` → `pretty_json`
  - `default jira` → `open_jira_projects`

### Palette de commandes (`Default.sublime-commands`)

- `alfaco command` → `text_to_table`

## Snippets

Les snippets sont accessibles via leur **tabTrigger** (saisir le mot puis `Tab`) ou via `insert_snippet` programmatique.

| Fichier | tabTrigger | Cible | Notes |
|---|---|---|---|
| `snippets/jira/jira.sublime-snippet` | `issue` | Payload Jira REST `POST /issue` | Utilise les variables `${selection}`, `${description}`, `${duedate}`, `${jira_key}` injectées par `init_json_jira`. |
| `snippets/jira.sublime-snippet` | `issue` | Variante plus ancienne, avec `duedate` codée en dur (`2022-02-23`). | À ne plus utiliser — préférer `snippets/jira/jira.sublime-snippet`. |
| `snippets/confluence/page.sublime-snippet` | `confluencepage` | Payload Confluence `POST /content` (page racine). | |
| `snippets/confluence/childPage.sublime-snippet` | `childpage` | Page Confluence enfant (avec `ancestors`). | |
| `snippets/confluence/space.sublime-snippet` | `confluencespace` | Création d'espace Confluence. | |
| `snippets/page.sublime-snippet`, `snippets/childPage.sublime-snippet`, `snippets/space.sublime-snippet` | idem | Doublons des fichiers ci-dessus, conservés à la racine `snippets/`. | À fusionner — voir [troubleshooting.md](troubleshooting.md#snippets-en-double). |
| `snippets/alfaco-key.sublime-snippet` | `alfacokey` | Squelette de keybinding Sublime. | |

## Macros

| Fichier | Description |
|---|---|
| `macros/addjira.sublime-macro` | Sélectionne la ligne, insère le snippet `User/jira.sublime-snippet`, va en fin de fichier, ajoute `,\n`. Utilisé pour empiler des issues dans un fichier `bulk`. Lié à `f2` sous Linux. |
| `macros/replace.sublime-macro` | Insère une tabulation (deux lignes — squelette à compléter). |
