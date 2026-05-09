# AlfacoLib

Bibliothèque partagée des plugins Sublime Text Alfaco. **Aucune commande utilisateur** — uniquement du code réutilisable.

## API publique

### `config.Configuration`

```python
from AlfacoLib.config import Configuration

cfg = Configuration([
    "alfaco-X.sublime-settings",
    "Preferences.sublime-settings",
])

cfg.get(key, default=None)        # lookup runtime → settings layers → default
cfg.set(key, value)                # ne mute QUE le runtime (jamais Preferences)
cfg.jira_auth()                    # → (login, password)
cfg.base_url(version=None)         # → 'https://<org>.atlassian.net/rest/api/<v>/'
```

### `atlassian_client`

```python
from AlfacoLib.atlassian_client import call_rest, list_projects

response = call_rest(url, body, auth, headers, verb="GET", verify=True, timeout=(5, 30))
projects = list_projects(url, auth, headers, verify=True, timeout=(5, 30))
# projects = ['BUS-Business', 'DEV-Dev', ...]
```

`call_rest` retourne une `requests.Response` brute (l'appelant décide quoi en faire). `list_projects` lève `RuntimeError` si le serveur ne répond pas 200.

### `io`

```python
from AlfacoLib.io import save_file, read_file, build_response_path, build_payload_path

save_file("contenu UTF-8", "/chemin/fichier.txt")    # crée les dossiers parents
content = read_file("/chemin/fichier.txt")
build_response_path("/dossier", "20260508-120000")   # → Path('/dossier/error_api_call_20260508-120000.html')
build_payload_path("/dossier", "BUS-42")             # → Path('/dossier/BUS-42.json')
```

### `logger`

```python
from AlfacoLib.logger import get_logger

log = get_logger("MonPlugin", debug=cfg.get("debug", False))
log.debug("trace")    # affiché si debug=True
log.info("info")      # alias de debug
log.warn("oops")      # toujours affiché, même debug=False
```

## Pourquoi un package séparé

Voir [../architecture.md](../architecture.md). Pattern utilisé par les packages officiels Sublime (Default, LSP, PackageControl) : un package "lib" sans commandes, importable par les autres packages via `from PackageName.module import symbol`.

## Tests

`pytest plugins/AlfacoLib/tests/` (24 tests : 7 config, 6 atlassian_client, 4 io, 3 logger, 4 deploy_paths, 4 deploy_ops).

## Version

`0.1.0` (cf. `package-metadata.json`).
