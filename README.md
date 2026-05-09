# Alfaco

Monorepo des plugins Sublime Text 4 Alfaco — pilotage Atlassian (Jira/Confluence) et utilitaires d'édition.

## Plugins

- **AlfacoLib** — bibliothèque partagée (Configuration, client REST Atlassian, IO, logger).
- **AlfacoAtlassian** — création d'issues Jira, sélection d'organisations/projets, snippets Confluence.
- **AlfacoEditing** — text-to-table, marqueurs `<start>`/`<end>`, insertion de date, gestion de tags.
- **AlfacoCompletion** — auto-complétion Python.

## Installation rapide

```bash
git clone https://github.com/jlbionville/Sublimetext.git
cd Sublimetext
make link              # mode dev (symlinks)  — Linux / macOS
# OU
make install           # mode utilisateur (copie)  — WSL / Windows
```

Puis créer `<Packages>/User/alfaco-atlassian.sublime-settings` avec votre token API Atlassian — voir [docs/configuration.md](docs/configuration.md).

## Documentation

- [Installation](docs/installation.md) — pré-requis, déploiement, première config.
- [Architecture](docs/architecture.md) — topologie, flux d'import inter-package.
- [Déploiement](docs/deployment.md) — Makefile, multi-OS, WSL.
- [Configuration](docs/configuration.md) — clés des `.sublime-settings`.
- [Contributing](docs/contributing.md) — workflow, `make new-plugin`, conventions.
- [Troubleshooting](docs/troubleshooting.md) — bugs résolus, diagnostic Atlassian.
- Documentation par plugin : [docs/plugins/](docs/plugins/).

## Développement

```bash
make test              # pytest hors-Sublime
make new-plugin NAME=X # scaffold un nouveau plugin
make status            # voir l'état de déploiement
make help              # liste toutes les cibles
```

## Licence

Voir [LICENSE](LICENSE).
