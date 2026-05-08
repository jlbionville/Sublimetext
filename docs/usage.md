# Guide d'utilisation

Le détail par plugin est dans [plugins/](plugins/). Cette page consolide les workflows transverses et l'index des commandes.

## Workflow Jira typique (AlfacoAtlassian)

1. **Choisir l'organisation** — `Tools → Alfaco → Atlassian → Sélectionner organisation` ou palette `select_organisation`.
2. **Choisir le projet** — palette `select_jira_project` (ou `Ctrl+J+L` Windows).
3. **Initialiser un buffer JSON** — palette `init_json_jira` (ou `Super+N` Windows). Ouvre un scratch avec le snippet pré-rempli (`project_key` courante, `duedate` à J+10).
4. **Éditer le JSON** dans le buffer.
5. **POSTer** — palette `create_jira_issue` (ou `Alt+J` Windows). La réponse s'affiche dans un nouveau buffer, le payload est sauvegardé sous `<path_json_files_folder>/<KEY>.json`.

## Workflow d'édition (AlfacoEditing)

Détails dans [plugins/alfaco-editing.md](plugins/alfaco-editing.md).

| Action | Comment |
|---|---|
| Dupliquer une sélection en fin de fichier | sélectionner + `Ctrl+Alt+T` |
| Marquer un bloc avec `<start>`/`<end>` | `Ctrl+Alt+T+S` puis `Ctrl+Alt+T+E` |
| Sélectionner le texte entre marqueurs | `Ctrl+Alt+S+B` |
| Supprimer les marqueurs | `Ctrl+Alt+D` |
| Insérer une date relative | sélectionner un nombre de jours + `Ctrl+Alt+A` (Windows) |

## Index des commandes

### AlfacoAtlassian

`select_organisation`, `select_jira_project`, `create_jira_issue`, `init_json_jira`, `set_jira_project_in_snippet`, `open_jira_projects`.

### AlfacoEditing

`text_to_table`, `select_between_markers`, `insert_tag`, `remove_tag`, `date_selection`, `show_file_name`, `modify_setting_from_selection`, `show_selected_input`.

### AlfacoCompletion

`AlfacoCompletion` (EventListener — pas de commande directement invocable).

## Menus

### `Tools → Alfaco → Atlassian` (AlfacoAtlassian)

- Sélectionner organisation
- Sélectionner projet Jira
- Créer ticket Jira
- Initialiser JSON Jira
- Open Jira projects (debug)

### Clic droit éditeur

- AlfacoAtlassian : format JSON, créer ticket Jira, sélectionner projet/organisation.

### Clic droit sidebar

- AlfacoAtlassian : format JSON, open jira projects.

### Palette de commandes

- AlfacoEditing : `text to table`, `show file name`, `select between markers`.
- (AlfacoAtlassian commandes accessibles aussi via leur snake_case Sublime.)

## Snippets

Tous les snippets sont accessibles via leur tabTrigger (saisir le mot puis `Tab`) :

- `issue` → payload Jira (AlfacoAtlassian).
- `confluencepage` → page Confluence.
- `childpage` → page Confluence enfant.
- `confluencespace` → espace Confluence.
- `alfacokey` → squelette de keybinding (AlfacoEditing).
