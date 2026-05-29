# Start date + Organisation dans le flux Markdown → Jira

- **Date** : 2026-05-29
- **Statut** : design approuvé, prêt pour planification d'implémentation
- **Branche cible** : `feat/jira-startdate-organisation`
- **Auteur** : brainstorming Alfaco

## Contexte

Le flux Markdown → Jira (`init_markdown_jira` → snippet `jira.sublime-snippet-markdown` → `create_jira_from_markdown`, cf. [2026-05-27-markdown-to-jira-design.md](2026-05-27-markdown-to-jira-design.md)) couvre aujourd'hui `Summary`, `Project`, `Type`, `Priority`, `Labels`, `Duedate`, `Description`.

Le champ `Startdate` avait été ajouté initialement puis **retiré en PR #20** : il était envoyé sous le nom `startdate`, qui n'est pas un champ Jira standard (il correspond à un *custom field* propre à chaque instance), ce qui provoquait des `400`. On le réintroduit ici **correctement**, via l'id de custom field réel.

Par ailleurs, le template ne porte aucune information de **routage** : la création POST toujours vers `default_organisation` (le site `*.atlassian.net` choisi via `select_organisation`). On veut pouvoir fixer le site directement dans le Markdown.

### Custom field « Start date »

Identifié sur l'instance via l'API Jira (`getJiraIssueTypeMetaWithFields`, projet GDP / type Tâche) :

| Nom | Clé | Type | Requis |
|---|---|---|---|
| Start date | `customfield_10015` | `date` (datepicker) | non |

Format payload identique à `duedate` : `"customfield_10015": "YYYY-MM-DD"`. Les ids de custom field pouvant varier d'une instance à l'autre, l'id est **configurable** (cf. §Settings) et non codé en dur.

## Objectifs

1. Réintroduire **Start date** dans le template Markdown, mappé sur le custom field configurable (défaut `customfield_10015`), pré-rempli à la date du jour, **non obligatoire**.
2. Ajouter **Organisation** au template : routage du POST vers un site Atlassian donné. Défaut = organisation courante (`default_organisation`), vide si rien n'est choisi.
3. **Priorité au Markdown** : si `# Organisation` est renseigné, il l'emporte sur `default_organisation` au moment du POST.
4. Ne **pas** casser le flux JSON (`init_json_jira` / `create_jira_issue` / `jira.sublime-snippet`) ni l'API publique du parser au-delà du strict nécessaire.

## Non-objectifs

- Pas de nouveau champ « espace » : « espace » = le projet Jira, déjà porté par `# Project` (défaut = `project_key` courant, Markdown prioritaire — comportement inchangé).
- Pas de commande « sélectionner une organisation dans le template » ni de validation que l'`url_key` existe dans `atlassian.organisations` (l'API renverra une erreur réseau explicite si le site est faux).
- Pas de mapping label → `url_key` : l'organisation est référencée par son **`url_key`** (cohérent avec `default_organisation` et `base_url()`).
- Pas de fallback « date du jour » côté parser pour Start date : le défaut est livré par le pré-remplissage du template, pas par le parser (champ réellement optionnel).
- Pas de dépendance pip externe (contrainte plugin host ST4 : `urllib` only).

## Format du template

### Champs réservés (mise à jour)

| Champ | Obligatoire | Fallback parser | Type | Cible payload |
|---|---|---|---|---|
| `# Summary` | oui | — | string mono-ligne | `fields.summary` |
| `# Organisation` | non | — (omis si vide) | string (`url_key`) | **routage** — pas dans `fields` |
| `# Project` | non | `config.project_key` | string (clé Jira) | `fields.project.key` |
| `# Type` | non | `Task` | string | `fields.issuetype.name` |
| `# Priority` | non | `High` | string | `fields.priority.name` |
| `# Labels` | non | `["important", "urgent"]` | CSV → liste | `fields.labels` |
| `# Startdate` | non | — (omis si vide) | `YYYY-MM-DD` | `fields.<jira_startdate_field>` |
| `# Duedate` | non | aujourd'hui + 10 j | `YYYY-MM-DD` | `fields.duedate` |
| `# Description` | oui | — | Markdown → ADF | `fields.description` |

Le découpage en champs reste basé sur le regex existant `^#\s+(\w+)\s*$` (un seul mot) : `Organisation` et `Startdate` sont des mots simples, compatibles sans modifier le regex.

### Exemple

```markdown
# Summary
Préparer la migration du poste de travail

# Organisation
business-projects

# Project
GDP

# Type
Task

# Priority
High

# Labels
important, urgent

# Startdate
2026-05-29

# Duedate
2026-06-08

# Description
Étapes :

- sauvegarde
- réinstallation
```

## Architecture & flux de données

```
init_markdown_jira              create_jira_from_markdown
  pré-remplit le snippet :        text du buffer
   - organisation = default_org      │
   - startdate    = aujourd'hui      ▼
   - duedate      = J+10        parse_markdown_jira_template(text, defaults)
   - jira_key     = project_key      │   defaults: project_key, duedate, type,
        │                            │            priority, labels, startdate_field
        ▼                            ▼
  buffer Markdown            (payload, meta)
                                  │        │
                       {"fields":{…}}   {"organisation": "<url_key|''>"}
                                  │        │
                                  ▼        ▼
                       url = cfg.base_url(org=meta["organisation"] or None) + "issue/"
                                  │
                                  ▼
                              call_rest POST
```

### Décision d'archi : retour `(payload, meta)`

`# Organisation` est du **routage**, pas un champ du payload. `parse_markdown_jira_template` retourne donc un **tuple** `(payload, meta)` :

- `payload` : `{"fields": {...}}` (inchangé dans sa forme).
- `meta` : `{"organisation": "<url_key>" | ""}`.

*Alternative rejetée* : ranger l'organisation sous une clé réservée `payload["_organisation"]` que la commande `pop()` avant POST. Évite de changer la signature mais pollue le dict envoyé et expose à un `400` si le `pop` est oublié. Le tuple est plus explicite et garde la fonction pure/testable.

## Détail par composant

### 1. `AlfacoLib/markdown_to_adf.py`

- `KNOWN_FIELDS` += `"Organisation"`, `"Startdate"`.
- `parse_markdown_jira_template(text, defaults)` retourne `(payload, meta)` :
  - **Organisation** : `org = (fields_md.get("Organisation") or "").strip()` → `meta = {"organisation": org}`. Jamais ajoutée à `fields`.
  - **Start date** : `sd = (fields_md.get("Startdate") or "").strip()` ; `sd_field = defaults.get("startdate_field", "")`. Si `sd` **et** `sd_field` non vides → `fields[sd_field] = sd`. Sinon, champ **omis**.
  - `# Project`, `# Summary`, `# Description`, etc. : inchangés.
- Docstring mise à jour (nouveau type de retour + nouveaux `defaults`).

### 2. `AlfacoLib/config.py`

`base_url(self, version=None, org=None)` : si `org` est fourni et non vide, l'utiliser à la place de `self.get("default_organisation")`. Aucun effet de bord (pas de `set`). Signature rétro-compatible (`org` optionnel, défaut `None`).

### 3. `AlfacoAtlassian/commands/create_jira_from_markdown.py`

- `defaults["startdate_field"] = cfg.get("jira_startdate_field", "customfield_10015")`.
- **Pas** de clé `startdate` dans `defaults` (optionnel).
- `payload, meta = parse_markdown_jira_template(text, defaults)`.
- `url = cfg.base_url(org=meta["organisation"] or None) + "issue/"` — Markdown prioritaire sur le site.
- Reste inchangé (log, POST, buffer réponse, sauvegarde).

### 4. `AlfacoAtlassian/commands/init_markdown_jira.py`

- `args["organisation"] = _atlassian_plugin.config.get("default_organisation", "")` (vide si rien choisi).
- `args["startdate"] = today.strftime("%Y-%m-%d")`.
- `duedate`, `jira_key` : inchangés.

### 5. Snippet `snippets/jira/jira.sublime-snippet-markdown`

Ajout de deux sections (avant `# Description`, qui capture jusqu'à EOF) :

```
# Organisation
${organisation}

...

# Startdate
${startdate}
```

Le snippet du flux JSON (`jira.sublime-snippet`) n'est **pas** modifié.

### 6. Settings

`alfaco-atlassian.sublime-settings` (defaults) **et** `templates/User/alfaco-atlassian.sublime-settings` :

```jsonc
// Custom field Jira pour la date de début (Start date).
// Varie selon l'instance ; vide ("") = ne jamais envoyer Start date.
"jira_startdate_field": "customfield_10015",
```

## Tests (`AlfacoLib/tests/test_markdown_to_adf.py`, TDD)

Adapter les tests existants au retour tuple (`payload, meta = parse_markdown_jira_template(...)`), puis ajouter :

1. Start date présente + `startdate_field` défini → `fields["customfield_10015"] == "<valeur MD>"`.
2. Start date absente → clé custom field absente de `fields`.
3. Start date présente mais `startdate_field == ""` → clé absente de `fields` (réglage désactivé).
4. `# Organisation` renseignée → `meta["organisation"] == "<url_key>"` et **pas** de clé organisation dans `fields`.
5. `# Organisation` absente → `meta["organisation"] == ""`.
6. `base_url(org="autre-site")` → URL sur `autre-site`, sans muter `default_organisation` ; `base_url()` (sans `org`) → comportement d'origine.

Les commandes `*Command` ne sont pas testables hors-Sublime (logique pure déjà extraite dans le parser / `config`).

## Documentation à mettre à jour

- `docs/plugins/alfaco-atlassian.md` : liste des champs réservés (ajouter `Organisation`, `Startdate`), tableau du workflow Markdown, mention de `customfield_10015` / `jira_startdate_field`.
- `docs/usage.md` : section « Variante Markdown » (citer Organisation + Startdate).
- `docs/configuration.md` : documenter `jira_startdate_field`.

## Risques / points d'attention

- **Id de custom field** : `customfield_10015` est valide sur cette instance ; le réglage `jira_startdate_field` couvre les autres instances. Ne **pas** recoder en dur (régression PR #20).
- **Start date hors écran** : si le custom field n'est pas sur l'écran de création d'un projet donné, Jira peut renvoyer un `400`. Comportement assumé (le message d'erreur s'affiche dans le buffer réponse) ; l'utilisateur vide alors `# Startdate`.
- **Organisation invalide** : `url_key` inconnu → erreur réseau/`404` explicite, pas de garde-fou côté plugin (non-objectif).
