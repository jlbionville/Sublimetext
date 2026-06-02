# Popup de confirmation après création Jira — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sur succès de création d'un ticket Jira, remplacer l'onglet JSON par un popup affichant la clé (lien cliquable vers le navigateur) et le projet ; conserver l'onglet JSON sur échec.

**Architecture:** Logique pure (URL navigateur, projet depuis la clé, rendu minihtml) isolée dans `AlfacoLib/jira_popup.py` (testée hors-Sublime). Un helper non-testable `AlfacoAtlassian/commands/_created_popup.py` appelle `view.show_popup(..., on_navigate=webbrowser.open)`. Les deux commandes de création (`create_jira_from_markdown`, `create_jira_issue`) appellent ce helper sur succès au lieu d'ouvrir un onglet.

**Tech Stack:** Python 3.8, Sublime Text 4 API (`view.show_popup`, minihtml), `webbrowser` (stdlib), pytest hors-Sublime.

---

### Task 1: Helpers purs dans AlfacoLib

**Files:**
- Create: `plugins/AlfacoLib/jira_popup.py`
- Test: `plugins/AlfacoLib/tests/test_jira_popup.py`

- [ ] **Step 1: Write the failing tests**

Créer `plugins/AlfacoLib/tests/test_jira_popup.py` :

```python
# -*- coding: utf-8 -*-
from AlfacoLib.jira_popup import (
    build_browse_url,
    project_from_key,
    build_creation_popup_html,
)


def test_build_browse_url():
    assert build_browse_url("mysite", "MMPO-123") == \
        "https://mysite.atlassian.net/browse/MMPO-123"


def test_project_from_key_standard():
    assert project_from_key("MMPO-123") == "MMPO"


def test_project_from_key_without_dash():
    assert project_from_key("ABC") == "ABC"


def test_project_from_key_multiple_dashes():
    # le projet est le préfixe avant le dernier '-'
    assert project_from_key("MM-PO-123") == "MM-PO"


def test_build_creation_popup_html_contains_key_project_and_href():
    html = build_creation_popup_html(
        "MMPO-123", "MMPO", "https://mysite.atlassian.net/browse/MMPO-123"
    )
    assert "MMPO-123" in html
    assert "MMPO" in html
    assert 'href="https://mysite.atlassian.net/browse/MMPO-123"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest plugins/AlfacoLib/tests/test_jira_popup.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'AlfacoLib.jira_popup'`

- [ ] **Step 3: Write the implementation**

Créer `plugins/AlfacoLib/jira_popup.py` :

```python
# -*- coding: utf-8 -*-
"""Helpers purs pour le popup de confirmation après création d'un ticket Jira.

Isolé de la commande Sublime (non testable hors-Sublime). Construit l'URL
« browse » navigateur, déduit le projet depuis la clé, et rend le minihtml.
"""


def build_browse_url(org, key):
    """URL navigateur d'un ticket : https://{org}.atlassian.net/browse/{key}."""
    return "https://{0}.atlassian.net/browse/{1}".format(org, key)


def project_from_key(key):
    """Projet déduit de la clé : préfixe avant le dernier '-'.

    'MMPO-123' -> 'MMPO' ; une clé sans '-' est retournée telle quelle.
    """
    if "-" in key:
        return key.rsplit("-", 1)[0]
    return key


def build_creation_popup_html(key, project, browse_url):
    """minihtml du popup : clé en lien cliquable + projet + indice."""
    return (
        '<body id="alfaco-jira-created">'
        '<style>'
        'body {{ font-family: system, sans-serif; padding: 6px 10px; }}'
        '.key a {{ font-size: 1.2rem; font-weight: bold; text-decoration: none; }}'
        '.project {{ color: color(var(--foreground) alpha(0.7)); margin-top: 4px; }}'
        '.hint {{ color: color(var(--foreground) alpha(0.5)); font-size: 0.85rem; margin-top: 6px; }}'
        '</style>'
        '<div class="key"><a href="{url}">{key}</a></div>'
        '<div class="project">Projet {project}</div>'
        '<div class="hint">Cliquer pour ouvrir dans le navigateur</div>'
        '</body>'
    ).format(url=browse_url, key=key, project=project)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest plugins/AlfacoLib/tests/test_jira_popup.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/jira_popup.py plugins/AlfacoLib/tests/test_jira_popup.py
git commit -m "feat(lib): helpers purs popup création Jira (browse url, projet, minihtml)"
```

---

### Task 2: Helper d'affichage du popup (AlfacoAtlassian)

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/_created_popup.py`

Ce fichier ne déclare aucune classe `*Command` (pas une commande) — juste
une fonction module mutualisée par les deux commandes. Non testable
hors-Sublime (dépend de `view.show_popup` et `webbrowser`), pas de test.

- [ ] **Step 1: Write the implementation**

Créer `plugins/AlfacoAtlassian/commands/_created_popup.py` :

```python
# -*- coding: utf-8 -*-
"""Affiche le popup de confirmation après création d'un ticket Jira.

Mutualisé par create_jira_from_markdown et create_jira_issue. Non testable
hors-Sublime (view.show_popup + webbrowser).
"""
import webbrowser

from AlfacoLib.jira_popup import (
    build_browse_url,
    project_from_key,
    build_creation_popup_html,
)


def show_created_popup(view, org, key):
    """Popup : clé (lien cliquable vers le navigateur) + projet."""
    project = project_from_key(key)
    browse_url = build_browse_url(org, key)
    html = build_creation_popup_html(key, project, browse_url)
    view.show_popup(html, max_width=480, on_navigate=webbrowser.open)
```

- [ ] **Step 2: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/_created_popup.py
git commit -m "feat(atlassian): helper show_created_popup (popup + ouverture navigateur)"
```

---

### Task 3: Brancher le popup dans create_jira_from_markdown

**Files:**
- Modify: `plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py`

Comportement cible : sur succès (HTTP < 400 ET clé extractible) → popup,
pas d'onglet. Sur échec → onglet JSON conservé. La sauvegarde disque reste.

- [ ] **Step 1: Add the import**

En haut du fichier, après `from AlfacoLib.markdown_to_adf import parse_markdown_jira_template`, ajouter :

```python
from AlfacoAtlassian.commands._created_popup import show_created_popup
```

- [ ] **Step 2: Remplacer le bloc « ouverture onglet + sauvegarde » par la logique succès/échec**

Le bloc actuel (à partir de `new_view = self.view.window().new_file()` jusqu'à la fin de `run`) :

```python
        new_view = self.view.window().new_file()
        new_view.set_name(f"Jira response {response.status_code}")
        new_view.run_command("insert", {"characters": response.text})

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            try:
                jira_key = response.json()["key"]
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(
                    f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})"
                )
                sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
            except (KeyError, ValueError):
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (code {response.status_code}) — payload non sauvegardé."
                )
```

devient :

```python
        # Extraction de la clé (succès = HTTP < 400 ET clé présente).
        jira_key = None
        if response.status_code < 400:
            try:
                jira_key = response.json()["key"]
            except (KeyError, ValueError):
                jira_key = None

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            if jira_key:
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(
                    f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})"
                )
            else:
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (code {response.status_code}) — payload non sauvegardé."
                )

        if jira_key:
            org = meta["organisation"] or cfg.get("default_organisation")
            show_created_popup(self.view, org, jira_key)
            sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
        else:
            # Échec : on conserve l'onglet JSON pour diagnostic.
            new_view = self.view.window().new_file()
            new_view.set_name(f"Jira response {response.status_code}")
            new_view.run_command("insert", {"characters": response.text})
```

- [ ] **Step 3: Vérifier la suite de tests existante (non-régression import)**

Run: `pytest plugins/AlfacoLib/tests/ -q`
Expected: PASS (aucune régression ; les commandes ne sont pas testées hors-Sublime mais le module lib l'est).

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py
git commit -m "feat(atlassian): popup au lieu de l'onglet JSON sur succès (Markdown)"
```

---

### Task 4: Brancher le popup dans create_jira_issue

**Files:**
- Modify: `plugins/AlfacoAtlassian/commands/create_jira_issue.py`

Même logique. Ici l'org est toujours `default_organisation` (base_url() sans org).

- [ ] **Step 1: Add the import**

En haut du fichier, après `from AlfacoLib.io import save_file, build_response_path, build_payload_path`, ajouter :

```python
from AlfacoAtlassian.commands._created_popup import show_created_popup
```

- [ ] **Step 2: Remplacer le bloc « ouverture onglet + sauvegarde »**

Le bloc actuel (à partir de `new_view = self.view.window().new_file()` jusqu'à la fin de `run`) :

```python
        new_view = self.view.window().new_file()
        new_view.set_name(f"Jira response {response.status_code}")
        new_view.run_command("insert", {"characters": response.text})

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            try:
                jira_key = response.json()["key"]
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})")
                sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
            except (KeyError, ValueError):
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (probablement échec — code {response.status_code}) "
                    "— payload non sauvegardé."
                )
```

devient :

```python
        # Extraction de la clé (succès = HTTP < 400 ET clé présente).
        jira_key = None
        if response.status_code < 400:
            try:
                jira_key = response.json()["key"]
            except (KeyError, ValueError):
                jira_key = None

        folder = cfg.get("path_json_files_folder")
        if folder:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_file(response.text, build_response_path(folder, timestamp))
            if jira_key:
                save_file(contenu, build_payload_path(folder, jira_key))
                _atlassian_plugin.log.info(f"ticket créé : {jira_key} (payload + réponse sauvegardés dans {folder})")
            else:
                _atlassian_plugin.log.warn(
                    f"Réponse sans 'key' (probablement échec — code {response.status_code}) "
                    "— payload non sauvegardé."
                )

        if jira_key:
            org = cfg.get("default_organisation")
            show_created_popup(self.view, org, jira_key)
            sublime.status_message(f"AlfacoAtlassian : ticket {jira_key} créé")
        else:
            # Échec : on conserve l'onglet JSON pour diagnostic.
            new_view = self.view.window().new_file()
            new_view.set_name(f"Jira response {response.status_code}")
            new_view.run_command("insert", {"characters": response.text})
```

- [ ] **Step 3: Run lib tests**

Run: `pytest plugins/AlfacoLib/tests/ -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/create_jira_issue.py
git commit -m "feat(atlassian): popup au lieu de l'onglet JSON sur succès (JSON)"
```

---

### Task 5: Documentation

**Files:**
- Modify: `docs/plugins/alfaco-atlassian.md`
- Modify: `docs/usage.md`

- [ ] **Step 1: Lire les sections concernées**

Run: `grep -n "onglet\|réponse\|response\|create_jira" docs/plugins/alfaco-atlassian.md docs/usage.md`

Repérer la description du comportement après création (onglet réponse).

- [ ] **Step 2: Mettre à jour la doc**

Remplacer la description « ouvre un onglet avec la réponse » par : sur
succès, un **popup** affiche la clé (lien cliquable → navigateur) et le
projet ; sur échec, l'onglet JSON est conservé pour diagnostic. Adapter au
texte réel trouvé à l'étape 1 (ne pas inventer de formulation absente).

- [ ] **Step 3: Commit**

```bash
git add docs/plugins/alfaco-atlassian.md docs/usage.md
git commit -m "docs(atlassian): popup de confirmation après création (clé + projet)"
```

---

### Task 6: Suite de tests complète + revue finale

- [ ] **Step 1: Run full suite**

Run: `make test`
Expected: PASS (suite existante + 5 nouveaux tests `test_jira_popup.py`).

- [ ] **Step 2: Note de validation manuelle (non bloquante)**

La validation Sublime (popup réel, clic → navigateur) ne peut être faite
hors-Sublime : `make install`, créer un ticket via Alt+M et Alt+J, vérifier
le popup et le clic. Consigner dans le résumé de fin.
