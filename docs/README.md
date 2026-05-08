# Documentation Alfaco

Plugin Sublime Text 3+ pour piloter les API REST d'Atlassian (Jira / Confluence) depuis l'éditeur, avec quelques utilitaires d'édition complémentaires (text-to-table, insertion de date, sélection entre marqueurs).

## Sommaire

### Pour l'utilisateur

| Document | Contenu |
|---|---|
| [installation.md](installation.md) | Pré-requis, installation manuelle dans `Packages/`, dépendance `requests`, première configuration. |
| [usage.md](usage.md) | Workflow Jira complet (sélection organisation → projet → création d'issue), liste exhaustive des commandes, raccourcis clavier par OS, snippets disponibles. |
| [configuration.md](configuration.md) | Référence des trois fichiers de settings, clés disponibles, exemple de `User/alfaco.sublime-settings`, gestion du mot de passe Jira. |

### Pour le développeur / contributeur

| Document | Contenu |
|---|---|
| [architecture.md](architecture.md) | Schéma global, cycle de vie du plugin, rôle de chaque module, modèle d'objet `Configuration`, flux d'un appel REST. |
| [contributing.md](contributing.md) | Comment ajouter une nouvelle commande, convention de nommage Sublime, où l'enregistrer (menu / keymap / palette), style de code, workflow git. |
| [troubleshooting.md](troubleshooting.md) | Bugs connus, dette technique, pièges multi-OS, erreurs Atlassian fréquentes et leur diagnostic. |

## Démarrage rapide

1. Cloner ce dépôt dans le dossier `Packages/Alfaco/` de Sublime Text — voir [installation.md](installation.md).
2. Créer `User/alfaco.sublime-settings` avec un token API Atlassian — voir [configuration.md](configuration.md).
3. Ouvrir un fichier JSON, sélectionner une organisation puis un projet via `Tools → Alfaco`, puis appeler `alt+j` pour POSTer le contenu vers Jira — voir [usage.md](usage.md).

## Statut du projet

- Version package : `0.1.0` (`package-metadata.json`)
- Compatibilité : Sublime Text ≥ 3000 (plugin host Python 3.3 ou 3.8)
- Plateformes ciblées : `*` (mais le code contient des chemins Windows codés en dur — voir [troubleshooting.md](troubleshooting.md))
- Langue du code, des commentaires et de l'UI : **français**
