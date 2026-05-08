# AlfacoEditing

Utilitaires d'édition (sans dépendance Atlassian).

## Commandes Sublime

| Commande | Effet |
|---|---|
| `text_to_table` | Duplique la sélection (lignes non-vides) en fin de fichier. |
| `select_between_markers` | Sélectionne le texte entre `<start>` et `<end>`, l'ajoute en fin de fichier. |
| `insert_tag` | Insère un tag arbitraire (arg `text`). |
| `remove_tag` | Supprime des tags listés (arg `text`, séparés par `,`). |
| `date_selection` | Lit un nombre de jours dans la sélection, ouvre un buffer avec `##dt: <date+N>`. |
| `show_file_name` | Affiche le chemin du fichier ouvert en console. |
| `modify_setting_from_selection` | Stocke la sélection comme `alfaco_delimiter`. |
| `show_selected_input` | Ouvre une input panel — bug `nput_view` du legacy corrigé. |

## Snippet

`snippets/alfaco-key.sublime-snippet` (tabTrigger `alfacokey`) — squelette de keybinding Sublime.

## Macro

`macros/replace.sublime-macro` — squelette qui insère une tabulation.

## Raccourcis clavier

### Linux et Windows

| Touches | Commande |
|---|---|
| `Ctrl+Alt+T` | `text_to_table` |
| `Ctrl+Alt+S+B` | `select_between_markers` |
| `Ctrl+Alt+T+S` | `insert_tag <start>` |
| `Ctrl+Alt+T+E` | `insert_tag <end>` |
| `Ctrl+Alt+D` | `remove_tag` |

### Windows uniquement

| Touches | Commande |
|---|---|
| `Ctrl+Alt+A` | `date_selection` |
| `Ctrl+Alt+M` | `modify_setting_from_selection` |

### macOS

`Ctrl+Super+T`, `Ctrl+Super+S+B`, `Ctrl+Super+T+S/E`, `Ctrl+Super+D`.

## Configuration

`alfaco-editing.sublime-settings` :

```json
{
    "alfaco_delimiter": "##"
}
```

## Bugs corrigés

| Bug | Statut |
|---|---|
| `ShowSelectedInputCommand` typo `nput_view` (NameError) | Résolu |

## Version

`0.2.0`.
