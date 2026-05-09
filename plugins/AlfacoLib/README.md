# AlfacoLib

Bibliothèque partagée des plugins Sublime Text Alfaco. Ne contient aucune commande utilisateur.

## Modules

- `config.Configuration` — Configuration empilée (settings + runtime).
- `atlassian_client.call_rest` / `list_projects` — Wrapper REST Atlassian (verify/timeout configurables).
- `io.save_file` / `read_file` / `build_response_path` / `build_payload_path` — IO UTF-8 cross-platform.
- `logger.get_logger` — Logger minimal avec flag debug.

## Installation

Depuis le monorepo : `make link PLUGIN=AlfacoLib`.

## Documentation

Voir `docs/plugins/alfaco-lib.md`.
