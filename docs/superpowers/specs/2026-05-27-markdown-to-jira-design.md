# Création de tickets Jira depuis Markdown

- **Date** : 2026-05-27
- **Statut** : design approuvé, prêt pour planification d'implémentation
- **Branche cible** : `feat/markdown-to-jira` (depuis `development`)
- **Auteur** : brainstorming Alfaco

## Contexte

Le flux actuel de création de ticket Jira passe par un buffer JSON brut (`init_json_jira` → snippet `jira.sublime-snippet` → `create_jira_issue`). Le contenu est du JSON pré-formaté, ce qui force l'utilisateur à composer avec :

- Une syntaxe non naturelle pour rédiger une description longue avec listes, sous-sections, code, liens.
- Aucune mise en forme visible côté éditeur (pas de rendu Markdown).
- L'API Jira v3 qui exige `description` en Atlassian Document Format (ADF) — déjà partiellement résolu par `wrap_description_as_adf` (pull request #15) qui transforme automatiquement les strings plates en paragraphe ADF unique, mais sans support de listes, headings, code, etc.

## Objectifs

1. Permettre la rédaction des tickets en **Markdown** (format naturel, rendu correct dans tout éditeur).
2. **Convertir** automatiquement le Markdown en payload Jira complet (champs structurés + description ADF riche).
3. **Réutiliser** l'infrastructure existante (`call_rest`, `Configuration`, logger, `init_json_jira` UX) sans la casser.
4. **Symétrie** avec le flux JSON : deux commandes parallèles, deux raccourcis, même expérience.

## Non-objectifs

- Pas d'éditeur WYSIWYG ni de rendu Markdown en preview dans Sublime.
- Pas de support exhaustif du Markdown : tables, images, blockquotes, listes imbriquées, strikethrough sont hors-scope MVP (cf. §Limites).
- Pas de remplacement du flux JSON existant : les deux coexistent. Un utilisateur peut continuer à utiliser `init_json_jira` + `create_jira_issue` s'il préfère.
- Pas de dépendance pip externe (contrainte plugin host ST4 : `urllib` only, comme `atlassian_client`).
- Pas de migration de l'API v2 vers v3 : on lit `api_rest_version`. Pour v3 (défaut du template) on génère de l'ADF. Pour v2 on envoie la description en string brute (le Markdown lui-même) — Jira v2 affiche du texte (rendu imparfait) ou interprète son wiki markup propre selon la configuration de l'instance. La conversion MD → wiki markup Atlassian est hors-scope MVP.

## Format du template

### Règles

Le template est un fichier Markdown avec **headings h1 (`#`) comme délimiteurs de champs**. Les noms de champs sont réservés. Tout ce qui n'est pas un champ reconnu avant `# Description` est une erreur. Tout ce qui suit `# Description` (jusqu'à EOF) est interprété en Markdown ADF.

### Champs réservés

| Champ | Obligatoire | Fallback | Type |
|---|---|---|---|
| `# Summary` | oui | — | string mono-ligne |
| `# Project` | non | `config.project_key` | string (clé Jira ex. `SDAL`) |
| `# Type` | non | `Task` | string |
| `# Priority` | non | `High` | string |
| `# Labels` | non | `["important", "urgent"]` | CSV → liste de strings |
| `# Startdate` | non | aujourd'hui | `YYYY-MM-DD` |
| `# Duedate` | non | aujourd'hui + 10 jours | `YYYY-MM-DD` |
| `# Description` | oui | — | Markdown (h2+ libres) |

### Exemple

```markdown
# Summary
Developper l'automatisation copy writing

# Project
SDAL

# Type
Task

# Priority
High

# Labels
important, urgent

# Startdate
2026-05-27

# Duedate
2026-06-06

# Description

Comme Wilfried mais avec un SEO approprié.

## Critères

- doc rendue
- 3 articles publiés

Voir [doc Atlassian](https://docs.atlassian.com).

​```python
print("hello")
​```
```

### Comportements de validation

- `# UnknownField` avant `# Description` → erreur explicite (`error_message` listant les champs reconnus) + log `error`, POST avorté.
- `# Summary` absent ou vide → erreur, POST avorté.
- `# Description` absent → erreur, POST avorté.
- Champ `Project` qui résout sur une valeur vide (template sans `# Project` ET `config.project_key` vide) → erreur, POST avorté.
- `Labels` parsé en `[s.strip() for s in csv.split(",") if s.strip()]`.
- `Startdate` / `Duedate` non-`YYYY-MM-DD` → warn, valeur passée telle quelle (Jira valide).

## Conversion Markdown → ADF

### Features supportées MVP

| Markdown | ADF node |
|---|---|
| `# h1` à `###### h6` (dans body Description uniquement) | `heading` `attrs.level=N` |
| Paragraphe (séparé par ligne vide) | `paragraph` |
| `- item`, `* item`, `+ item` | `bulletList > listItem > paragraph` |
| `1. item`, `2. item`, … | `orderedList > listItem > paragraph` |
| `**bold**` ou `__bold__` | mark `strong` |
| `*italic*` ou `_italic_` | mark `em` |
| `` `code inline` `` | mark `code` |
| ` ```lang\n…\n``` ` | `codeBlock` `attrs.language=lang` |
| `[text](url)` | mark `link` `attrs.href=url` |

### Limites (non-supporté MVP, fallback texte)

- Tables Markdown (` | a | b | `) → texte brut.
- Images (`![alt](url)`) → texte brut.
- Blockquotes (`> …`) → texte brut.
- Listes imbriquées (`  - item`) → 1er niveau seulement, indentation perdue.
- Strikethrough (`~~text~~`) → texte brut.
- Soft line breaks dans paragraphe → joint avec espace.
- **Marks imbriquées** (`**bold *italic***`) → la mark la plus extérieure gagne (le contenu intérieur est traité comme un seul `text` node). Mix séquentiel OK (`**bold** et *italic*`).

En cas de feature non supportée, le parser laisse le texte tel quel dans un `text` node (pas de plantage). Documenté dans la spec.

### Structure ADF générée

Document racine :
```json
{
    "type": "doc",
    "version": 1,
    "content": [<liste de nodes top-level>]
}
```

Nodes top-level autorisés : `paragraph`, `heading`, `bulletList`, `orderedList`, `codeBlock`.

## Workflow utilisateur

| Étape | Action |
|---|---|
| 1 | `Ctrl+Alt+M` (Linux/Win) / `Cmd+Alt+M` (Mac) → `init_markdown_jira` : nouveau buffer scratch `.md`, template inséré, dates + `project_key` auto-remplis, syntax = Markdown |
| 2 | Remplir les champs. `Tab` navigue summary → description (placeholders du snippet) |
| 3 | `Alt+M` (Linux/Win) / `Cmd+Shift+M` (Mac) → `create_jira_from_markdown` : parse le buffer, valide, convertit, POST |
| 4 | Buffer `Jira response NNN` s'ouvre avec la réponse Jira (comme `create_jira_issue` actuel) |

L'utilisateur peut sauvegarder le `.md` localement (workflow porté hors-Sublime).

## Architecture

### Module pur : `AlfacoLib/markdown_to_adf.py`

Une fonction publique principale :

```python
def parse_markdown_jira_template(text: str, defaults: dict) -> dict:
    """Parse un template Markdown en payload Jira complet (prêt à POST).

    Args:
        text: contenu Markdown du buffer.
        defaults: valeurs de fallback ({"project_key", "startdate", "duedate",
            "type", "priority", "labels"}).

    Returns:
        Payload {"fields": {...}} avec description en ADF.

    Raises:
        ValueError: champ obligatoire absent, champ inconnu, etc.
    """
```

Helpers internes :

- `_split_fields(text) -> dict[str, str]` : découpe sur les `# H1`, renvoie `{field_name: body}`.
- `_markdown_to_adf(md_body: str) -> dict` : transforme le body Markdown en doc ADF.
- `_parse_block(lines: list[str]) -> list[node]` : paragraphe, heading, liste, code block.
- `_parse_inline(text: str) -> list[node]` : marks (strong, em, code, link).

Module **pur**, **testable hors-Sublime**, **sans import sublime**. Réutilisable.

### Commandes : `plugins/AlfacoAtlassian/commands/`

- **`init_markdown_jira.py`** (`InitMarkdownJiraCommand`, `TextCommand`)
  - Ouvre `window().new_file()`, set syntax Markdown.
  - Insère le snippet `jira.sublime-snippet-markdown` avec args `{project_key, startdate, duedate}`.
  - Logs `[INFO]`, status_message.

- **`create_jira_from_markdown.py`** (`CreateJiraFromMarkdownCommand`, `TextCommand`)
  - Lit le buffer entier.
  - Appelle `parse_markdown_jira_template(text, defaults)` ; sur `ValueError` → `error_message` + log `error` + return.
  - Sérialise en JSON, POST via `call_rest`.
  - Mêmes logs/status/buffer réponse que `create_jira_issue`.
  - Sauvegarde réponse + payload dans `path_json_files_folder` si défini (réutilise `save_file`, `build_response_path`, `build_payload_path`).

### Snippet : `plugins/AlfacoAtlassian/snippets/jira/jira.sublime-snippet-markdown`

```xml
<snippet>
    <content><![CDATA[
# Summary
${1:à compléter}

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
</snippet>
```

Pas de `tabTrigger` ni `scope` : on l'insère via la commande (pas auto-complétion).

### Keymaps (3 OS)

| Plateforme | Touches | Commande |
|---|---|---|
| Linux | `ctrl+alt+m` | `init_markdown_jira` |
| Linux | `alt+m` | `create_jira_from_markdown` |
| Windows | `ctrl+alt+m` | `init_markdown_jira` |
| Windows | `alt+m` | `create_jira_from_markdown` |
| macOS | `super+alt+m` | `init_markdown_jira` |
| macOS | `super+shift+m` | `create_jira_from_markdown` |

### Menus

- **`Main.sublime-menu`** : ajouter sous Tools → Alfaco → Atlassian :
  - `Initialiser Markdown Jira` → `init_markdown_jira`
  - `Créer ticket Jira (depuis Markdown)` → `create_jira_from_markdown`
- **`Context.sublime-menu`** : ajouter `créer ticket Jira (Markdown)` → `create_jira_from_markdown`. Pas de filtrage par scope (la commande valide elle-même que le buffer est bien un template Markdown via la présence de `# Summary` / `# Description`).

### Plugin entry-point : `plugins/AlfacoAtlassian/plugin.py`

Ajouter les 2 imports en fin de fichier (pour que Sublime découvre les classes) :

```python
from AlfacoAtlassian.commands.init_markdown_jira import InitMarkdownJiraCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.create_jira_from_markdown import CreateJiraFromMarkdownCommand  # noqa: E402, F401
```

## Tests

### TDD pour `markdown_to_adf.py`

Fichier `plugins/AlfacoLib/tests/test_markdown_to_adf.py`. ~15 tests minimum :

1. **Découpage en champs**
   - 8 champs présents → dict avec 8 entrées.
   - Champ `Description` capture jusqu'à EOF (y compris h2+).
   - Champ inconnu avant Description → ValueError.

2. **Conversion inline (marks)**
   - `**bold**` → `strong`.
   - `*italic*` → `em`.
   - `` `code` `` → `code`.
   - `[text](url)` → `link` avec href.
   - Combinaison `**bold** et *italic*` → mix correct.

3. **Conversion block**
   - Paragraphe simple → `paragraph`.
   - `## heading` → `heading` level 2.
   - `- item\n- item` → `bulletList` 2 items.
   - `1. item\n2. item` → `orderedList` 2 items.
   - ` ```python\nprint()\n``` ` → `codeBlock` avec `attrs.language=python`.

4. **Validation et fallbacks**
   - Pas de `# Summary` → ValueError.
   - Pas de `# Description` → ValueError.
   - Pas de `# Project` + defaults sans `project_key` → ValueError.
   - Labels CSV `"a, b ,c"` → `["a", "b", "c"]`.
   - Startdate manquante → defaults["startdate"].

5. **Intégration**
   - Template complet → payload `{"fields": {...}}` correct, description ADF complète.

### Commandes (non testables hors-Sublime)

`init_markdown_jira` et `create_jira_from_markdown` ne sont pas couvertes par pytest (import `sublime_plugin`). Validation manuelle dans Sublime.

## Documentation

- `docs/plugins/alfaco-atlassian.md` : nouvelle sous-section "Workflow Markdown" + ajout dans le tableau Raccourcis.
- `CLAUDE.md` : ligne dans la section "What this is" (le plugin AlfacoAtlassian supporte deux flux : JSON et Markdown).
- Template d'exemple `plugins/AlfacoAtlassian/snippets/jira/jira-markdown-example.md` (non déployé, dans `templates/`) si utile pour onboarding.

## Risques et mitigations

| Risque | Mitigation |
|---|---|
| Parser MD bogué sur un edge case (description corrompue) | TDD strict, tests sur fragments réels. Fallback : texte brut dans paragraph (jamais de plantage). |
| Ordre Description en dernier oublié par l'utilisateur | Validation : si champ reconnu trouvé après `# Description` → ValueError explicite. |
| Conflit raccourci `Alt+M` avec menu système | Documenté ; user peut override via User keymap. |
| Buffer non-Markdown invoqué par erreur via `Alt+M` | Validation : si pas de `# Summary` ou `# Description` → ValueError explicite. |
| ADF non accepté pour champ paginé/complex (`customfield_…`) | Hors-scope MVP. Le user édite le payload JSON s'il a besoin de custom fields. |

## Suivi

- PR à ouvrir : `feat/markdown-to-jira` → `development` → `main` (workflow standard).
- Tag `markdown-jira-v0.1.0` après merge si validation manuelle OK.
- Issue de suivi possible : support des listes imbriquées (v0.2.0).
