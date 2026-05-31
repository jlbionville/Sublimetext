# Guide d'utilisation

Le détail par plugin est dans [plugins/](plugins/). Cette page consolide les workflows transverses et l'index des commandes.

## Workflow Jira typique (AlfacoAtlassian)

1. **Choisir l'organisation** — `Tools → Alfaco → Atlassian → Sélectionner organisation` ou palette `select_organisation`.
2. **Choisir le projet** — palette `select_jira_project` (ou `Ctrl+J+L` Windows).
3. **Initialiser un buffer JSON** — palette `init_json_jira` (ou `Super+N` Windows). Ouvre un scratch avec le snippet pré-rempli (`project_key` courante, `duedate` à J+10).
4. **Éditer le JSON** dans le buffer.
5. **POSTer** — palette `create_jira_issue` (ou `Alt+J` Windows). La réponse s'affiche dans un nouveau buffer, le payload est sauvegardé sous `<path_json_files_folder>/<KEY>.json`.

### Variante Markdown

Au lieu du buffer JSON (étapes 3-5), un flux Markdown est disponible (détails dans [plugins/alfaco-atlassian.md](plugins/alfaco-atlassian.md#workflow-markdown-alternatif-au-json)) :

1. **Initialiser** — palette `init_markdown_jira` (ou `Ctrl+Alt+M` Linux / `Cmd+Alt+M` macOS ; ⚠️ collision Windows, voir [troubleshooting.md](troubleshooting.md#conflit-de-raccourci-ctrlaltm-entre-plugins-windows)). Ouvre un scratch Markdown avec template pré-rempli (`project_key` courant + `duedate` à J+10).
   - *Alternative typée* : `select_jira_issue_type` (`Ctrl+J Ctrl+T`) propose les types du projet courant et ouvre le buffer avec `# Type` déjà rempli.
2. **Rédiger** — corps en Markdown (headings, listes, **emphase**, `code`, liens, blocs de code). Champs réservés via `# Summary`, `# Organisation` (site Atlassian, prioritaire sur `default_organisation`), `# Project`, `# Type`, `# Priority`, `# Labels`, `# Parent` (Epic/Story de rattachement, optionnel), `# Startdate` (date du jour, optionnelle → `customfield_10015`), `# Duedate`, `# Description`.
   - *Rattacher à un parent* : `select_jira_parent` (`Ctrl+J Ctrl+R`) propose les Epics/Stories du projet et remplit `# Parent` ; à défaut, saisir la clé à la main sous `# Parent`.
3. **POSTer** — palette `create_jira_from_markdown` (ou `Alt+M` Linux/Windows / `Cmd+Shift+M` macOS). Le corps est converti en ADF puis envoyé.

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

`select_organisation`, `select_jira_project`, `create_jira_issue`, `init_json_jira`, `init_markdown_jira`, `create_jira_from_markdown`, `insert_current_project`, `insert_current_organisation`, `select_jira_issue_type`, `set_jira_project_in_snippet`, `open_jira_projects`.

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
- Initialiser Markdown Jira
- Créer ticket Jira (depuis Markdown)
- Open Jira projects (debug)

### Clic droit éditeur

- AlfacoAtlassian : format JSON, créer ticket Jira (JSON et depuis Markdown), init Markdown Jira, sélectionner projet/organisation.

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
