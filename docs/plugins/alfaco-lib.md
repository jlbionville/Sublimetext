# AlfacoLib

## Présentation

Bibliothèque partagée des plugins Sublime Text Alfaco. **Aucune commande utilisateur, aucun raccourci** — uniquement du code réutilisable :
- `Configuration` : settings empilés (runtime → fichiers → défaut).
- `atlassian_client` : wrapper REST minimal sur `urllib` (pas de `requests`).
- `io` : helpers de chemins et de lecture/écriture UTF-8.
- `logger` : logger simple piloté par la clé `debug`.

Pattern utilisé par les packages officiels Sublime (`Default`, `LSP`, `Package Control`) : un package « lib » sans commandes, importable par les autres packages via `from <PackageName>.module import symbol`.

## Prérequis

- Sublime Text 4 (plugin host Python 3.8).
- Aucun package Python tiers — tout est stdlib.

## Configuration

Aucune `.sublime-settings` propre. La config se fait au niveau de chaque consommateur (voir [alfaco-atlassian.md](alfaco-atlassian.md), [alfaco-editing.md](alfaco-editing.md)).

## Utilisation (API publique)

### `config.Configuration`

```python
from AlfacoLib.config import Configuration

cfg = Configuration([
    "alfaco-X.sublime-settings",
    "Preferences.sublime-settings",
])

cfg.get(key, default=None)        # lookup runtime → settings layers → default
cfg.set(key, value)               # ne mute QUE le runtime (jamais Preferences)
cfg.jira_auth()                   # → (login, password)
cfg.base_url(version=None)        # → 'https://<org>.atlassian.net/rest/api/<v>/'
```

### `atlassian_client`

```python
from AlfacoLib.atlassian_client import call_rest, list_projects

response = call_rest(
    url, body, auth, headers,
    verb="GET", verify=True, timeout=(5, 30),
)
# response.status_code, response.text, response.json()

projects = list_projects(url, auth, headers, verify=True, timeout=(5, 30))
# projects = ['BUS-Business', 'DEV-Dev', ...]
```

`call_rest` retourne une `Response` minimale (interface inspirée de `requests` : `status_code`, `text`, `json()`). Implémenté avec `urllib` stdlib pour ne pas dépendre de `requests`, non livré par le plugin host. `list_projects` lève `RuntimeError` si le serveur ne répond pas 200.

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

## Tests

`pytest plugins/AlfacoLib/tests/` couvre Configuration, atlassian_client, io, logger, et les opérations de `tools/deploy.py`.

| Module testé | Fichier | Approche mock |
|---|---|---|
| `Configuration` | `test_config.py` | `MagicMock` sur `sublime.load_settings` |
| `atlassian_client` | `test_atlassian_client.py` | `monkeypatch` sur `AlfacoLib.atlassian_client.urlopen` |
| `io` | `test_io.py` | `tmp_path` (vrais I/O dans un répertoire temporaire) |
| `logger` | `test_logger.py` | `capsys` |
| `tools.deploy` | `test_deploy_paths.py`, `test_deploy_ops.py` | `tmp_path` + monkeypatch env vars |

## Raccourcis

Sans objet — aucun command utilisateur.

## Dépannage

| Erreur | Cause probable | Fix |
|---|---|---|
| `ImportError: No module named 'AlfacoLib'` | Lib non déployée ou plugin host différent | `make status` puis `make link PLUGIN=AlfacoLib`, vérifier que `.python-version` est `3.8` partout. |
| Modifs non prises en compte dans Sublime | Sublime ne cascade pas les reloads | Sauvegarder un `.py` du consommateur pour rejouer `plugin_loaded()` (qui fait `importlib.reload`). |

## Version

`0.1.0` (cf. `package-metadata.json`).
