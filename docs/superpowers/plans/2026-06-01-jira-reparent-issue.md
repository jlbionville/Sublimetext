# Re-parenter un ticket existant — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter une commande `reparent_jira_issue` qui demande la clé d'un ticket existant, propose les Epics/Stories du projet courant (popup), et déplace le ticket sous le parent choisi via `PUT /issue/{KEY}`.

**Architecture:** Édition d'un ticket existant, indépendante du flux Markdown. Aucune nouvelle logique pure : on réutilise `parse_parent_choices` (AlfacoLib, déjà testé en #1) et le pattern `search` JQL + garde-fous de `select_jira_parent`. Une seule commande TextCommand enchaîne input panel → popup parent → PUT. Succès = HTTP 204 (corps vide, ne pas parser en JSON).

**Tech Stack:** Python 3.8 (host Sublime Text 4), `urllib` stdlib, fichiers `.sublime-keymap`/`.sublime-menu`. Pas de nouveau test pytest (commande non testable hors-Sublime).

**Contraintes projet :** code/commentaires/captions en **français** ; une commande = un fichier dans `commands/` importée dans `plugin.py` ; mettre à jour **les 3 keymaps OS** ; commits fréquents ; pas de `--no-verify`. `PUT /issue/{KEY}` renvoie 204 sans corps → ne jamais appeler `response.json()` sur le succès.

---

## File Structure

- **Create** `plugins/AlfacoAtlassian/commands/reparent_jira_issue.py` — `ReparentJiraIssueCommand`.
- **Modify** `plugins/AlfacoAtlassian/plugin.py` — import de la commande.
- **Modify** `plugins/AlfacoAtlassian/Context.sublime-menu` — entrée clic droit.
- **Modify** `plugins/AlfacoAtlassian/Main.sublime-menu` — entrée Tools.
- **Modify** `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap` — chord `ctrl+j ctrl+m`.
- **Modify** `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap` — chord `ctrl+j ctrl+m`.
- **Modify** `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap` — chord `super+j super+m`.
- **Modify** `docs/plugins/alfaco-atlassian.md`, `docs/usage.md` — doc.

---

## Task 1 : commande `reparent_jira_issue`

Pas de test unitaire (TextCommand + input panel non testables hors-Sublime). On réutilise
`parse_parent_choices` déjà couvert par des tests en #1. Validation manuelle (Task 4).

**Files:**
- Create: `plugins/AlfacoAtlassian/commands/reparent_jira_issue.py`
- Modify: `plugins/AlfacoAtlassian/plugin.py`

- [ ] **Step 1 : créer le fichier de commande**

Créer `plugins/AlfacoAtlassian/commands/reparent_jira_issue.py` avec EXACTEMENT :

```python
# -*- coding: utf-8 -*-
"""Déplace un ticket existant sous un parent (Epic/Story) via PUT /issue/{KEY}.

Flux : input panel (clé du ticket) → popup des Epics/Stories du projet courant
(réutilise parse_parent_choices + jira_parent_types) → PUT du champ `parent`.
Un PUT réussi renvoie 204 No Content (corps vide) : on ne parse pas de JSON.
"""
import json as _json
import socket
from urllib.error import URLError
from urllib.parse import quote

import sublime
import sublime_plugin

from AlfacoAtlassian import plugin as _atlassian_plugin
from AlfacoLib.atlassian_client import call_rest, parse_parent_choices


class ReparentJiraIssueCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        cfg = _atlassian_plugin.config

        self._project_key = cfg.get("project_key", "")
        if not self._project_key:
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

        window = self.view.window()
        window.show_input_panel(
            "Clé du ticket à déplacer :", "", self._on_issue_key, None, None
        )

    def _on_issue_key(self, issue_key):
        issue_key = issue_key.strip()
        if not issue_key:
            _atlassian_plugin.log.info("re-parentage annulé (clé vide)")
            return
        self._issue_key = issue_key

        cfg = _atlassian_plugin.config
        login, password = cfg.jira_auth()
        types = cfg.get("jira_parent_types", ["Epic", "Story"])
        clause = ", ".join('"%s"' % t for t in types)
        jql = 'project = "%s" AND issuetype in (%s) ORDER BY created DESC' % (self._project_key, clause)
        url = cfg.base_url() + "search?jql=" + quote(jql)
        _atlassian_plugin.log.info(f"GET {url} (user={login})")
        sublime.status_message(f"AlfacoAtlassian : récupération parents ({self._project_key})…")

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
                f"AlfacoAtlassian : aucune Epic/Story trouvée pour {self._project_key}."
            )
            return

        labels = [label for _, label in self._choices]
        _atlassian_plugin.log.info(f"{len(labels)} parent(s) prêts pour le popup")
        sublime.status_message(f"AlfacoAtlassian : {len(labels)} parent(s)")
        self.view.show_popup_menu(labels, self._on_parent_done)

    def _on_parent_done(self, index):
        if index == -1:
            _atlassian_plugin.log.info("sélection parent annulée")
            return
        parent_key = self._choices[index][0]
        cfg = _atlassian_plugin.config
        payload = _json.dumps(
            {"fields": {"parent": {"key": parent_key}}}, ensure_ascii=False
        )
        url = cfg.base_url() + "issue/" + self._issue_key
        headers = cfg.get(
            "headers", {"Content-type": "application/json", "Accept": "application/json"}
        )
        _atlassian_plugin.log.info(f"PUT {url} parent={parent_key}")
        sublime.status_message(f"AlfacoAtlassian : PUT {self._issue_key} → parent {parent_key}…")

        try:
            response = call_rest(
                url,
                body=payload,
                auth=cfg.jira_auth(),
                headers=headers,
                verb="PUT",
                verify=cfg.get("tls_verify", True),
            )
        except (URLError, socket.timeout) as e:
            _atlassian_plugin.log.error(f"erreur réseau sur {url} : {e}")
            sublime.error_message(
                f"AlfacoAtlassian : impossible de joindre {url}\n\n{e}"
            )
            return

        if response.status_code < 400:
            _atlassian_plugin.log.info(
                f"PUT {url} → {response.status_code} : {self._issue_key} rattaché à {parent_key}"
            )
            sublime.status_message(
                f"AlfacoAtlassian : {self._issue_key} rattaché à {parent_key}"
            )
        else:
            _atlassian_plugin.log.error(
                f"PUT {url} → {response.status_code} : {response.text[:300]}"
            )
            sublime.error_message(
                f"AlfacoAtlassian : le déplacement a échoué.\n\n"
                f"HTTP {response.status_code}\n{response.text[:500]}"
            )
```

- [ ] **Step 2 : enregistrer la commande dans plugin.py**

Dans `plugins/AlfacoAtlassian/plugin.py`, après la dernière ligne d'import de commande
(celle de `select_jira_parent`), ajouter :

```python
from AlfacoAtlassian.commands.reparent_jira_issue import ReparentJiraIssueCommand  # noqa: E402, F401
```

(Lire le fichier d'abord pour confirmer l'ordre ; placer après l'import `select_jira_parent`.)

- [ ] **Step 3 : vérifier la syntaxe Python**

Run: `cd /mnt/c/workspace/depots/Sublimetext && python3 -c "import ast; ast.parse(open('plugins/AlfacoAtlassian/commands/reparent_jira_issue.py').read()); ast.parse(open('plugins/AlfacoAtlassian/plugin.py').read()); print('OK')"`
Expected: `OK`.

- [ ] **Step 4 : suite verte (non-régression)**

Run: `cd /mnt/c/workspace/depots/Sublimetext && make test`
Expected: PASS (106 — aucun nouveau test, aucune régression).

- [ ] **Step 5 : commit**

```bash
git add plugins/AlfacoAtlassian/commands/reparent_jira_issue.py plugins/AlfacoAtlassian/plugin.py
git commit -m "feat(atlassian): reparent_jira_issue (déplace un ticket sous un parent)"
```

---

## Task 2 : intégration UI (menus + 3 keymaps)

**Files:**
- Modify: `plugins/AlfacoAtlassian/Context.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Main.sublime-menu`
- Modify: `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`
- Modify: `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`

- [ ] **Step 1 : menu contextuel (Context.sublime-menu)**

Fichier JSON strict. Le tableau `children` se termine actuellement par l'entrée
`{ "caption": "choisir le parent (Epic/Story)", "command": "select_jira_parent" }` (dernier
élément, sans virgule finale). Ajouter une virgule à cette ligne puis une nouvelle entrée :

```json
            { "caption": "choisir le parent (Epic/Story)", "command": "select_jira_parent" },
            { "caption": "déplacer un ticket sous un parent", "command": "reparent_jira_issue" }
```

- [ ] **Step 2 : menu Tools (Main.sublime-menu)**

Dans le `children` du nœud `alfaco-atlassian`, la ligne
`{ "caption": "Choisir le parent (Epic/Story)", "command": "select_jira_parent" },` est
suivie de `{ "caption": "Open Jira projects (debug)", "command": "open_jira_projects" }`
(dernière entrée). Insérer ENTRE les deux :

```json
                            { "caption": "Déplacer un ticket sous un parent", "command": "reparent_jira_issue" },
```

(« Open Jira projects (debug) » reste dernier, sans virgule finale.)

- [ ] **Step 2bis : combler le manque OSX `select_jira_issue_type` (réparation)**

Constat connu (revue #1) : le keymap OSX n'a PAS la liaison `super+j super+t` →
`select_jira_issue_type` que Linux/Windows ont. Tant qu'on édite les 3 keymaps, on corrige.
Dans `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`, après la ligne
`{ "keys": ["super+j", "super+r"], "command": "select_jira_parent" }` (lire le fichier pour
confirmer la dernière entrée et sa virgule), ajouter la liaison manquante. Si `super+j
super+t` est absent, l'ajouter aussi. Résultat attendu : OSX contient à la fois
`super+j super+t` → `select_jira_issue_type` ET `super+j super+m` → `reparent_jira_issue`
(voir Step 5). Garder le JSON valide.

> Si la vérification montre que `super+j super+t` est en fait déjà présent, ne rien ajouter
> ici et le noter dans le rapport.

- [ ] **Step 3 : keymap Linux**

Dans `plugins/AlfacoAtlassian/Default (Linux).sublime-keymap`, après la ligne
`{ "keys": ["ctrl+j", "ctrl+r"], "command": "select_jira_parent" },` ajouter :

```json
    { "keys": ["ctrl+j", "ctrl+m"], "command": "reparent_jira_issue" },
```

- [ ] **Step 4 : keymap Windows**

Dans `plugins/AlfacoAtlassian/Default (Windows).sublime-keymap`, après la ligne
`{ "keys": ["ctrl+j", "ctrl+r"], "command": "select_jira_parent" },` ajouter la même ligne :

```json
    { "keys": ["ctrl+j", "ctrl+m"], "command": "reparent_jira_issue" },
```

- [ ] **Step 5 : keymap OSX**

Dans `plugins/AlfacoAtlassian/Default (OSX).sublime-keymap`, ajouter (après la liaison
`select_jira_parent` / la liaison `super+j super+t` ajoutée au Step 2bis) :

```json
    { "keys": ["super+j", "super+m"], "command": "reparent_jira_issue" },
```

Veiller à ce que la dernière entrée du tableau n'ait pas de virgule traînante.

- [ ] **Step 6 : valider le JSON des 5 fichiers + occurrences**

Run:
```bash
cd /mnt/c/workspace/depots/Sublimetext
python3 -c "import json; [json.load(open(f)) for f in ['plugins/AlfacoAtlassian/Context.sublime-menu','plugins/AlfacoAtlassian/Main.sublime-menu','plugins/AlfacoAtlassian/Default (Linux).sublime-keymap','plugins/AlfacoAtlassian/Default (Windows).sublime-keymap','plugins/AlfacoAtlassian/Default (OSX).sublime-keymap']]; print('JSON OK')"
for f in "plugins/AlfacoAtlassian/Context.sublime-menu" "plugins/AlfacoAtlassian/Main.sublime-menu" "plugins/AlfacoAtlassian/Default (Linux).sublime-keymap" "plugins/AlfacoAtlassian/Default (Windows).sublime-keymap" "plugins/AlfacoAtlassian/Default (OSX).sublime-keymap"; do printf "%s -> %s\n" "$(basename "$f")" "$(grep -c reparent_jira_issue "$f")"; done
```
Expected: `JSON OK` et chaque fichier `-> 1`. (Les 5 fichiers sont du JSON strict sans commentaires.)

- [ ] **Step 7 : commit**

```bash
git add "plugins/AlfacoAtlassian/Context.sublime-menu" "plugins/AlfacoAtlassian/Main.sublime-menu" "plugins/AlfacoAtlassian/Default (Linux).sublime-keymap" "plugins/AlfacoAtlassian/Default (Windows).sublime-keymap" "plugins/AlfacoAtlassian/Default (OSX).sublime-keymap"
git commit -m "feat(atlassian): menus + raccourci Ctrl+J Ctrl+M pour reparent_jira_issue (+ fix OSX issue_type)"
```

---

## Task 3 : documentation

**Files:**
- Modify: `docs/plugins/alfaco-atlassian.md`
- Modify: `docs/usage.md`

- [ ] **Step 1 : documenter la commande dans alfaco-atlassian.md**

Dans `docs/plugins/alfaco-atlassian.md`, table « Commandes », après la ligne
`select_jira_parent`, ajouter :

```markdown
| `reparent_jira_issue` | Demande la clé d'un ticket existant (input panel), propose les Epics/Stories du projet (popup), puis déplace le ticket sous le parent choisi (`PUT /issue/{KEY}` avec `parent`). |
```

Dans la table « Raccourcis », après la ligne `Ctrl+J Ctrl+R … select_jira_parent`, ajouter :

```markdown
| `Ctrl+J Ctrl+M` / `Cmd+J Cmd+M` | tous | `reparent_jira_issue` (déplace un ticket existant sous un parent) |
```

- [ ] **Step 2 : usage.md**

Dans `docs/usage.md`, section « Index des commandes » → « AlfacoAtlassian », ajouter
`reparent_jira_issue` à la liste inline (après `select_jira_parent`), en conservant le
format séparé par virgules et le point final.

Dans la sous-section « Variante Markdown », après la puce « Rattacher à un parent », ajouter :

```markdown
   - *Déplacer un ticket existant* : `reparent_jira_issue` (`Ctrl+J Ctrl+M`) demande la clé d'un ticket déjà créé et le rattache à une Epic/Story choisie dans un popup.
```

- [ ] **Step 3 : commit**

```bash
git add docs/plugins/alfaco-atlassian.md docs/usage.md
git commit -m "docs(atlassian): documenter reparent_jira_issue + raccourci Ctrl+J Ctrl+M"
```

---

## Task 4 : validation manuelle dans Sublime (humain)

Non automatisable. À réaliser après `make install`.

- [ ] `make install` puis redémarrer Sublime.
- [ ] `select_organisation` + `select_jira_project` (poser org + projet, ex. MMPO).
- [ ] `Ctrl+J Ctrl+M` → input panel « Clé du ticket à déplacer : » → saisir une clé existante non-parent (ex. une Tâche `MMPO-3`) → Entrée.
- [ ] Popup des Epics/Stories du projet → choisir une Epic (ex. `MMPO-2`).
- [ ] Message de succès « `MMPO-3` rattaché à `MMPO-2` » ; vérifier dans Jira que le parent est posé.
- [ ] ⚠️ Si le GET parents renvoie 410/404 : basculer `search?jql=` → `search/jql` dans `reparent_jira_issue.py` (et idéalement dans `select_jira_parent.py` aussi) — même réserve qu'en #1.
- [ ] Clé inexistante (ex. `MMPO-9999`) → message d'erreur HTTP explicite (404).
- [ ] Input vide (juste Entrée) → rien ne se passe (annulation silencieuse).
- [ ] Sans projet courant : `Ctrl+J Ctrl+M` affiche « aucun projet courant ».
- [ ] Vérifier menu clic droit + `Tools → Alfaco → Atlassian` contiennent « Déplacer un ticket sous un parent ».

---

## Self-Review (auteur du plan)

- **Couverture du spec** : commande input→popup→PUT (T1) ✓ ; réutilise `parse_parent_choices`
  + `jira_parent_types` ✓ ; 204 traité comme succès sans `.json()` (`status_code < 400`,
  pas de parse) ✓ ; garde-fous réseau/HTTP/JSON sur le GET parents ✓ ; menus + 3 keymaps
  `Ctrl+J Ctrl+M` (T2) ✓ ; docs (T3) ✓ ; validation manuelle dont réserve `search/jql` (T4) ✓.
  Réparation hors-scope mais opportune : liaison OSX `select_jira_issue_type` manquante
  (T2 step 2bis) — corrigée pendant qu'on édite les keymaps (signalée en revue #1).
- **Placeholders** : aucun — code complet. Les Steps qui demandent de « lire le fichier »
  (ordre d'import, dernière entrée OSX) fournissent quand même la ligne exacte à insérer.
- **Cohérence des types** : `parse_parent_choices(data) -> [(key, label)]` ; le popup affiche
  `label`, garde `parent_key = self._choices[index][0]` ; payload
  `{"fields": {"parent": {"key": parent_key}}}` ; verbe `PUT` sur `issue/<self._issue_key>` ;
  succès = `status_code < 400` (couvre 204). `self._project_key` / `self._issue_key` /
  `self._choices` portés entre les 3 callbacks de la même instance de commande.
