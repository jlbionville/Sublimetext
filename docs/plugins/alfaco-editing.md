# AlfacoEditing

## Présentation

Utilitaires d'édition divers, sans dépendance Atlassian :
- Duplication de sélection en fin de fichier (text-to-table).
- Marqueurs `<start>` / `<end>` pour borner un bloc et l'extraire.
- Insertion de tags arbitraires, suppression de tags listés.
- Insertion d'une date relative (`+N` jours).
- Manipulation de paramètres et d'inputs depuis la sélection.

## Prérequis

- `AlfacoLib` déployé (`make status`).

## Configuration

### Initialiser depuis le template

```bash
make init-config PLUGIN=AlfacoEditing
```

Copie [`plugins/AlfacoEditing/templates/User/alfaco-editing.sublime-settings`](../../plugins/AlfacoEditing/templates/User/alfaco-editing.sublime-settings) vers `<Packages>/User/alfaco-editing.sublime-settings`.

### Template inline

```jsonc
{
    // Délimiteur utilisé par modify_setting_from_selection et certains snippets.
    "alfaco_delimiter": "##"
}
```

### Référence des clés

| Clé | Type | Défaut | Rôle |
|---|---|---|---|
| `alfaco_delimiter` | string | `"##"` | Marqueur de bloc pour `modify_setting_from_selection`. Doit être unique dans les buffers où on l'utilise. |

## Utilisation

### Commandes

| Commande | Effet |
|---|---|
| `text_to_table` | Duplique la sélection (lignes non vides) en fin de fichier. |
| `select_between_markers` | Sélectionne le texte entre `<start>` et `<end>`, l'ajoute en fin de fichier. |
| `insert_tag` | Insère un tag arbitraire — argument `text`. |
| `remove_tag` | Supprime des tags listés — argument `text` séparé par `,`. |
| `date_selection` | Lit un nombre de jours dans la sélection, ouvre un buffer avec `##dt: <date+N>`. |
| `show_file_name` | Affiche le chemin du fichier ouvert en console. |
| `modify_setting_from_selection` | Stocke la sélection comme `alfaco_delimiter` (runtime). |
| `show_selected_input` | Ouvre un input panel pré-rempli avec la sélection. |

### Snippets

| TabTrigger | Cible |
|---|---|
| `alfacokey` | Squelette de keybinding Sublime (`{"keys": [], "command": ""}`). |

### Macro

`replace.sublime-macro` — squelette qui insère une tabulation. Démo de macro Sublime.

## Raccourcis

### Linux et Windows

| Touches | Commande |
|---|---|
| `Ctrl+Alt+T` | `text_to_table` |
| `Ctrl+Alt+S B` | `select_between_markers` |
| `Ctrl+Alt+T S` | `insert_tag <start>` |
| `Ctrl+Alt+T E` | `insert_tag <end>` |
| `Ctrl+Alt+D` | `remove_tag` |

### Windows uniquement

| Touches | Commande |
|---|---|
| `Ctrl+Alt+A` | `date_selection` |
| `Ctrl+Alt+M` | `modify_setting_from_selection` |

### macOS

`Ctrl+Super+T`, `Ctrl+Super+S B`, `Ctrl+Super+T S/E`, `Ctrl+Super+D` — équivalents des bindings Linux/Windows.

Voir [`plugins/AlfacoEditing/Default (*).sublime-keymap`](../../plugins/AlfacoEditing/) pour la liste exhaustive.

## Dépannage

| Erreur | Cause probable | Fix |
|---|---|---|
| `text_to_table` ne fait rien | Pas de sélection ou sélection sans ligne non-vide | Sélectionner au moins une ligne avec contenu. |
| `select_between_markers` retourne vide | Marqueurs `<start>` ou `<end>` absents | Insérer d'abord via `Ctrl+Alt+T S` puis `Ctrl+Alt+T E`. |
| `date_selection` plante | La sélection n'est pas un entier | Sélectionner uniquement le nombre de jours, sans espaces. |
| Plugin non chargé | Voir [troubleshooting.md](../troubleshooting.md) | — |

### Bugs corrigés depuis le legacy

| Bug | Statut |
|---|---|
| `ShowSelectedInputCommand` typo `nput_view` (NameError) | Résolu |

## Version

`0.2.0`.
