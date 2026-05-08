# Déploiement

## Cibles Makefile

| Cible | Effet |
|---|---|
| `make link` | Symlinks `plugins/*` → `<Packages>/`. Mode dev : modifications immédiates. |
| `make install` | Copie `plugins/*` → `<Packages>/`. Mode utilisateur. |
| `make uninstall` | Supprime `<Packages>/Alfaco*`. |
| `make relink` | uninstall + link. |
| `make status` | État de chaque plugin (link/copy/absent). |
| `make new-plugin NAME=X` | Scaffold `plugins/AlfacoX/`. |
| `make test` | pytest sur `plugins/*/tests/`. |
| `make clean` | Nettoyage `__pycache__`, `.pytest_cache`. |

Variable `PLUGIN=AlfacoEditing` pour cibler un plugin spécifique : `make link PLUGIN=AlfacoEditing`.

## Détection multi-OS du dossier Packages/

Voir `tools/deploy.py:detect_packages_dir`. Override possible :

- Variable d'environnement : `SUBLIME_PACKAGES_DIR=/chemin/absolu`.
- Flag CLI : `python tools/deploy.py link --packages-dir /chemin/absolu`.

| OS / Contexte | Chemin |
|---|---|
| Linux ST4 | `~/.config/sublime-text/Packages/` (ou `$XDG_CONFIG_HOME`) |
| Linux ST3 | `~/.config/sublime-text-3/Packages/` |
| macOS | `~/Library/Application Support/Sublime Text/Packages/` |
| Windows | `%APPDATA%\Sublime Text\Packages\` |
| WSL → Sublime hôte Windows | `/mnt/c/Users/<user>/AppData/Roaming/Sublime Text/Packages/` |

## WSL : `make link` force `make install`

Sous WSL, `link` détecte l'environnement et force la copie : NTFS ne suit pas les symlinks WSL. Un message s'affiche :

```
WSL détecté → mode 'install' (copie) forcé : NTFS ne suit pas les symlinks WSL.
```

### Username Windows ≠ username WSL

`tools/deploy.py` interroge `cmd.exe /c echo %USERNAME%` pour récupérer le nom Windows réel (cas fréquent : `$USER=ubuntu` côté WSL mais `Jean` côté Windows). Si `cmd.exe` n'est pas accessible, fallback sur `$USER` puis `$USERNAME`. Si le profil `/mnt/c/Users/<user>/` n'existe pas, le déploiement lève une erreur claire pointant vers `SUBLIME_PACKAGES_DIR`.

## Windows natif

`os.symlink` est tenté en premier ; en cas d'échec (Developer Mode désactivé, pas de privilège), fallback sur `mklink /J` (junction NTFS). Aucun privilège admin requis.

> Limitation connue : sur Windows, `make status` reportera une junction comme `copy` (Python `<3.12` ne reconnaît pas les junctions comme symlinks). Cosmétique.

## Détection des plugins

`_iter_plugins` lit `plugins/*/` et garde uniquement les sous-dossiers (filtre `is_dir() and not name.startswith(".")`). Les `tests/`, `__pycache__/`, `.pytest_cache/`, `.git/` et `*.pyc` sont **exclus** au moment du `link`/`install`.

## Dépendance d'inter-package

`AlfacoLib` doit être déployé avant les autres plugins. Le `make link` les déploie tous d'un coup en ordre alphabétique — `AlfacoLib` arrive en dernier, mais Sublime charge les packages dans cet ordre alphabétique aussi, donc l'import inter-package fonctionne au démarrage.

Pour une installation sélective :
```bash
make link PLUGIN=AlfacoLib       # d'abord
make link PLUGIN=AlfacoAtlassian # puis les consommateurs
```
