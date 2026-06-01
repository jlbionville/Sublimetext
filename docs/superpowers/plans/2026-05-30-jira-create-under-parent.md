# Créer une issue sous un parent (Epic/Story) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permettre de créer une issue Jira rattachée à un parent (Epic ou Story) depuis le flux Markdown : champ `# Parent` + commande popup qui le pré-remplit.

**Architecture:** Logique pure dans `AlfacoLib` (champ `# Parent` → `fields["parent"]={"key":…}` dans `parse_markdown_jira_template` ; helper `parse_parent_choices` pour le popup), testée hors-Sublime. Une commande `select_jira_parent` interroge `search` JQL (types configurables) et délègue l'écriture dans le buffer à une commande d'édition `set_markdown_parent`. Snippet + settings + UI complètent le flux.

**Tech Stack:** Python 3.8 (host Sublime Text 4), `urllib` stdlib, pytest hors-Sublime, fichiers `.sublime-keymap`/`.sublime-menu`/`.sublime-snippet`/`.sublime-settings`.

**Contraintes projet :** code/commentaires/captions en **français** ; une commande = un fichier dans `commands/` importée dans `plugin.py` ; mettre à jour **les 3 keymaps OS** ; commits fréquents ; pas de `--no-verify`. Sur ce Jira Cloud, parent (Epic et Story) = champ unique `parent` `{"key": …}`.

---

## File Structure

- **Modify** `plugins/AlfacoLib/markdown_to_adf.py` — `KNOWN_FIELDS` += `"Parent"` ; `parse_markdown_jira_template` ajoute `fields["parent"]`.
- **Modify** `plugins/AlfacoLib/tests/test_markdown_to_adf.py` — MAJ `test_known_fields_constants` + nouveaux tests `# Parent`.
- **Modify** `plugins/AlfacoLib/atlassian_client.py` — `parse_parent_choices(data)`.
- **Modify** `plugins/AlfacoLib/tests/test_atlassian_client.py` — tests `parse_parent_choices`.
- **Modify** `plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet` — section `# Parent\n${parent}`.
- **Modify** `plugins/AlfacoAtlassian/commands/init_markdown_jira.py` — `args.setdefault("parent", "")`.
- **Create** `plugins/AlfacoAtlassian/commands/select_jira_parent.py` — `SelectJiraParentCommand` + `SetMarkdownParentCommand`.
- **Modify** `plugins/AlfacoAtlassian/plugin.py` — import des 2 commandes.
- **Modify** `plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings` — `jira_parent_types`.
- **Modify** `plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings` — bloc documenté `jira_parent_types`.
- **Modify** `Context.sublime-menu`, `Main.sublime-menu`, 3 `.sublime-keymap` — entrée + chord `Ctrl+J Ctrl+R`.
- **Modify** `docs/plugins/alfaco-atlassian.md`, `docs/usage.md`, `docs/configuration.md` — doc.

---

## Task 1 : champ `# Parent` dans le parser (TDD)

**Files:**
- Test: `plugins/AlfacoLib/tests/test_markdown_to_adf.py`
- Modify: `plugins/AlfacoLib/markdown_to_adf.py`

- [ ] **Step 1 : mettre à jour le test de constante + ajouter les tests `# Parent`**

Dans `plugins/AlfacoLib/tests/test_markdown_to_adf.py`, remplacer le corps de
`test_known_fields_constants` (actuellement il asserte la liste SANS `Parent`) par :

```python
def test_known_fields_constants():
    """Les 10 champs réservés du template (Organisation = routage, Startdate/Parent optionnels)."""
    assert KNOWN_FIELDS == [
        "Summary", "Organisation", "Project", "Type", "Priority", "Labels",
        "Parent", "Startdate", "Duedate", "Description",
    ]
```

Puis ajouter à la FIN du fichier :

```python
def test_parse_parent_present_goes_to_fields():
    template = "# Summary\nS\n\n# Parent\nMMPO-2\n\n# Description\nbody"
    payload, _ = parse_markdown_jira_template(template, _DEFAULTS)
    assert payload["fields"]["parent"] == {"key": "MMPO-2"}


def test_parse_parent_absent_field_omitted():
    template = "# Summary\nS\n\n# Description\nbody"
    payload, _ = parse_markdown_jira_template(template, _DEFAULTS)
    assert "parent" not in payload["fields"]


def test_parse_parent_empty_value_omitted():
    template = "# Summary\nS\n\n# Parent\n\n\n# Description\nbody"
    payload, _ = parse_markdown_jira_template(template, _DEFAULTS)
    assert "parent" not in payload["fields"]


def test_split_fields_accepts_parent():
    template = "# Summary\nS\n\n# Parent\nMMPO-2\n\n# Description\nbody"
    result = _split_fields(template)
    assert result["Parent"] == "MMPO-2"
```

- [ ] **Step 2 : lancer les tests pour vérifier l'échec**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -k "parent or known_fields" -v`
Expected: FAIL — `test_known_fields_constants` échoue (Parent absent) et les 3 `parent` échouent (`# Parent` lève « champ inconnu » / clé absente).

- [ ] **Step 3 : ajouter `Parent` à KNOWN_FIELDS**

Dans `plugins/AlfacoLib/markdown_to_adf.py`, remplacer :

```python
KNOWN_FIELDS = [
    "Summary", "Organisation", "Project", "Type", "Priority", "Labels",
    "Startdate", "Duedate", "Description",
]
```

par :

```python
KNOWN_FIELDS = [
    "Summary", "Organisation", "Project", "Type", "Priority", "Labels",
    "Parent", "Startdate", "Duedate", "Description",
]
```

- [ ] **Step 4 : injecter `parent` dans le payload**

Dans `parse_markdown_jira_template`, juste APRÈS le bloc startdate (les lignes) :

```python
    startdate = (fields_md.get("Startdate") or "").strip()
    startdate_field = defaults.get("startdate_field", "")
    if startdate and startdate_field:
        fields[startdate_field] = startdate
```

ajouter :

```python
    parent = (fields_md.get("Parent") or "").strip()
    if parent:
        fields["parent"] = {"key": parent}
```

- [ ] **Step 5 : lancer les tests pour vérifier le succès**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: PASS (tous, dont les 4 nouveaux + `test_known_fields_constants` mis à jour).

- [ ] **Step 6 : commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(lib): champ # Parent -> fields.parent dans le template Markdown"
```

---

## Task 2 : helper `parse_parent_choices` (TDD)

**Files:**
- Test: `plugins/AlfacoLib/tests/test_atlassian_client.py`
- Modify: `plugins/AlfacoLib/atlassian_client.py`

- [ ] **Step 1 : écrire les tests qui échouent**

Le fichier importe déjà `from AlfacoLib import atlassian_client` (ajouté en PR #27). Ajouter à
la FIN de `plugins/AlfacoLib/tests/test_atlassian_client.py` :

```python
def test_parse_parent_choices_extracts_key_and_label():
    data = {
        "issues": [
            {"key": "MMPO-2", "fields": {"summary": "Sync Obsidian",
                                         "issuetype": {"name": "Epic"}}},
            {"key": "MMPO-8", "fields": {"summary": "Emplacement équipements",
                                         "issuetype": {"name": "Story"}}},
        ]
    }
    assert atlassian_client.parse_parent_choices(data) == [
        ("MMPO-2", "MMPO-2 — Sync Obsidian (Epic)"),
        ("MMPO-8", "MMPO-8 — Emplacement équipements (Story)"),
    ]


def test_parse_parent_choices_empty():
    assert atlassian_client.parse_parent_choices({"issues": []}) == []
    assert atlassian_client.parse_parent_choices({}) == []
    assert atlassian_client.parse_parent_choices(None) == []


def test_parse_parent_choices_ignores_entries_without_key():
    data = {"issues": [
        {"fields": {"summary": "x", "issuetype": {"name": "Epic"}}},
        {"key": "MMPO-1", "fields": {"summary": "ok", "issuetype": {"name": "Epic"}}},
    ]}
    assert atlassian_client.parse_parent_choices(data) == [
        ("MMPO-1", "MMPO-1 — ok (Epic)"),
    ]


def test_parse_parent_choices_tolerates_missing_summary_or_type():
    data = {"issues": [{"key": "MMPO-9", "fields": {}}]}
    assert atlassian_client.parse_parent_choices(data) == [
        ("MMPO-9", "MMPO-9 —  ()"),
    ]
```

- [ ] **Step 2 : lancer les tests pour vérifier l'échec**

Run: `pytest plugins/AlfacoLib/tests/test_atlassian_client.py -k parent_choices -v`
Expected: FAIL — `AttributeError: ... has no attribute 'parse_parent_choices'`.

- [ ] **Step 3 : implémenter le helper**

Ajouter à la FIN de `plugins/AlfacoLib/atlassian_client.py` :

```python
def parse_parent_choices(data):
    """Extrait les parents candidats d'une réponse Jira `search`.

    `data` est l'objet décodé du `GET .../search?jql=...`, de forme
    `{"issues": [{"key", "fields": {"summary", "issuetype": {"name"}}}]}`.
    Retourne une liste de tuples `(key, label)` avec
    `label = "KEY — résumé (Type)"`, dans l'ordre de la réponse.
    Ignore les entrées sans `key`. Retourne `[]` si `data` vide/mal formé.
    """
    if not isinstance(data, dict):
        return []
    issues = data.get("issues") or []
    choices = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        key = issue.get("key")
        if not key:
            continue
        fields = issue.get("fields") or {}
        summary = fields.get("summary") or ""
        issuetype = fields.get("issuetype") or {}
        type_name = issuetype.get("name") or ""
        label = f"{key} — {summary} ({type_name})"
        choices.append((key, label))
    return choices
```

- [ ] **Step 4 : lancer les tests pour vérifier le succès**

Run: `pytest plugins/AlfacoLib/tests/test_atlassian_client.py -k parent_choices -v`
Expected: PASS (4 tests). Puis `pytest plugins/AlfacoLib/tests/test_atlassian_client.py -q` → tous verts.

- [ ] **Step 5 : commit**

```bash
git add plugins/AlfacoLib/atlassian_client.py plugins/AlfacoLib/tests/test_atlassian_client.py
git commit -m "feat(lib): parse_parent_choices (popup parents Jira)"
```

---

## Task 3 : snippet `# Parent` + défaut dans init_markdown_jira

Pas de test (snippet/Command non testables hors-Sublime). Validation manuelle (Task 7).

**Files:**
- Modify: `plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet`
- Modify: `plugins/AlfacoAtlassian/commands/init_markdown_jira.py`

- [ ] **Step 1 : ajouter la section `# Parent` au snippet**

Dans `plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet`, le contenu
inclut actuellement (entre `# Labels` et `# Startdate`) :

```
# Labels
important, urgent

# Startdate
${startdate}
```

Insérer une section `# Parent` ENTRE `# Labels` et `# Startdate`, pour donner :

```
# Labels
important, urgent

# Parent
${parent}

# Startdate
${startdate}
```

(Ne pas toucher au reste.)

- [ ] **Step 2 : poser le défaut `parent` dans init_markdown_jira**

Dans `plugins/AlfacoAtlassian/commands/init_markdown_jira.py`, après la ligne
`args.setdefault("type", "Task")`, ajouter :

```python
        args.setdefault("parent", "")
```

- [ ] **Step 3 : valider le XML du snippet + suite verte**

Run:
```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet'); print('XML OK')"
make test
```
Expected: `XML OK` puis suite verte (les nouveaux champs n'affectent pas les tests existants).

- [ ] **Step 4 : commit**

```bash
git add plugins/AlfacoAtlassian/snippets/jira/jira-markdown.sublime-snippet plugins/AlfacoAtlassian/commands/init_markdown_jira.py
git commit -m "feat(atlassian): section # Parent dans le template Markdown (vide par défaut)"
```

---

## Task 4 : commandes `select_jira_parent` + `set_markdown_parent`

Pas de test unitaire (TextCommand non testables hors-Sublime). La logique testable est dans
`parse_parent_choices` (Task 2) et le parser (Task 1).

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/select_jira_parent.py`
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1 : créer le fichier de commandes**

Créer `plugins/AlfacoAtlassian/commands/select_jira_parent.py` avec EXACTEMENT :

```python
# -*- coding: utf-8 -*-
"""Popup des parents (Epic/Story) du projet courant, remplit `# Parent` du buffer.

select_jira_parent : GET .../search?jql=..., popup `KEY — résumé (Type)`.
À la sélection, délègue à set_markdown_parent (commande d'édition) qui écrit la
clé sous la section `# Parent` du buffer Markdown courant. Le périmètre des types
proposés est configurable via `jira_parent_types` (défaut ["Epic", "Story"]).
"""
import re
import socket
from urllib.error import URLError
from urllib.parse import quote

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, parse_parent_choices


class SelectJiraParentCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config

        project_key = cfg.get("project_key", "")
        if not project_key:
            _atlassian_plugin.log.error("project_key vide : select_jira_project requis d'abord")
            sublime.error_message(
                "AlfacoAtlassian : aucun projet courant.\n\n"
                "Lance d'abord « Sélectionner projet Jira » (select_jira_project)."
            )
            return

        login, password = cfg.jira_auth()
        if not login or not password:
            _atlassian_plugin.log.error(
                f"jira_login/jira_password vide (login={login!r}, password={'(set)' if password else '(empty)'})"
            )
            sublime.error_message(
                "AlfacoAtlassian : `jira_login` ou `jira_password` manquant.\n\n"
                "Renseigner un email et un token API dans :\n"
                "Preferences → Package Settings → AlfacoAtlassian → Settings – User"
            )
            return

        types = cfg.get("jira_parent_types", ["Epic", "Story"])
        clause = ", ".join('"%s"' % t for t in types)
        jql = 'project = "%s" AND issuetype in (%s) ORDER BY created DESC' % (project_key, clause)
        url = cfg.base_url() + "search?jql=" + quote(jql)
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération parents ({project_key})…")

        try:
            response = call_rest(
                url,
                body=None,
                auth=(login, password),
                headers=cfg.get("headers", {"Accept": "application/json"}),
                verb="GET",
                verify=cfg.get("tls_verify", True),
            )
        except (URLError, socket.timeout) as e:
            _atlassian_plugin.log.error(f"erreur réseau sur {url} : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : impossible de joindre {url}\n\n"
                f"{e}\n\nVérifier `default_organisation` et la connectivité."
            )
            return

        _atlassian_plugin.log.info(
            f"GET {url} → {response.status_code} ({len(response.text)} bytes)"
        )

        if response.status_code != 200:
            _atlassian_plugin.log.error(
                f"GET {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : la requête a échoué.\n\n"
                f"HTTP {response.status_code}\n{response.text[:500]}"
            )
            return

        try:
            data = response.json()
        except ValueError as e:
            _atlassian_plugin.log.error(
                f"réponse non-JSON ({len(response.text)} bytes) : {e} | preview={response.text[:200]!r}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : réponse non-JSON.\n\n{response.text[:500]}"
            )
            return

        self._choices = parse_parent_choices(data)
        if not self._choices:
            _atlassian_plugin.log.warn(
                f"{url} : 0 parent (status=200, preview={response.text[:200]!r})"
            )
            sublime.message_dialog(
                f"AlfacoAtlassian : aucune Epic/Story trouvée pour {project_key}."
            )
            return

        labels = [label for _, label in self._choices]
        _atlassian_plugin.log.info(f"{len(labels)} parent(s) prêts pour le popup")
        sublime.status_message(f"AlfacoAtlassian : {len(labels)} parent(s)")
        self.view.show_popup_menu(labels, self._on_done)

    def _on_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection parent annulée")
            return
        key = self._choices[index][0]
        _atlassian_plugin.log.info(f"parent sélectionné : {key}")
        self.view.run_command("set_markdown_parent", {"key": key})


class SetMarkdownParentCommand(sublime_plugin.TextCommand):
    """Écrit `key` sous la section `# Parent` du buffer courant.

    Si `# Parent` existe : remplace la ligne suivante par la clé.
    Sinon : insère un bloc `# Parent\\n<key>` avant `# Description`
    (ou en fin de buffer si `# Description` absent).
    """
    def run(self, edit, key):
        view = self.view
        full = sublime.Region(0, view.size())
        text = view.substr(full)
        lines = text.split("\n")

        parent_idx = None
        description_idx = None
        for i, line in enumerate(lines):
            if re.match(r"^#\s+Parent\s*$", line):
                parent_idx = i
            elif re.match(r"^#\s+Description\s*$", line) and description_idx is None:
                description_idx = i

        if parent_idx is not None:
            # Remplace la ligne valeur (juste après le heading) si elle existe et
            # n'est pas un autre heading ; sinon insère la valeur.
            value_idx = parent_idx + 1
            if value_idx < len(lines) and not lines[value_idx].startswith("#"):
                lines[value_idx] = key
            else:
                lines.insert(value_idx, key)
        elif description_idx is not None:
            lines[description_idx:description_idx] = ["# Parent", key, ""]
        else:
            lines += ["", "# Parent", key]

        view.replace(edit, full, "\n".join(lines))
        _atlassian_plugin.log.info(f"# Parent renseigné : {key}")
        sublime.status_message(f"AlfacoAtlassian : parent = {key}")
```

- [ ] **Step 2 : enregistrer les commandes dans plugin.py**

Dans `plugins/AlfacoAtlassian/plugin.py`, après la dernière ligne d'import de commande
(`from AlfacoAtlassian.commands.select_jira_issue_type import SelectJiraIssueTypeCommand  # noqa: E402, F401`),
ajouter :

```python
from AlfacoAtlassian.commands.select_jira_parent import SelectJiraParentCommand, SetMarkdownParentCommand  # noqa: E402, F401
```

- [ ] **Step 3 : vérifier la syntaxe Python**

Run: `python3 -c "import ast; ast.parse(open('plugins/AlfacoAtlassian/commands/select_jira_parent.py').read()); ast.parse(open('plugins/AlfacoAtlassian/plugin.py').read()); print('OK')"`
Expected: `OK`.

- [ ] **Step 4 : suite verte (non-régression)**

Run: `make test`
Expected: PASS.

- [ ] **Step 5 : commit**

```bash
git add plugins/AlfacoAtlassian/commands/select_jira_parent.py plugins/AlfacoAtlassian/plugin.py
git commit -m "feat(atlassian): select_jira_parent + set_markdown_parent (popup parents)"
```

---

## Task 5 : settings `jira_parent_types`

**Files:**
- Modify: `plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings`
- Modify: `plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings`

- [ ] **Step 1 : ajouter la clé au settings du package**

Dans `plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings`, après la ligne
`"jira_startdate_field": "customfield_10015",` ajouter :

```json
    "jira_parent_types": ["Epic", "Story"],
```

(Vérifier que la virgule précédente est présente ; JSON strict, pas de virgule traînante.)

- [ ] **Step 2 : documenter dans le template User**

Dans `plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings`, après le
bloc `jira_startdate_field` (la ligne `"jira_startdate_field": "customfield_10015",`),
ajouter :

```jsonc

    // === Types de parent (popup "choisir le parent") ===

    // Types d'issues proposés par la commande select_jira_parent comme parent
    // possible (Ctrl+J Ctrl+R). Le champ # Parent du template reste prioritaire.
    "jira_parent_types": ["Epic", "Story"],
```

- [ ] **Step 3 : valider le JSON du settings package**

Run: `python3 -c "import json; json.load(open('plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings')); print('JSON OK')"`
Expected: `JSON OK`. (Le template User contient des commentaires JSONC → ne pas le passer à `json.load` ; vérifier visuellement.)

- [ ] **Step 4 : commit**

```bash
git add plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings
git commit -m "feat(atlassian): réglage jira_parent_types (défaut Epic, Story)"
```

---

## Task 6 : intégration UI (menus + 3 keymaps)

**Files:**
- Modify: `plugins/AlfacoAtlassian/Context.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Main.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`

- [ ] **Step 1 : menu contextuel**

Dans `plugins/AlfacoAtlassian/Context.sublime-menu`, après la ligne
`{ "caption": "insérer projet courant", "command": "insert_current_project" }` (dernière
entrée du tableau `children`), ajouter une virgule à cette ligne puis la nouvelle entrée :

```json
            { "caption": "insérer projet courant", "command": "insert_current_project" },
            { "caption": "choisir le parent (Epic/Story)", "command": "select_jira_parent" }
```

- [ ] **Step 2 : menu Tools**

Dans `plugins/AlfacoAtlassian/Main.sublime-menu`, dans le tableau `children` du nœud
`alfaco-atlassian`, après la ligne
`{ "caption": "Insérer projet courant", "command": "insert_current_project" },` ajouter :

```json
                            { "caption": "Choisir le parent (Epic/Story)", "command": "select_jira_parent" },
```

(La ligne suivante est `{ "caption": "Open Jira projects (debug)", ... }` qui termine sans
virgule — ne pas créer de virgule traînante.)

- [ ] **Step 3 : keymap Linux**

Dans `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`, après la ligne
`{ "keys": ["ctrl+j", "ctrl+t"], "command": "select_jira_issue_type" },` ajouter :

```json
    { "keys": ["ctrl+j", "ctrl+r"], "command": "select_jira_parent" },
```

- [ ] **Step 4 : keymap Windows**

Dans `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`, après la ligne
`{ "keys": ["ctrl+j", "ctrl+t"], "command": "select_jira_issue_type" },` ajouter la même
ligne :

```json
    { "keys": ["ctrl+j", "ctrl+r"], "command": "select_jira_parent" },
```

- [ ] **Step 5 : keymap OSX**

Dans `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`, après la ligne
`{ "keys": ["super+j", "super+t"], "command": "select_jira_issue_type" },` ajouter :

```json
    { "keys": ["super+j", "super+r"], "command": "select_jira_parent" },
```

- [ ] **Step 6 : valider le JSON des 5 fichiers**

Run:
```bash
python3 -c "import json; [json.load(open(f)) for f in ['plugins/AlfacoAtlassian/Context.sublime-menu','plugins/AlfacoAtlassian/Main.sublime-menu','plugins/AlfacoAtlassian/Default (Linux).sublime-keymap','plugins/AlfacoAtlassian/Default (Windows).sublime-keymap','plugins/AlfacoAtlassian/Default (OSX).sublime-keymap']]; print('JSON OK')"
```
Expected: `JSON OK` (ces 5 fichiers sont du JSON strict sans commentaires sur ce repo).
Confirmer aussi que `select_jira_parent` apparaît une fois par fichier :
```bash
for f in "plugins/AlfacoAtlassian/Context.sublime-menu" "plugins/AlfacoAtlassian/Main.sublime-menu" "plugins/AlfacoAtlassian/Default (Linux).sublime-keymap" "plugins/AlfacoAtlassian/Default (Windows).sublime-keymap" "plugins/AlfacoAtlassian/Default (OSX).sublime-keymap"; do printf "%s -> %s\n" "$(basename "$f")" "$(grep -c select_jira_parent "$f")"; done
```
Expected: chaque fichier `-> 1`.

- [ ] **Step 7 : commit**

```bash
git add "plugins/AlfacoAtlassian/Context.sublime-menu" "plugins/AlfacoAtlassian/Main.sublime-menu" "plugins/AlfacoAtlassian/Default (Linux).sublime-keymap" "plugins/AlfacoAtlassian/Default (Windows).sublime-keymap" "plugins/AlfacoAtlassian/Default (OSX).sublime-keymap"
git commit -m "feat(atlassian): menus + raccourci Ctrl+J Ctrl+R pour select_jira_parent"
```

---

## Task 7 : documentation

**Files:**
- Modify: `docs/plugins/alfaco-atlassian.md`
- Modify: `docs/usage.md`
- Modify: `docs/configuration.md`

- [ ] **Step 1 : documenter la commande + le champ dans alfaco-atlassian.md**

Dans `docs/plugins/alfaco-atlassian.md`, table « Commandes », après la ligne
`| select_jira_issue_type | ... |` ajouter :

```markdown
| `select_jira_parent` | Popup des parents (Epic/Story par défaut, cf. `jira_parent_types`) du projet courant (`search` JQL) ; à la sélection, remplit la section `# Parent` du buffer Markdown. |
```

Dans la table « Raccourcis », après la ligne `Ctrl+J Ctrl+T … select_jira_issue_type`,
ajouter :

```markdown
| `Ctrl+J Ctrl+R` / `Cmd+J Cmd+R` | tous | `select_jira_parent` (popup Epic/Story, remplit `# Parent`) |
```

Dans la table « Référence des clés » (section Configuration), après la ligne
`jira_startdate_field`, ajouter :

```markdown
| `jira_parent_types` | array | `["Epic", "Story"]` | Types d'issues proposés par `select_jira_parent` comme parent possible. |
```

Dans la section « Workflow Markdown », ajouter à la liste des champs réservés `Parent`
(après `Labels`) et une phrase :

```markdown
`# Parent` (optionnel) rattache l'issue créée à une Epic ou une Story : la clé saisie est
envoyée comme `parent` (`{"key": "<KEY>"}`). La commande `select_jira_parent`
(`Ctrl+J Ctrl+R`) propose les Epics/Stories du projet et remplit ce champ.
```

- [ ] **Step 2 : usage.md**

Dans `docs/usage.md`, section « Index des commandes » → « AlfacoAtlassian », ajouter
`select_jira_parent` (après `select_jira_issue_type`).

Dans la sous-section « Variante Markdown », après la puce « Alternative typée », ajouter :

```markdown
   - *Rattacher à un parent* : `select_jira_parent` (`Ctrl+J Ctrl+R`) propose les Epics/Stories du projet et remplit `# Parent` ; à défaut, saisir la clé à la main sous `# Parent`.
```

Mettre aussi à jour la ligne 18 (champs réservés) pour inclure `# Parent` après `# Labels`.

- [ ] **Step 3 : configuration.md**

Dans `docs/configuration.md`, ajouter une entrée pour `jira_parent_types` à l'endroit où les
clés de `alfaco-atlassian` sont décrites (près de `jira_startdate_field`) :

```markdown
- `jira_parent_types` (array, défaut `["Epic", "Story"]`) — types d'issues proposés par la commande `select_jira_parent` comme parent. Élargir (ex. ajouter `"Tâche"`) pour autoriser d'autres parents.
```

Si `docs/configuration.md` n'a pas de section dédiée à `alfaco-atlassian`, placer l'entrée à
côté des autres clés `jira_*` existantes ; lire le fichier d'abord pour trouver l'emplacement
cohérent.

- [ ] **Step 4 : commit**

```bash
git add docs/plugins/alfaco-atlassian.md docs/usage.md docs/configuration.md
git commit -m "docs(atlassian): documenter select_jira_parent, # Parent, jira_parent_types"
```

---

## Task 8 : validation manuelle dans Sublime (humain)

Non automatisable. À réaliser après `make install`.

- [ ] `make install` puis redémarrer Sublime.
- [ ] `select_organisation` + `select_jira_project`.
- [ ] `Ctrl+J Ctrl+T` → buffer Markdown typé (section `# Parent` vide présente).
- [ ] `Ctrl+J Ctrl+R` → popup `KEY — résumé (Type)` listant les Epics/Stories ; sélectionner une Epic → la section `# Parent` du buffer se remplit avec la clé.
- [ ] Compléter summary/description, `Alt+M` → l'issue est créée **rattachée au parent** (vérifier le lien parent dans Jira).
- [ ] ⚠️ Si `Ctrl+J Ctrl+R` renvoie une erreur HTTP 410/404 : l'endpoint `search?jql=` doit devenir `search/jql` (cf. spec). Adapter `url` dans `select_jira_parent.py` et re-tester.
- [ ] Saisie manuelle : taper une clé sous `# Parent` sans popup → `Alt+M` rattache aussi.
- [ ] Sans projet courant : `Ctrl+J Ctrl+R` affiche le message « aucun projet courant ».
- [ ] Élargir `jira_parent_types` (ex. `["Epic", "Story", "Tâche"]`) dans User settings → le popup propose les tâches.

---

## Self-Review (auteur du plan)

- **Couverture du spec** : champ `# Parent` parser (T1) ✓ ; `parse_parent_choices` (T2) ✓ ;
  snippet + défaut (T3) ✓ ; commandes popup + édition buffer (T4) ✓ ; `jira_parent_types`
  settings package + template (T5) ✓ ; menus + 3 keymaps `Ctrl+J Ctrl+R` (T6) ✓ ; docs
  (T7) ✓ ; validation manuelle dont fallback `search/jql` (T8) ✓. Gestion d'erreurs du spec
  couverte par le code de T4. Priorité « Markdown prioritaire » respectée : le popup écrit
  dans `# Parent`, et c'est `# Parent` qui est lu au POST (T1) — une seule source de vérité.
- **Placeholders** : aucun — code complet partout. (T7 step 3 demande de lire
  `configuration.md` pour situer l'entrée, mais fournit le texte exact à insérer.)
- **Cohérence des types** : `parse_parent_choices(data) -> list[(key, label)]` ; la commande
  affiche `label` et passe `key` à `set_markdown_parent({"key": key})` ; `# Parent` → 
  `fields["parent"] = {"key": parent}` (T1) cohérent. `KNOWN_FIELDS` mis à jour à la fois
  dans le code (T1 step 3) et dans le test de constante (T1 step 1).
