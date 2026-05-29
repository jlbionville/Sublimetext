# Start date + Organisation (flux Markdown → Jira) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Réintroduire le champ Jira *Start date* (custom field configurable, défaut `customfield_10015`) dans le template Markdown — pré-rempli à aujourd'hui, optionnel — et ajouter une métadonnée *Organisation* qui route le POST vers un site Atlassian donné (Markdown prioritaire sur `default_organisation`).

**Architecture:** `parse_markdown_jira_template` passe d'un retour `{"fields": {...}}` à un tuple `(payload, meta)` où `meta = {"organisation": "<url_key|''>"}` ; l'organisation est du routage, jamais un champ du payload. `config.base_url` accepte un paramètre `org` pour surcharger le site sans muter la config. La commande `create_jira_from_markdown` consomme `meta` pour construire l'URL et injecte l'id de custom field (`jira_startdate_field`) dans `defaults`.

**Tech Stack:** Python 3.8 (plugin host Sublime Text 4), `pytest` hors-Sublime (stubs `sublime`/`sublime_plugin` via `conftest.py`), `urllib` stdlib (pas de `requests`).

**Spec:** `docs/superpowers/specs/2026-05-29-jira-startdate-organisation-design.md`

---

## Notes de coordination (lire avant de commencer)

- **Branche** : `feat/jira-startdate-organisation` (déjà créée depuis `main`, contient le commit du spec).
- **Recouvrement avec le PR #23** (non mergé au moment de l'écriture) : le PR #23 ajoute la section « Variante Markdown » à `docs/usage.md` et corrige `docs/troubleshooting.md`. Cette branche partant de `main`, ces changements n'y sont pas. La **Task 9** (docs) en tient compte explicitement : si le PR #23 est déjà mergé quand on traite la Task 9, on **édite** la section existante ; sinon on la **crée**. Si possible, merger le PR #23 puis `git rebase main` cette branche **avant** la Task 9 pour éviter un conflit.
- **Commandes Sublime non testables hors-Sublime** : les fichiers `commands/*.py` ne sont pas couverts par `pytest` (cf. `CLAUDE.md`). Les Tasks 5–7 fournissent le code exact + une vérification manuelle dans Sublime (Task 10).

## File Structure

| Fichier | Responsabilité | Action |
|---|---|---|
| `plugins/AlfacoLib/config.py` | `base_url(version, org)` — surcharge du site | Modifier |
| `plugins/AlfacoLib/tests/test_config.py` | tests `base_url` | Modifier |
| `plugins/AlfacoLib/markdown_to_adf.py` | parser : `KNOWN_FIELDS`, retour `(payload, meta)`, start date, organisation | Modifier |
| `plugins/AlfacoLib/tests/test_markdown_to_adf.py` | tests parser | Modifier |
| `plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py` | unpack tuple, `startdate_field`, routage org | Modifier |
| `plugins/AlfacoAtlassian/commands/init_markdown_jira.py` | pré-remplissage `organisation` + `startdate` | Modifier |
| `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown` | sections `# Organisation` + `# Startdate` | Modifier |
| `plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings` | défaut `jira_startdate_field` | Modifier |
| `plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings` | doc du réglage `jira_startdate_field` | Modifier |
| `docs/plugins/alfaco-atlassian.md`, `docs/configuration.md`, `docs/usage.md` | documentation | Modifier |

---

## Task 1: `config.base_url` accepte un paramètre `org`

**Files:**
- Modify: `plugins/AlfacoLib/config.py:39-42`
- Test: `plugins/AlfacoLib/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Ajouter à la fin de `plugins/AlfacoLib/tests/test_config.py` :

```python
def test_base_url_org_override_takes_precedence():
    cfg = Configuration([])
    cfg.set("default_organisation", "default-site")
    cfg.set("api_rest_version", "3")
    assert cfg.base_url(org="autre-site") == "https://autre-site.atlassian.net/rest/api/3/"
    # pas d'effet de bord : la config n'est pas mutée
    assert cfg.base_url() == "https://default-site.atlassian.net/rest/api/3/"


def test_base_url_org_empty_falls_back_to_default():
    cfg = Configuration([])
    cfg.set("default_organisation", "default-site")
    cfg.set("api_rest_version", "2")
    assert cfg.base_url(org="") == "https://default-site.atlassian.net/rest/api/2/"
    assert cfg.base_url(org=None) == "https://default-site.atlassian.net/rest/api/2/"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest plugins/AlfacoLib/tests/test_config.py::test_base_url_org_override_takes_precedence -v`
Expected: FAIL avec `TypeError: base_url() got an unexpected keyword argument 'org'`

- [ ] **Step 3: Write minimal implementation**

Remplacer la méthode `base_url` dans `plugins/AlfacoLib/config.py` :

```python
    def base_url(self, version=None, org=None):
        organisation = org if org else self.get("default_organisation")
        ver = version if version is not None else self.get("api_rest_version", "2")
        return f"https://{organisation}.atlassian.net/rest/api/{ver}/"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest plugins/AlfacoLib/tests/test_config.py -v`
Expected: PASS (tous, y compris les `test_base_url_*` existants)

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/config.py plugins/AlfacoLib/tests/test_config.py
git commit -m "feat(config): base_url(org=…) pour surcharger le site Atlassian"
```

---

## Task 2: Ajouter `Organisation` et `Startdate` à `KNOWN_FIELDS`

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py:153-156`
- Test: `plugins/AlfacoLib/tests/test_markdown_to_adf.py:234-260`

- [ ] **Step 1: Mettre à jour les tests existants**

Dans `plugins/AlfacoLib/tests/test_markdown_to_adf.py`, remplacer `test_known_fields_constants` :

```python
def test_known_fields_constants():
    """Les 9 champs réservés du template (Organisation = routage, Startdate optionnel)."""
    assert KNOWN_FIELDS == [
        "Summary", "Organisation", "Project", "Type", "Priority", "Labels",
        "Startdate", "Duedate", "Description",
    ]
```

Puis remplacer `test_split_fields_all_fields` pour inclure les deux nouveaux champs :

```python
def test_split_fields_all_fields():
    template = (
        "# Summary\nS\n\n"
        "# Organisation\nmon-site\n\n"
        "# Project\nPRJ\n\n"
        "# Type\nTask\n\n"
        "# Priority\nHigh\n\n"
        "# Labels\nimportant, urgent\n\n"
        "# Startdate\n2026-05-29\n\n"
        "# Duedate\n2026-06-06\n\n"
        "# Description\nbody"
    )
    result = _split_fields(template)
    assert set(result.keys()) == set(KNOWN_FIELDS)
    assert result["Labels"] == "important, urgent"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py::test_known_fields_constants -v`
Expected: FAIL (KNOWN_FIELDS ne contient pas encore Organisation/Startdate)

- [ ] **Step 3: Write minimal implementation**

Remplacer `KNOWN_FIELDS` dans `plugins/AlfacoLib/markdown_to_adf.py` :

```python
KNOWN_FIELDS = [
    "Summary", "Organisation", "Project", "Type", "Priority", "Labels",
    "Startdate", "Duedate", "Description",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -k "known_fields or split_fields" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown): Organisation + Startdate dans KNOWN_FIELDS"
```

---

## Task 3: `parse_markdown_jira_template` retourne `(payload, meta)` avec l'organisation

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py:199-256`
- Test: `plugins/AlfacoLib/tests/test_markdown_to_adf.py` (tests existants + nouveaux)

- [ ] **Step 1: Adapter les tests existants au tuple + ajouter les tests organisation**

Dans `plugins/AlfacoLib/tests/test_markdown_to_adf.py`, remplacer les trois tests qui déballent le retour :

```python
def test_parse_full_template_returns_payload_with_adf():
    template = (
        "# Summary\nDevelopper feature\n\n"
        "# Description\nLe contexte.\n\n- item 1\n- item 2"
    )
    payload, meta = parse_markdown_jira_template(template, _DEFAULTS)
    fields = payload["fields"]
    assert fields["summary"] == "Developper feature"
    assert fields["project"] == {"key": "SDAL"}
    assert fields["issuetype"] == {"name": "Task", "subtask": False}
    assert fields["priority"] == {"name": "High"}
    assert fields["labels"] == ["important", "urgent"]
    assert fields["duedate"] == "2026-06-06"
    assert fields["description"]["type"] == "doc"
    assert len(fields["description"]["content"]) == 2
    assert meta == {"organisation": ""}


def test_parse_template_overrides_defaults():
    template = (
        "# Summary\nS\n# Project\nFOO\n# Type\nBug\n# Priority\nLow\n"
        "# Labels\na, b\n# Duedate\n2026-01-10\n"
        "# Description\nbody"
    )
    payload, meta = parse_markdown_jira_template(template, _DEFAULTS)
    fields = payload["fields"]
    assert fields["project"] == {"key": "FOO"}
    assert fields["issuetype"] == {"name": "Bug", "subtask": False}
    assert fields["priority"] == {"name": "Low"}
    assert fields["labels"] == ["a", "b"]
    assert fields["duedate"] == "2026-01-10"


def test_parse_template_labels_csv_split():
    template = (
        "# Summary\nS\n\n# Labels\nfoo,  bar ,baz  \n\n"
        "# Description\nbody"
    )
    payload, meta = parse_markdown_jira_template(template, _DEFAULTS)
    assert payload["fields"]["labels"] == ["foo", "bar", "baz"]
```

Puis ajouter les nouveaux tests organisation :

```python
def test_parse_organisation_present_goes_to_meta_not_fields():
    template = (
        "# Summary\nS\n\n# Organisation\nmon-site\n\n"
        "# Description\nbody"
    )
    payload, meta = parse_markdown_jira_template(template, _DEFAULTS)
    assert meta == {"organisation": "mon-site"}
    assert "organisation" not in payload["fields"]
    assert "Organisation" not in payload["fields"]


def test_parse_organisation_absent_is_empty_string():
    template = "# Summary\nS\n\n# Description\nbody"
    payload, meta = parse_markdown_jira_template(template, _DEFAULTS)
    assert meta["organisation"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py::test_parse_organisation_present_goes_to_meta_not_fields -v`
Expected: FAIL avec `ValueError: too many values to unpack` ou `TypeError` (la fonction retourne encore un dict)

- [ ] **Step 3: Write minimal implementation**

Remplacer `parse_markdown_jira_template` dans `plugins/AlfacoLib/markdown_to_adf.py` (docstring + retour tuple ; **pas encore** la start date) :

```python
def parse_markdown_jira_template(text, defaults):
    """Parse un template Markdown Jira en `(payload, meta)`.

    Args:
        text: contenu Markdown du template (cf. spec pour le format).
        defaults: dict avec `project_key`, `duedate`, `type`, `priority`,
            `labels`, `startdate_field` utilisés comme fallback / config.

    Returns:
        Tuple `(payload, meta)` :
            payload: `{"fields": {...}}` prêt à JSON-dump et POST (API v3, ADF).
            meta: `{"organisation": "<url_key>" | ""}` — routage, hors payload.

    Raises:
        ValueError: champ obligatoire absent, champ inconnu, project_key
            non résolu.
    """
    fields_md = _split_fields(text)

    summary = fields_md.get("Summary", "").strip()
    if not summary:
        raise ValueError("Champ `# Summary` obligatoire et non vide.")

    description_md = fields_md.get("Description")
    if description_md is None:
        raise ValueError("Champ `# Description` obligatoire.")

    project_key = fields_md.get("Project") or defaults.get("project_key", "")
    if not project_key:
        raise ValueError(
            "`# Project` absent et `project_key` non défini dans la config. "
            "Utiliser `Tools → Alfaco → Atlassian → Sélectionner projet Jira` "
            "ou ajouter `# Project\\n<KEY>` au template."
        )

    issue_type = fields_md.get("Type") or defaults.get("type", "Task")
    priority = fields_md.get("Priority") or defaults.get("priority", "High")

    labels_csv = fields_md.get("Labels")
    if labels_csv:
        labels = [s.strip() for s in labels_csv.split(",") if s.strip()]
    else:
        labels = list(defaults.get("labels", []))

    duedate = fields_md.get("Duedate") or defaults.get("duedate", "")

    fields = {
        "summary": summary,
        "description": _markdown_to_adf(description_md),
        "duedate": duedate,
        "issuetype": {"name": issue_type, "subtask": False},
        "project": {"key": project_key},
        "priority": {"name": priority},
        "labels": labels,
    }

    organisation = (fields_md.get("Organisation") or "").strip()

    return {"fields": fields}, {"organisation": organisation}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: PASS (tous)

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown): parse retourne (payload, meta) avec organisation de routage"
```

---

## Task 4: Start date optionnelle via custom field configurable

**Files:**
- Modify: `plugins/AlfacoLib/markdown_to_adf.py` (fonction `parse_markdown_jira_template`)
- Test: `plugins/AlfacoLib/tests/test_markdown_to_adf.py` (`_DEFAULTS` + nouveaux tests)

- [ ] **Step 1: Ajouter `startdate_field` à `_DEFAULTS` et écrire les tests start date**

Dans `plugins/AlfacoLib/tests/test_markdown_to_adf.py`, remplacer la constante `_DEFAULTS` (haut du fichier) :

```python
_DEFAULTS = {
    "project_key": "SDAL",
    "duedate": "2026-06-06",
    "type": "Task",
    "priority": "High",
    "labels": ["important", "urgent"],
    "startdate_field": "customfield_10015",
}
```

Puis ajouter les tests start date :

```python
def test_parse_startdate_present_uses_configured_custom_field():
    template = (
        "# Summary\nS\n\n# Startdate\n2026-05-29\n\n# Description\nbody"
    )
    payload, _ = parse_markdown_jira_template(template, _DEFAULTS)
    assert payload["fields"]["customfield_10015"] == "2026-05-29"


def test_parse_startdate_absent_field_omitted():
    template = "# Summary\nS\n\n# Description\nbody"
    payload, _ = parse_markdown_jira_template(template, _DEFAULTS)
    assert "customfield_10015" not in payload["fields"]
    assert "startdate" not in payload["fields"]


def test_parse_startdate_present_but_field_disabled_is_omitted():
    template = (
        "# Summary\nS\n\n# Startdate\n2026-05-29\n\n# Description\nbody"
    )
    defaults_no_field = dict(_DEFAULTS)
    defaults_no_field["startdate_field"] = ""
    payload, _ = parse_markdown_jira_template(template, defaults_no_field)
    assert "customfield_10015" not in payload["fields"]


def test_parse_startdate_empty_value_omitted():
    template = "# Summary\nS\n\n# Startdate\n\n\n# Description\nbody"
    payload, _ = parse_markdown_jira_template(template, _DEFAULTS)
    assert "customfield_10015" not in payload["fields"]
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py::test_parse_startdate_present_uses_configured_custom_field -v`
Expected: FAIL avec `KeyError: 'customfield_10015'`

- [ ] **Step 3: Write minimal implementation**

Dans `parse_markdown_jira_template`, **insérer** le bloc start date entre la construction de `fields` et le calcul de `organisation` :

```python
    fields = {
        "summary": summary,
        "description": _markdown_to_adf(description_md),
        "duedate": duedate,
        "issuetype": {"name": issue_type, "subtask": False},
        "project": {"key": project_key},
        "priority": {"name": priority},
        "labels": labels,
    }

    startdate = (fields_md.get("Startdate") or "").strip()
    startdate_field = defaults.get("startdate_field", "")
    if startdate and startdate_field:
        fields[startdate_field] = startdate

    organisation = (fields_md.get("Organisation") or "").strip()

    return {"fields": fields}, {"organisation": organisation}
```

- [ ] **Step 4: Run the full parser suite**

Run: `pytest plugins/AlfacoLib/tests/test_markdown_to_adf.py -v`
Expected: PASS (tous)

- [ ] **Step 5: Commit**

```bash
git add plugins/AlfacoLib/markdown_to_adf.py plugins/AlfacoLib/tests/test_markdown_to_adf.py
git commit -m "feat(markdown): Start date optionnelle via custom field configurable"
```

---

## Task 5: `create_jira_from_markdown` consomme `meta` + `startdate_field`

**Files:**
- Modify: `plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py:24-42`

> Non testable hors-Sublime (commande `*Command`). Vérification manuelle en Task 10.

- [ ] **Step 1: Injecter `startdate_field` dans `defaults`, déballer le tuple, router l'org**

Remplacer le bloc `defaults = {...}` jusqu'à la ligne `url = cfg.base_url() + "issue/"` dans `plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py` par :

```python
        today = datetime.now()
        defaults = {
            "project_key": cfg.get("project_key", ""),
            "duedate": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "type": "Task",
            "priority": "High",
            "labels": ["important", "urgent"],
            "startdate_field": cfg.get("jira_startdate_field", "customfield_10015"),
        }

        try:
            payload, meta = parse_markdown_jira_template(text, defaults)
        except ValueError as e:
            _atlassian_plugin.log.error(f"parse_markdown_jira_template : {e}")
            sublime.error_message(f"AlfacoAtlassian (Markdown) : {e}")
            return

        contenu = _json.dumps(payload, ensure_ascii=False, indent=4)
        url = cfg.base_url(org=meta["organisation"] or None) + "issue/"
```

(Le reste de la méthode — `headers`, `call_rest`, buffer réponse, sauvegarde — est inchangé.)

- [ ] **Step 2: Vérifier la cohérence (lint d'import)**

Run: `python3 -c "import ast; ast.parse(open('plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py').read())"`
Expected: aucune sortie (syntaxe valide)

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/create_jira_from_markdown.py
git commit -m "feat(atlassian): create_jira_from_markdown route l'org + start date configurable"
```

---

## Task 6: `init_markdown_jira` pré-remplit Organisation + Startdate

**Files:**
- Modify: `plugins/AlfacoAtlassian/commands/init_markdown_jira.py:18-24`

> Non testable hors-Sublime. Vérification manuelle en Task 10.

- [ ] **Step 1: Ajouter les args `organisation` et `startdate`**

Remplacer le bloc qui construit `args` (de `today = datetime.now()` jusqu'à `args["jira_key"] = ...`) dans `plugins/AlfacoAtlassian/commands/init_markdown_jira.py` par :

```python
        today = datetime.now()
        args.setdefault(
            "name",
            "Packages/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown",
        )
        args["organisation"] = _atlassian_plugin.config.get("default_organisation", "")
        args["startdate"] = today.strftime("%Y-%m-%d")
        args["duedate"] = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        args["jira_key"] = _atlassian_plugin.config.get("project_key", "")
```

- [ ] **Step 2: Vérifier la syntaxe**

Run: `python3 -c "import ast; ast.parse(open('plugins/AlfacoAtlassian/commands/init_markdown_jira.py').read())"`
Expected: aucune sortie

- [ ] **Step 3: Commit**

```bash
git add plugins/AlfacoAtlassian/commands/init_markdown_jira.py
git commit -m "feat(atlassian): init_markdown_jira pré-remplit organisation + startdate"
```

---

## Task 7: Snippet — sections `# Organisation` et `# Startdate`

**Files:**
- Modify: `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown`

> Non testable hors-Sublime. Vérification manuelle en Task 10.

- [ ] **Step 1: Remplacer le contenu du snippet**

Remplacer **tout** le fichier `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown` par :

```xml
<snippet>
	<content><![CDATA[
# Summary
${1:à compléter}

# Organisation
${organisation}

# Project
${jira_key}

# Type
Task

# Priority
High

# Labels
important, urgent

# Startdate
${startdate}

# Duedate
${duedate}

# Description

${2:à compléter}
$0
]]></content>
	<!-- Pas de tabTrigger : insertion via la commande init_markdown_jira uniquement. -->
</snippet>
```

- [ ] **Step 2: Vérifier que c'est du XML bien formé**

Run: `python3 -c "import xml.dom.minidom as m; m.parse('plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown'); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add "plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown"
git commit -m "feat(atlassian): snippet Markdown avec Organisation + Startdate"
```

---

## Task 8: Réglage `jira_startdate_field` (defaults + template User)

**Files:**
- Modify: `plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings`
- Modify: `plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings`

- [ ] **Step 1: Ajouter le défaut dans `alfaco-atlassian.sublime-settings`**

Remplacer la ligne `"default_organisation": "",` par :

```json
    "default_organisation": "",
    "jira_startdate_field": "customfield_10015",
```

- [ ] **Step 2: Documenter le réglage dans le template User**

Dans `plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings`, insérer juste **après** le bloc `"tls_verify": true,` (ligne 36) et **avant** le commentaire `// === Persistance...` :

```jsonc

    // === Champ Start date ===

    // Custom field Jira utilisé pour la date de début (Start date).
    // Cet id varie selon l'instance Jira ; sur l'instance de référence
    // c'est `customfield_10015`. Laisser vide ("") pour ne JAMAIS envoyer
    // Start date (le champ du template Markdown sera alors ignoré).
    "jira_startdate_field": "customfield_10015",
```

- [ ] **Step 3: Vérifier que les deux fichiers se chargent (JSON / JSONC)**

Run: `python3 -c "import json; json.load(open('plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings')); print('defaults ok')"`
Expected: `defaults ok`
(Le template User contient des commentaires JSONC — non parsable en JSON strict ; vérifier visuellement l'équilibre des accolades.)

- [ ] **Step 4: Commit**

```bash
git add plugins/AlfacoAtlassian/alfaco-atlassian.sublime-settings plugins/AlfacoAtlassian/templates/User/alfaco-atlassian.sublime-settings
git commit -m "feat(atlassian): réglage jira_startdate_field (défaut customfield_10015)"
```

---

## Task 9: Documentation

**Files:**
- Modify: `docs/plugins/alfaco-atlassian.md`
- Modify: `docs/configuration.md`
- Modify: `docs/usage.md`

> **Coordination PR #23** : si le PR #23 est mergé et la branche rebasée, `docs/usage.md` contient déjà une section « Variante Markdown » → on l'**édite** (Step 3a). Sinon → on la **crée** (Step 3b). Vérifier d'abord : `grep -n "Variante Markdown" docs/usage.md`.

- [ ] **Step 1: `alfaco-atlassian.md` — champs réservés + référence des clés**

Dans `docs/plugins/alfaco-atlassian.md`, remplacer la phrase « Champs réservés : … » (section *Workflow Markdown*) par :

```markdown
Champs réservés : `Summary`, `Organisation`, `Project`, `Type`, `Priority`, `Labels`, `Startdate`, `Duedate`, `Description`. Un `# UnknownField` produit une erreur explicite. `Summary` et `Description` sont obligatoires ; les autres ont des fallbacks (`project_key` courant, today + 10 jours, etc.). `# Organisation` (= `url_key` du site Atlassian) ne fait pas partie du payload : il **route** le POST et l'emporte sur `default_organisation`. `# Startdate` (date du jour pré-remplie, optionnelle) est envoyée sur le custom field `jira_startdate_field` (défaut `customfield_10015`) ; vide ou réglage désactivé → champ non envoyé.
```

Puis, dans le tableau « Référence des clés », ajouter une ligne après celle de `default_organisation` :

```markdown
| `jira_startdate_field` | string | `"customfield_10015"` | Custom field Jira pour Start date (varie selon l'instance ; vide = désactivé). |
```

- [ ] **Step 2: `configuration.md` — documenter le réglage**

Dans `docs/configuration.md`, repérer la section/clé des réglages AlfacoAtlassian et ajouter (sous la même forme que les autres entrées du fichier) :

```markdown
- `jira_startdate_field` (string, défaut `"customfield_10015"`) — custom field Jira pour la date de début (Start date) du flux Markdown. L'id varie selon l'instance ; laisser vide (`""`) désactive l'envoi de Start date.
```

- [ ] **Step 3a: `usage.md` — SI la section « Variante Markdown » existe déjà (post-#23)**

Dans la liste de la section « Variante Markdown » de `docs/usage.md`, remplacer la puce « Rédiger » par :

```markdown
2. **Rédiger** — corps en Markdown (headings, listes, **emphase**, `code`, liens, blocs de code). Champs réservés via `# Summary`, `# Organisation` (site Atlassian, prioritaire sur `default_organisation`), `# Project`, `# Type`, `# Priority`, `# Labels`, `# Startdate` (date du jour, optionnelle → `customfield_10015`), `# Duedate`, `# Description`.
```

- [ ] **Step 3b: `usage.md` — SINON (PR #23 pas encore mergé)**

Ne pas dupliquer le travail du PR #23. Ajouter seulement, à la fin de la section « Workflow Jira typique (AlfacoAtlassian) », un court paragraphe :

```markdown
Le flux Markdown (`init_markdown_jira` / `create_jira_from_markdown`) accepte en plus `# Organisation` (route le POST vers un autre site Atlassian, prioritaire sur `default_organisation`) et `# Startdate` (date du jour pré-remplie, optionnelle, envoyée sur `customfield_10015` via le réglage `jira_startdate_field`).
```

- [ ] **Step 4: Commit**

```bash
git add docs/plugins/alfaco-atlassian.md docs/configuration.md docs/usage.md
git commit -m "docs: Organisation + Start date dans le flux Markdown Jira"
```

---

## Task 10: Vérification finale (suite complète + validation Sublime)

**Files:** aucun (vérification)

- [ ] **Step 1: Lancer toute la suite de tests**

Run: `make test`
Expected: PASS, 0 échec. (La suite passe d'environ 83 à ~90 tests avec les nouveaux cas.)

- [ ] **Step 2: Déployer dans Sublime**

Run: `make install`
Expected: copie sans erreur. Redémarrer Sublime Text (ou recharger le plugin en sauvegardant `plugins/AlfacoAtlassian/plugin.py`).

- [ ] **Step 3: Vérifier `init_markdown_jira`**

Dans Sublime : `Tools → Alfaco → Atlassian → Initialiser Markdown Jira` (ou `Ctrl+Alt+M` Linux).
Attendu : un buffer Markdown contient `# Organisation` pré-rempli avec l'org courante (vide si aucune `select_organisation`), `# Startdate` à la date du jour, `# Duedate` à J+10, `# Project` = projet courant.

- [ ] **Step 4: Vérifier la création avec Start date**

Sélectionner un projet (`select_jira_project`), remplir `# Summary` et `# Description`, garder `# Startdate` à aujourd'hui, puis `create_jira_from_markdown` (`Alt+M`).
Attendu : réponse `201`, ticket créé, **Start date renseignée** à aujourd'hui dans Jira (vérifier sur l'issue). Le buffer payload sauvegardé contient `"customfield_10015": "<aujourd'hui>"`.

- [ ] **Step 5: Vérifier l'optionnalité + le routage org**

a. Supprimer la section `# Startdate` (ou vider sa valeur) → re-créer → attendu : pas d'erreur, ticket créé sans Start date.
b. Mettre dans `# Organisation` un `url_key` différent de `default_organisation` → attendu : le POST cible bien `https://<url_key>.atlassian.net/...` (visible dans le log info `POST <url>` ; activer `"debug": true`).

- [ ] **Step 6: Mettre à jour les suivis et clôturer**

Vérifier qu'aucun `git status` ne laisse de fichier non commité, puis suivre la skill `superpowers:finishing-a-development-branch` (PR vers `main`).

---

## Self-Review

- **Spec coverage** :
  - Objectif 1 (Start date custom field, pré-rempli, optionnel) → Tasks 4, 6, 7, 8 ✔
  - Objectif 2 (Organisation, défaut = courant, vide sinon) → Tasks 3, 6, 7 ✔
  - Objectif 3 (Markdown prioritaire sur le site) → Tasks 1, 3, 5 ✔
  - Objectif 4 (ne pas casser flux JSON / API parser au-delà du nécessaire) → snippet JSON intact (Task 7 ne touche que `*-markdown`) ; retour tuple répercuté sur l'unique appelant (Task 5) ✔
  - « espace » = `# Project` inchangé → aucune tâche (volontaire) ✔
  - Settings `jira_startdate_field` → Task 8 ✔
  - Tests spec §Tests (6 cas) → Tasks 1 (base_url ×2), 3 (org ×2), 4 (start date ×4) ✔
  - Docs → Task 9 ✔
- **Placeholder scan** : aucun TBD/TODO ; tout step de code montre le code complet.
- **Type consistency** : `base_url(version=None, org=None)` (Task 1) ↔ appel `base_url(org=meta["organisation"] or None)` (Task 5) ✔ ; retour `(payload, meta)` avec `meta["organisation"]` (Tasks 3/4) ↔ unpack `payload, meta` (Task 5) ✔ ; `defaults["startdate_field"]` (Task 4) ↔ `cfg.get("jira_startdate_field", ...)` (Task 5) ↔ setting `jira_startdate_field` (Task 8) ✔ ; snippet vars `${organisation}`/`${startdate}` (Task 7) ↔ `args["organisation"]`/`args["startdate"]` (Task 6) ✔.
