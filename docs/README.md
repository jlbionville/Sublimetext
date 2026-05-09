# Documentation Alfaco

Monorepo des plugins Sublime Text 4 Alfaco.

## Plugins

| Plugin | Description | Doc |
|---|---|---|
| `AlfacoLib` | Bibliothèque partagée (Configuration, client REST Atlassian, IO, logger) | [plugins/alfaco-lib.md](plugins/alfaco-lib.md) |
| `AlfacoAtlassian` | Pilotage Jira/Confluence depuis l'éditeur | [plugins/alfaco-atlassian.md](plugins/alfaco-atlassian.md) |
| `AlfacoEditing` | Utilitaires d'édition (text-to-table, marqueurs, dates, tags) | [plugins/alfaco-editing.md](plugins/alfaco-editing.md) |
| `AlfacoCompletion` | Auto-complétion Python | [plugins/alfaco-completion.md](plugins/alfaco-completion.md) |

## Documentation transversale

- [Installation](installation.md) — pré-requis, déploiement, première config.
- [Architecture](architecture.md) — topologie multi-plugins, flux d'import inter-package.
- [Configuration](configuration.md) — clés des `.sublime-settings`, sécurité du token.
- [Déploiement](deployment.md) — Makefile, multi-OS, WSL.
- [Contributing](contributing.md) — workflow, `make new-plugin`, conventions.
- [Troubleshooting](troubleshooting.md) — bugs corrigés, diagnostic Atlassian.
