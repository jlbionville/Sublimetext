# AlfacoShell — exécuter la sélection comme commande shell

Date : 2026-06-19
Plugin : AlfacoShell (nouveau, autonome — pas de dépendance `AlfacoLib`)

## Origine

Intégration dans la suite Alfaco d'un plugin externe (`C:\tmp\AwsRunner`)
qui exécutait une sélection comme commande **AWS CLI via WSL** et affichait
le résultat dans un buffer scratch. L'intégration : (1) mise en conformité
avec les conventions du monorepo, (2) cadrage **neutre** (shell générique,
plus d'AWS dans les noms ni l'UI ; les commandes AWS restent de simples
exemples), (3) **support multi-OS** (Mac / Linux / Windows-WSL) alors que
l'original codait `wsl.exe` en dur.

## Objectif

Sélectionner du texte → l'exécuter comme commande shell → afficher le
résultat dans un buffer scratch (JSON indenté si parsable, sinon brut),
suivi de `--- stderr ---` (si présent) et `--- exit code: N ---`.
Exécution **asynchrone** (l'UI ne gèle pas).

## Comportement

| Cas | Comportement |
|---|---|
| Sélection vide | message de statut `[SELECTION_EMPTY] …`, aucune exécution |
| Sélection multi-régions | régions concaténées par `\n`, exécutées en un seul appel (comportement de l'original conservé) |
| Sortie JSON parsable | `json.dumps(..., indent=2, ensure_ascii=False)` |
| Sortie non-JSON | texte brut inchangé |
| `stderr` non vide | bloc `--- stderr ---` ajouté |
| Toujours | `--- exit code: N ---` en fin |
| Timeout dépassé | message `[EXEC_TIMEOUT] …` |
| Échec du runner (exception) | message `[EXEC_FAILED] …: <détail>` |

Buffer : scratch, lecture seule, nommé `Shell ▸ <40 premiers car. de la commande>`,
syntaxe **Plain text** (l'original forçait JSON ; en générique on évite la
coloration trompeuse sur une sortie non-JSON).

## Exécution multi-OS (cœur du changement)

Le **domain pur** résout le préfixe d'exécution à partir de la plateforme
(`sublime.platform()` est passé en argument — le domain n'importe jamais
`sublime`, il reste testable hors éditeur).

Défauts intégrés :

```python
DEFAULT_EXEC_BY_PLATFORM = {
    "windows": ["wsl.exe", "-e", "bash", "-lc"],  # WSL, login shell → ~/.aws + PATH
    "osx":     ["/bin/zsh", "-lc"],               # zsh login → PATH Homebrew (aws)
    "linux":   ["bash", "-lc"],
}
```

Ordre de résolution (du plus prioritaire au défaut) :

1. `exec_prefix` (liste) — override global, tous OS confondus ;
2. `exec_by_platform[<os>]` (dict) — override par OS ;
3. `DEFAULT_EXEC_BY_PLATFORM[<os>]` — défaut intégré.

`argv` final = `prefix + [texte_commande]`. Conséquence : **fonctionne
out-of-the-box sur Mac sans configuration**, et reste 100 % surchargeable.

Si la plateforme est inconnue (cas théorique), repli sur le défaut `linux`.

## Architecture (conventions de la suite)

```
plugins/AlfacoShell/
├── .python-version                 # 3.8 (host ST4)
├── plugin.py                       # autonome : plugin_loaded reload + import commande
├── constants.py                    # PLUGIN_NAME, SETTINGS_FILE, clés, défauts
├── errors.py                       # ErrorCode (str) + ERROR_CATALOG + error_message
├── domain.py                       # PUR : resolve_exec_argv, prettify, format_result
├── commands/
│   ├── __init__.py
│   └── run_selection.py            # AlfacoShellRunSelectionCommand (alfaco_shell_run_selection)
├── alfaco-shell.sublime-settings   # défaut du package (NON déployé)
├── templates/User/
│   └── alfaco-shell.sublime-settings  # seed posé dans <Packages>/User/ par init-config
├── Context.sublime-menu            # clic droit
├── Main.sublime-menu               # Tools → Alfaco → Shell + Preferences → AlfacoShell
├── Default.sublime-commands        # Command Palette
├── Default.sublime-keymap          # vide (binding commenté en suggestion)
├── package-metadata.json           # NON déployé
├── README.md                       # style suite, en français
└── tests/
    └── test_domain.py              # pytest hors-Sublime
```

### Découpage des unités

- **`domain.py`** (pur, sans I/O ni `sublime`) :
  - `resolve_exec_argv(command_text, settings_like, platform)` → `list[str]` ;
  - `prettify(raw)` → JSON indenté si parsable, sinon brut ;
  - `format_result(stdout, stderr, returncode)` → texte du buffer.
  - `settings_like` expose `.get(key, default)` (compatible `sublime.Settings`
    **et** `dict` → testable via un stub `dict`).
- **`commands/run_selection.py`** (adapter Sublime) : `TextCommand` qui lit
  la sélection, lance `subprocess.run` en `set_timeout_async`, écrit le
  buffer. Aucune logique métier (déléguée au domain).
- **`plugin.py`** : standalone (cf. AlfacoTemplates) — `plugin_loaded()`
  fait `importlib.reload` des modules locaux ; import de la classe commande
  pour la découverte Sublime ; settings rechargés à chaque exécution
  (`sublime.load_settings`) pour refléter les éditions à chaud.

## Settings

`alfaco-shell.sublime-settings` (défaut package, non déployé) **et** le seed
`templates/User/alfaco-shell.sublime-settings` :

```jsonc
{
    // Override global du préfixe d'exécution (tous OS). Décommenter pour forcer.
    // "exec_prefix": ["wsl.exe", "-e", "bash", "-c"],

    // Override par plateforme (clés Sublime : "windows" | "osx" | "linux").
    // Fusionne avec les défauts intégrés ; seules les clés présentes priment.
    "exec_by_platform": {
        "windows": ["wsl.exe", "-e", "bash", "-lc"],
        "osx":     ["/bin/zsh", "-lc"],
        "linux":   ["bash", "-lc"]
    },

    "timeout_seconds": 120
}
```

Précédence : `exec_prefix` > `exec_by_platform[os]` > défaut intégré.

## Erreurs codifiées

Style de la suite (`ErrorCode` à constantes `str`, `ERROR_CATALOG`,
`error_message(code, detail="")`), remplace les codes `AWSR-00x` de
l'original :

| Code | Sens |
|---|---|
| `SELECTION_EMPTY` | Aucune sélection à exécuter |
| `EXEC_TIMEOUT` | Délai d'exécution dépassé |
| `EXEC_FAILED` | Échec du runner |

## Interface

- **Command Palette** : « Shell : exécuter la sélection » → `alfaco_shell_run_selection`.
- **Clic droit** (`Context.sublime-menu`) : même entrée.
- **Tools → Alfaco → Shell** : même entrée.
- **Preferences → Package Settings → AlfacoShell** : Settings – Default / User.
- **Keymap** : aucun binding par défaut (espace de touches partagé entre
  plugins → risque de collision, cf. CLAUDE.md). Un binding commenté
  (ex. `ctrl+alt+a`) est laissé en suggestion dans `Default.sublime-keymap`.

## Tests (TDD)

`tests/test_domain.py`, hors-Sublime via le `conftest.py` racine
(`sys.path.insert(0, parents[2])`) :

- `resolve_exec_argv` : défaut par OS (windows / osx / linux) ;
- précédence `exec_by_platform[os]` > défaut ;
- précédence `exec_prefix` > `exec_by_platform` ;
- plateforme inconnue → repli `linux` ;
- `prettify` : JSON valide indenté / passe-plat non-JSON / vide ;
- `format_result` : exit code présent, bloc stderr conditionnel, corps JSON.

Les `*Command` ne sont pas testables hors-Sublime (logique extraite dans
le domain).

## Conformité monorepo

- `tools/deploy.py` auto-découvre `plugins/*` → AlfacoShell déployable sans
  modif (`make install PLUGIN=AlfacoShell`, `make link`, `make status`).
- Settings du package exclus du déploiement ; config réelle via
  `templates/User/` seedée par `init-config` (skip-if-exists).
- Mettre à jour le tableau des plugins de **CLAUDE.md** (6 plugins).

## Hors périmètre (YAGNI)

Reprises des « pistes d'évolution » de l'original, **non** traitées ici :

- multi-sélection → N commandes → N buffers (aujourd'hui concaténées) ;
- réutilisation d'un buffer taggé au lieu d'en rouvrir un ;
- injection profil/région AWS depuis les settings.
