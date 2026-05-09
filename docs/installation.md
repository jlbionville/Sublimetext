# Installation

## Pré-requis

- **Sublime Text 4** (plugin host Python 3.8). ST3 (Python 3.3) n'est plus supporté.
- **Python ≥ 3.8** sur la machine de dev (pour `make` / pytest).
- **Compte Atlassian** + token API (https://id.atlassian.com/manage-profile/security/api-tokens) pour utiliser AlfacoAtlassian.

Aucune dépendance Python tierce côté plugin host (le client REST utilise `urllib`, livré avec Python).

## Installation en mode développeur (recommandé)

```bash
git clone https://github.com/jlbionville/Sublimetext.git
cd Sublimetext
make link              # symlinks plugins/* → <Packages>/  (Linux/macOS)
# OU
make install           # copie plugins/* → <Packages>/    (WSL/Windows)
```

`make link` modifie en direct ; `make install` copie (à relancer après chaque modif). Voir [deployment.md](deployment.md) pour les détails multi-OS.

## Installation utilisateur

Si vous voulez juste utiliser les plugins sans modifier le code :

```bash
git clone https://github.com/jlbionville/Sublimetext.git
cd Sublimetext
make install
```

## Première configuration

1. Ouvrir `Preferences → Package Settings → AlfacoAtlassian → Settings – User`.
2. Coller au minimum :

```json
{
    "jira_login": "votre.email@domaine.tld",
    "jira_password": "ATATT3xFfGF0…",
    "default_organisation": "votre-org",
    "api_rest_version": "3",
    "path_json_files_folder": "/chemin/absolu/dossier/jira"
}
```

3. Redémarrer Sublime (ou simplement modifier puis sauvegarder un `.py` du package pour rejouer `plugin_loaded()`).
4. Vérifier la console (`` Ctrl+` ``) : aucun Traceback. La commande `Tools → Alfaco → Atlassian → Sélectionner organisation` doit afficher la liste.

## Cohabitation avec Package Control

Si Package Control est installé, il supprime au démarrage tout package présent dans `Packages/` mais absent de `installed_packages` (« orphelins »). `make install` copie nos plugins hors PC, donc il faut les déclarer une fois pour que PC les laisse tranquilles.

Ouvrir `Preferences → Package Settings → Package Control → Settings – User` et ajouter les 4 noms à `installed_packages` :

```json
{
    "installed_packages":
    [
        "AlfacoAtlassian",
        "AlfacoCompletion",
        "AlfacoEditing",
        "AlfacoLib",
        // ... vos autres packages
    ]
}
```

Sans ça : au prochain redémarrage, PC affichera `Removing N orphaned packages...` et videra les `Packages/Alfaco*`.

## WSL : précisions

`make link` détecte WSL et force `make install` (NTFS ne suit pas les symlinks WSL). Le username Windows est résolu via `cmd.exe` (peut différer de `$USER` côté WSL — par exemple `ubuntu` ↔ `Jean`).

Si la détection échoue : poser explicitement `SUBLIME_PACKAGES_DIR=/mnt/c/Users/<user>/AppData/Roaming/Sublime\ Text/Packages` avant le `make`.

## Désinstallation

```bash
make uninstall
```

Supprime tous les `<Packages>/Alfaco*`. Les `User/alfaco-*.sublime-settings` ne sont pas touchés.
