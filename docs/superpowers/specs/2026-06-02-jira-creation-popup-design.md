# Popup de confirmation après création d'un ticket Jira

Date : 2026-06-02
Plugin : AlfacoAtlassian (+ helpers purs dans AlfacoLib)

## Problème

Après création d'un ticket Jira, les deux commandes
(`create_jira_from_markdown` — Alt+M — et `create_jira_issue` — Alt+J)
ouvrent systématiquement un nouvel onglet contenant le JSON brut de la
réponse. Cet onglet est bruyant : l'information utile (la clé du ticket,
son projet, un lien pour l'ouvrir) est noyée dans le payload de réponse.

## Objectif

Sur **succès**, remplacer l'onglet par un **popup** affichant la clé du
ticket et son projet, la clé étant un **lien cliquable** qui ouvre le
ticket dans le navigateur. Sur **échec**, conserver le comportement
actuel (onglet JSON) pour le diagnostic.

## Comportement

| Cas | Aujourd'hui | Demain |
|---|---|---|
| **Succès** (HTTP < 400 ET clé présente) | onglet JSON ouvert | **popup** « MMPO-123 — Projet MMPO », clé = lien cliquable → navigateur ; **aucun onglet** |
| **Échec** (HTTP ≥ 400 ou pas de clé) | onglet JSON | onglet JSON **conservé** (inchangé) |

- **Lien cliquable** : `https://{org}.atlassian.net/browse/{clé}`. Le clic
  déclenche `webbrowser.open(url)` via le callback `on_navigate` de
  `view.show_popup`.
- **Projet** : dérivé du préfixe de la clé (`MMPO-123` → `MMPO`). Robuste
  car la réponse de création Jira contient toujours `key` ; elle ne
  contient pas les champs de projet.
- **Org** : `meta["organisation"] or default_organisation` pour le flux
  Markdown ; `default_organisation` pour le flux JSON. Cohérent avec
  l'organisation utilisée pour le POST.
- **Sauvegarde disque** (`path_json_files_folder`) : inchangée dans les
  deux cas (réponse toujours sauvegardée ; payload sauvegardé sur succès).

## Découpage

Pour rester testable hors-Sublime (les classes `*Command` ne le sont
pas), on isole la logique pure dans AlfacoLib.

### `AlfacoLib/jira_popup.py` (pur, testé)

- `build_browse_url(org, key)` → `https://{org}.atlassian.net/browse/{key}`.
- `build_creation_popup_html(key, project, browse_url)` → minihtml :
  clé rendue en `<a href="{browse_url}">{key}</a>`, ligne « Projet {project} »,
  et un indice « Cliquer pour ouvrir ».
- `project_from_key(key)` → préfixe avant le dernier `-` (`MMPO-123` →
  `MMPO`) ; tolère une clé sans `-` (retourne la clé telle quelle).

### `AlfacoAtlassian/commands/_created_popup.py` (non testable)

Helper mutualisé `show_created_popup(view, org, key)` :
1. `project = project_from_key(key)`
2. `browse_url = build_browse_url(org, key)`
3. `html = build_creation_popup_html(key, project, browse_url)`
4. `view.show_popup(html, max_width=480, on_navigate=webbrowser.open)`

Ce n'est pas une commande (pas de classe `*Command`) — juste une fonction
module, importée par les deux commandes. Respecte la règle « 1 commande =
1 fichier » (ce fichier ne déclare aucune commande).

### Les deux commandes

Après le POST :
- **succès** (`status_code < 400` et clé extractible) →
  `show_created_popup(self.view, org, key)` au lieu de `window().new_file()`.
- **échec** → onglet JSON comme aujourd'hui.

La sauvegarde disque existante reste en place.

## Tests (hors-Sublime, `AlfacoLib/tests/`)

- `build_browse_url("mysite", "MMPO-123")` == `https://mysite.atlassian.net/browse/MMPO-123`.
- `project_from_key("MMPO-123")` == `"MMPO"` ; `project_from_key("ABC")` == `"ABC"`.
- `build_creation_popup_html(...)` contient la clé, le projet et le `href` (browse_url).

## Hors périmètre (YAGNI)

- Pas de configuration du contenu/format du popup.
- Pas de bouton « copier la clé » ni d'autres actions que l'ouverture navigateur.
- Pas de changement de la sauvegarde disque ni du flux d'erreur.
