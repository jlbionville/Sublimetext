# AlfacoCompletion

Auto-complétion statique (`def`, `class`, `None`, `True`, `False`) en scope `source.python`.

`EventListener` simple — squelette de démonstration plus qu'utilité réelle (Sublime fournit déjà ces complétions natives).

## Comportement

À chaque frappe dans un buffer Python (`source.python`), Sublime appelle `on_query_completions`. La classe filtre la liste statique par préfixe (case-insensitive) et la retourne au menu de complétion.

## Configuration

Aucune.

## Version

`0.2.0`.
