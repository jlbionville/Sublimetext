# Installation

## Pré-requis

- **Sublime Text** version ≥ 3.0 (déclaré dans `package-metadata.json` : `"sublime_text": ">=3000"`).
- **Python `requests`** disponible dans le plugin host de Sublime. Le package l'importe (`modules/tools.py`) mais ne le déclare pas comme dépendance Package Control. Voir la section [Dépendance requests](#dépendance-requests).
- **Compte Atlassian** avec accès Jira (et Confluence si vous comptez utiliser les snippets associés), et un **token API** (jamais le mot de passe du compte).
- **Plateformes** : Windows, Linux, macOS — mais certains chemins par défaut sont Windows (voir [troubleshooting.md](troubleshooting.md#chemin-windows-coden-dur)).

## Localiser le dossier `Packages` de Sublime Text

Ouvrir Sublime Text puis : `Preferences → Browse Packages…`. Cela ouvre le dossier `Packages` de votre installation. Les chemins typiques :

| OS | Chemin |
|---|---|
| Linux | `~/.config/sublime-text/Packages/` (ST4) ou `~/.config/sublime-text-3/Packages/` (ST3) |
| Windows | `%APPDATA%\Sublime Text\Packages\` |
| macOS | `~/Library/Application Support/Sublime Text/Packages/` |

## Installer le package

### Option A — Clone direct (mode développeur, recommandé pour ce dépôt)

```bash
cd "<dossier Packages>"
git clone https://github.com/jlbionville/Sublimetext.git Alfaco
```

Le dossier doit s'appeler **exactement `Alfaco`** : les keymaps et menus référencent `Packages/Alfaco/...` (par exemple `Packages/Alfaco/snippets/jira/jira.sublime-snippet` dans la keymap Windows).

### Option B — Lien symbolique (édition depuis votre dépôt local)

Pratique si vous travaillez dans `~/code/Sublimetext` et voulez que les modifications soient prises en compte par Sublime sans recopie :

```bash
# Linux / macOS
ln -s "$HOME/code/Sublimetext" "<dossier Packages>/Alfaco"

# Windows (PowerShell admin)
New-Item -ItemType SymbolicLink -Path "<Packages>\Alfaco" -Target "C:\code\Sublimetext"
```

### Recharge automatique

Sublime recharge les fichiers `*.py` à la sauvegarde et rejoue `plugin_loaded()`. Surveiller la console (`` Ctrl+` ``) pour voir les `print()` du plugin.

## Dépendance `requests`

Le package importe `requests` dans `modules/tools.py` mais `package-metadata.json` déclare `"dependencies": []`. Sur une installation Sublime fraîche, l'import lèvera `ModuleNotFoundError`.

Trois solutions :

1. **Package Control + dépendance manuelle** : installer le package `requests` via Package Control en créant un fichier `dependencies.json` à la racine :
   ```json
   {
       "*": { "*": ["requests"] }
   }
   ```
   puis lancer `Package Control: Satisfy Dependencies` depuis la palette.

2. **Vendoring** : copier `requests` (et ses dépendances `urllib3`, `certifi`, `chardet`/`charset_normalizer`, `idna`) dans `modules/vendor/` et ajuster les imports.

3. **`pip install --target`** dans le dossier des paquets Python embarqués (fragile, à éviter).

> **TODO projet** : ajouter le fichier `dependencies.json` officiel pour que Package Control gère `requests` automatiquement.

## Première configuration

1. Ouvrir `Preferences → Package Settings → Alfaco → Settings – User`.
2. Coller au minimum :
   ```json
   {
       "jira_login": "votre.email@domaine.tld",
       "jira_password": "VOTRE_TOKEN_API_ATLASSIAN",
       "api_rest_version": "3",
       "path_json_files_folder": "/chemin/absolu/vers/dossier/jira"
   }
   ```
3. Recharger Sublime (`Tools → Command Palette → Restart`) ou simplement modifier un `.py` du package pour retrigger `plugin_loaded()`.
4. Vérifier dans la console : pas d'exception, et la commande `Tools → Alfaco → Jira → open list projects` doit afficher dans la console les valeurs de `jira_login` / `jira_password`.

Voir [configuration.md](configuration.md) pour la référence complète des clés.

## Désinstallation

Supprimer le dossier `Packages/Alfaco/`. Aucune donnée n'est conservée hors `Preferences.sublime-settings` : la clé `organisation` y est écrite par `plugin_loaded()` et peut être retirée manuellement.
