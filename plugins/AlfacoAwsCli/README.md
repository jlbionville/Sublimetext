# AlfacoAwsCli — plugin Sublime Text 4 (suite Alfaco)

Insère des templates de commandes **AWS CLI** (EC2, S3, EBS snapshots, AWS Backup…)
depuis un menu déroulant, avec gestion des placeholders.

Plugin **autonome** : il ne dépend pas d'`AlfacoLib`.

## Fonctionnalités

- Menu déroulant (quick panel) listant les templates, avec description et aperçu de la commande
- Accessible par **clic droit**, **Tools → Alfaco → AWS CLI** ou **Command Palette**
- Liste des templates **100 % configurable** dans les préférences du plugin
- Placeholders `${nom}` ou `${nom:valeur_par_defaut}` avec deux modes :

| Mode | Comportement | Quand l'utiliser |
|---|---|---|
| `guided` | Un input panel par placeholder (valeur par défaut pré-remplie), puis insertion de la commande complétée | Saisie rapide guidée, valeurs longues (ARN…) |
| `snippet` | Insertion immédiate, navigation entre les champs avec **Tab** (snippet Sublime natif) | Édition visuelle dans le contexte du fichier |

### Sélection → paramètres

Si du texte est **sélectionné** au moment de choisir le template, ses tokens
(séparés par des espaces) remplissent les placeholders **dans l'ordre
d'apparition**, et la sélection est remplacée par la commande générée.

| Sélection | Template choisi | Résultat |
|---|---|---|
| `i-0abc123 eu-west-1` | `aws ec2 start-instances --instance-ids ${instance_id} --region ${region:eu-west-3}` | `aws ec2 start-instances --instance-ids i-0abc123 --region eu-west-1` |
| `vol-0def "avant migration"` | `aws ec2 create-snapshot --volume-id ${volume_id} --description "${description}" …` | Les guillemets groupent un token contenant des espaces |
| `i-0abc123` (sélection partielle) | Template à 3 placeholders | 1er placeholder rempli ; les autres suivent le mode actif (saisie guidée ou champs Tab) |

- Tokens excédentaires : ignorés, avertissement dans la barre de statut.
- Désactivable via `"selection_as_parameters": false`.

### Mode batch (plusieurs lignes)

Si la sélection contient **plusieurs lignes non vides**, chaque ligne est un
jeu de paramètres : une commande est générée **par ligne**, et la sélection
est remplacée par le bloc de commandes.

Exemple — sélection :

```
i-0abc123 eu-west-1
i-0def456 eu-west-3
i-0ghi789
```

- Template « EC2 — Stop instance » → 3 commandes `aws ec2 stop-instances …`,
  une par instance ; la 3ᵉ ligne, incomplète, utilise la région par défaut
  (`eu-west-3`).
- Un récapitulatif s'affiche dans la barre de statut : commandes générées,
  tokens en trop ignorés, lignes incomplètes (défauts appliqués).
- En batch, il n'y a **pas de saisie guidée** ligne par ligne : les valeurs
  manquantes retombent sur le défaut du placeholder, sinon sur son nom.
- Multi-curseurs (Ctrl+D / Ctrl+clic) : chaque région de sélection est
  traitée et remplacée indépendamment.

### Snippets (.sublime-snippet)

En plus des templates JSON, le menu propose les fichiers **`.sublime-snippet`**
(format XML officiel de Sublime) trouvés dans les répertoires configurés :

```jsonc
"snippet_directories":
[
    "${packages}/AlfacoAwsCli/snippets",   // défaut (livré avec 2 exemples)
    "~/mes-snippets-aws",                   // ~ supporté
    "$HOME/projets/equipe/snippets"         // variables d'env supportées
]
```

Format d'un fichier :

```xml
<snippet>
    <content><![CDATA[aws s3 presign s3://${bucket}/${key} --expires-in ${expires:3600}]]></content>
    <description>S3 — URL présignée</description>
</snippet>
```

- La **caption** dans le menu = `<description>`, sinon le nom du fichier ;
  les entrées snippets sont marquées « snippet » avec une icône dédiée.
- Le contenu passe par le **même moteur de placeholders** `${nom}` /
  `${nom:défaut}` : saisie guidée, sélection → paramètres et mode batch
  fonctionnent à l'identique.
- Répertoire absent ou fichier XML invalide : ignoré, warning
  `[SNIPPET_DIR_NOT_FOUND]` / `[SNIPPET_PARSE_FAILED]` dans la console.

### Enregistrer la sélection comme snippet

Sélectionnez une commande dans l'éditeur → clic droit →
**AWS CLI : enregistrer la sélection comme snippet…** (aussi dans
Tools → Alfaco → AWS CLI et la Command Palette). Le plugin demande :

1. la **description** (deviendra la caption dans le menu) ;
2. le **nom du fichier**, pré-rempli avec un slug de la description
   (ex. « S3 — URL présignée » → `s3-url-presignee.sublime-snippet`).

Le fichier est écrit dans le **premier** répertoire de `snippet_directories`
(créé s'il n'existe pas), puis ouvert pour relecture. Si un fichier du même
nom existe, une **confirmation explicite** est demandée avant écrasement.

## Installation (monorepo)

```bash
make install PLUGIN=AlfacoAwsCli       # copie le plugin + seed la config User/
# ou, hors WSL :
make link PLUGIN=AlfacoAwsCli          # symlink (mode dev)
```

`make install` exécute `init-config` : la liste de templates par défaut est
copiée dans `<Packages>/User/alfaco-aws-cli.sublime-settings` (sans écraser
un fichier existant). C'est ce fichier User qui fournit les templates en
production — le défaut du package n'est volontairement **pas** déployé.

## Utilisation

1. Clic droit dans un fichier → **AWS CLI : insérer un template…**
   (ou `Tools → Alfaco → AWS CLI → Insérer un template…`)
2. Filtrer/choisir le template (recherche floue native du quick panel).
3. Selon le mode :
   - `guided` : renseigner chaque placeholder (Entrée pour valider, Échap pour annuler).
   - `snippet` : la commande est insérée, **Tab** passe au champ suivant.

## Configuration

`Preferences → Package Settings → AlfacoAwsCli → Settings – User`

```jsonc
{
    "placeholder_mode": "guided",        // "guided" | "snippet"
    "show_descriptions": true,           // descriptions dans le menu
    "insert_trailing_newline": false,    // \n après la commande
    "templates":
    [
        {
            "caption": "EC2 — Describe instances (par ID)",
            "description": "Détails d'une ou plusieurs instances",
            "command": "aws ec2 describe-instances --instance-ids ${instance_id} --region ${region:eu-west-3}"
        }
    ]
}
```

Règles :

- `caption` et `command` sont obligatoires ; `description` est optionnelle.
- Un placeholder répété (`${region}` deux fois) n'est demandé qu'une fois.
- Vos overrides utilisateur sont fusionnés avec les défauts (mécanisme
  standard de Sublime : le fichier User prime).

## Structure du package

```
AlfacoAwsCli/
├── .python-version                  # force le plugin host Python 3.8 (ST4)
├── plugin.py                        # entry-point : plugin_loaded + import des commandes
├── constants.py                     # clés de settings, valeurs par défaut
├── errors.py                        # codes d'erreur + libellés UI
├── domain.py                        # entités Template / Placeholder (Python pur)
├── engine.py                        # logique : placeholders, sélection, snippets
├── commands/                        # une commande Sublime = un fichier
│   ├── insert_template.py
│   ├── insert_text.py
│   ├── replace_regions.py
│   └── save_snippet.py
├── alfaco-aws-cli.sublime-settings  # défaut du package (non déployé)
├── templates/User/                  # config seedée dans <Packages>/User/ par init-config
│   └── alfaco-aws-cli.sublime-settings
├── snippets/                        # snippets livrés par défaut
│   ├── ec2-describe-volumes.sublime-snippet
│   └── s3-presign.sublime-snippet
├── Context.sublime-menu             # entrée clic droit
├── Main.sublime-menu                # Tools → Alfaco → AWS CLI + Preferences
├── Default.sublime-commands         # entrées Command Palette
├── package-metadata.json            # métadonnées suite (non déployé)
└── tests/                           # pytest hors-Sublime (logique pure)
```

## Références officielles

- API Sublime Text : <https://www.sublimetext.com/docs/api_reference.html>
- Format des menus : <https://www.sublimetext.com/docs/menus.html>
- Syntaxe des snippets : <https://www.sublimetext.com/docs/completions.html>
- AWS CLI Command Reference : <https://docs.aws.amazon.com/cli/latest/reference/>
