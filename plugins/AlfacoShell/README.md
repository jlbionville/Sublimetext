# AlfacoShell — plugin Sublime Text 4 (suite Alfaco)

Exécute le **texte sélectionné comme commande shell** et affiche le résultat
dans un buffer scratch (JSON indenté si parsable, sinon brut), suivi de
`stderr` (si présent) et du code de sortie. Exécution **asynchrone** :
l'éditeur ne gèle pas.

Multi-OS : **macOS** (`/bin/zsh -lc`), **Linux** (`bash -lc`), **Windows via
WSL** (`wsl.exe -e bash -lc`). Le préfixe d'exécution est entièrement
configurable.

Plugin **autonome** : il ne dépend pas d'`AlfacoLib`.

## Fonctionnalités

- Exécute une ou plusieurs régions sélectionnées (concaténées) comme commande.
- Accessible par **clic droit**, **Tools → Alfaco → Shell** ou **Command Palette**.
- Sortie JSON jolie si parsable, sinon texte brut ; `--- stderr ---` et
  `--- exit code: N ---` ajoutés.
- Préfixe d'exécution résolu **par OS**, surchargeable.

## Installation (monorepo)

```bash
make install PLUGIN=AlfacoShell       # copie le plugin + seed la config User/
# ou, hors WSL :
make link PLUGIN=AlfacoShell          # symlink (mode dev)
```

`make install` exécute `init-config` : le fichier de config par défaut est
copié dans `<Packages>/User/alfaco-shell.sublime-settings` (sans écraser un
fichier existant).

## Utilisation

1. Sélectionner une commande, ex. `aws ec2 describe-instances --region eu-west-1`.
2. Command Palette (`Ctrl+Shift+P`) → **AlfacoShell: Exécuter la sélection**
   (ou clic droit, ou Tools → Alfaco → Shell).
3. Un buffer scratch `Shell ▸ …` s'ouvre avec la sortie.

## Configuration

`Preferences → Package Settings → AlfacoShell → Settings – User`

```jsonc
{
    // Override global (tous OS) — prioritaire sur tout le reste.
    // "exec_prefix": ["wsl.exe", "-e", "bash", "-c"],

    // Override par plateforme ("windows" | "osx" | "linux").
    "exec_by_platform": {
        "windows": ["wsl.exe", "-e", "bash", "-lc"],
        "osx": ["/bin/zsh", "-lc"],
        "linux": ["bash", "-lc"]
    },

    "timeout_seconds": 120
}
```

Précédence : `exec_prefix` > `exec_by_platform[os]` > défaut intégré.
`-lc` charge le login shell (donc `PATH`, `~/.aws/config`, variables d'env).

## Architecture

| Couche | Fichier | Rôle |
|--------|---------|------|
| Domain (pur) | `domain.py` | argv par OS, prettify JSON, formatage |
| Adapter | `commands/run_selection.py` | I/O Sublime, subprocess async, buffer |
| Entry-point | `plugin.py` | `plugin_loaded` (reload) + découverte commande |
| Config | `alfaco-shell.sublime-settings` | params surchargeables (non déployé) |
| Interface | `*.sublime-menu` / `Default.sublime-commands` | palette + menus |
| Tests | `tests/test_shell_domain.py` | pytest sur le domain |

Le domain n'importe ni Sublime ni `subprocess` → testable hors éditeur :
`pytest plugins/AlfacoShell/tests/`.

## Erreurs codifiées

| Code | Sens |
|------|------|
| `SELECTION_EMPTY` | Aucune sélection à exécuter |
| `EXEC_TIMEOUT` | Délai d'exécution dépassé |
| `EXEC_FAILED` | Échec du runner |

## Références officielles

- API Sublime Text : <https://www.sublimetext.com/docs/api_reference.html>
- AWS CLI Command Reference : <https://docs.aws.amazon.com/cli/latest/reference/>
