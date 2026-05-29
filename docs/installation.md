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

> Les settings **du package** ne sont pas déployés : la config vit uniquement dans `<Packages>/User/`, que `make install` ne touche jamais (il y lance `init-config` en skip-if-exists). Tu ne perds donc plus ta config en réinstallant.

1. Initialiser les fichiers `User/` depuis les templates versionnés :

   ```bash
   make init-config
   ```

   Cette cible copie `plugins/<X>/templates/User/*.sublime-settings` vers `<Packages>/User/`. Elle **ne remplace pas** un fichier existant — relancer avec `make init-config-force` si besoin. (`make install` fait déjà ce seed automatiquement au 1er install.)

2. Ouvrir `Preferences → Package Settings → AlfacoAtlassian → Settings – User` et remplir les valeurs (le template contient des placeholders + commentaires inline) :

   ```jsonc
   {
       "jira_login": "votre.email@domaine.tld",
       "jira_password": "ATATT3xFfGF0…",          // token API, PAS le mdp
       "default_organisation": "votre-org",
       "api_rest_version": "3",
       "path_json_files_folder": "/chemin/absolu/dossier/jira"
   }
   ```

   Détail des clés disponibles : [configuration.md](configuration.md).

3. Redémarrer Sublime (ou simplement modifier puis sauvegarder un `.py` du package pour rejouer `plugin_loaded()`).
4. Vérifier la console (`` Ctrl+` ``) : aucun Traceback. La commande `Tools → Alfaco → Atlassian → Sélectionner organisation` doit afficher la liste.

## Cohabitation avec Package Control

Rien à configurer. `tools/deploy.py` exclut le fichier `package-metadata.json` du déploiement (`EXCLUDE_DURING_DEPLOY`). Sans ce marqueur, Package Control ne considère pas nos plugins comme « gérés par lui » et ne les touche pas au démarrage — exactement comme tout dossier manuel déposé dans `Packages/`.

**Migration depuis une version antérieure** (`<= v0.2.0` qui livrait `package-metadata.json`) : un simple `make install` écrase chaque dossier cible et purge donc les anciens fichiers. Vérifier au besoin :

```bash
find "$SUBLIME_PACKAGES_DIR"/Alfaco* -name package-metadata.json
# doit être vide
```

Si tu avais ajouté `AlfacoAtlassian`, `AlfacoCompletion`, `AlfacoEditing`, `AlfacoLib` à `installed_packages` (ancienne procédure), tu peux retirer ces 4 entrées — elles ne servent plus à rien (mais ne nuisent pas non plus).

## WSL : précisions

`make link` détecte WSL et force `make install` (NTFS ne suit pas les symlinks WSL). Le username Windows est résolu via `cmd.exe` (peut différer de `$USER` côté WSL — par exemple `ubuntu` ↔ `Jean`).

Si la détection échoue : poser explicitement `SUBLIME_PACKAGES_DIR=/mnt/c/Users/<user>/AppData/Roaming/Sublime\ Text/Packages` avant le `make`.

## Désinstallation

```bash
make uninstall
```

Supprime tous les `<Packages>/Alfaco*`. Les `User/alfaco-*.sublime-settings` ne sont pas touchés.
