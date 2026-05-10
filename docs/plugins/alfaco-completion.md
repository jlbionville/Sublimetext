# AlfacoCompletion

## Présentation

Auto-complétion statique pour le scope `source.python` : `def`, `class`, `None`, `True`, `False`.

⚠️ **Démo plus que vraie utilité** — Sublime Text fournit déjà ces complétions via son scope par défaut. Le plugin sert surtout d'exemple minimaliste d'`EventListener` dans le monorepo.

## Prérequis

- `AlfacoLib` déployé.

## Configuration

Aucune. Pas de `.sublime-settings`, pas de template.

## Utilisation

Aucune commande utilisateur. À chaque frappe dans un buffer Python, Sublime appelle `on_query_completions` ; la classe filtre la liste statique par préfixe (case-insensitive) et la retourne au menu de complétion natif.

Exemple :
- Taper `de` dans un buffer `.py` → `def` apparaît dans le menu.
- Taper `cl` → `class`.
- Taper `Tr` → `True`.

## Raccourcis

Aucun. Le déclenchement passe par le menu de complétion Sublime (`Ctrl+Space` ou auto-complétion à la frappe).

## Dépannage

| Erreur | Cause probable | Fix |
|---|---|---|
| Les complétions n'apparaissent pas | Plugin non chargé ou scope autre que `source.python` | `make status` ; vérifier le scope avec `Ctrl+Alt+Shift+P`. |
| Doublons avec les complétions natives | Comportement attendu — voir « Présentation » | Désactiver le plugin si gênant : ajouter `"AlfacoCompletion"` à `ignored_packages`. |

## Version

`0.2.0`.
