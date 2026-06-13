# -*- coding: utf-8 -*-
"""Entry point du plugin AwsCli (suite Alfaco).

Plugin autonome : insère des templates de commandes AWS CLI depuis un
quick panel, avec gestion des placeholders (modes ``snippet`` / ``guided``),
sélection → paramètres, mode batch et import/export de fichiers
``.sublime-snippet``. Toute la config vit dans
``alfaco-aws-cli.sublime-settings`` (User/), zéro valeur métier en dur.

Contrairement aux autres plugins consommateurs, AlfacoAwsCli ne dépend
pas d'``AlfacoLib`` (rien à voir avec Atlassian) et lit ses settings via
``sublime.load_settings`` à chaque exécution, pour refléter à chaud les
éditions de la liste de templates.

Compatibilité : Sublime Text 4, plugin host Python 3.8 (.python-version).
"""
import importlib

import sublime  # noqa: F401  (réservé pour usages futurs)

from AlfacoAwsCli import constants as _constants
from AlfacoAwsCli import errors as _errors
from AlfacoAwsCli import domain as _domain
from AlfacoAwsCli import engine as _engine

# Sublime ne cascade pas les reloads des sous-modules d'un package : on les
# recharge explicitement au chargement du plugin (mêmes raisons que les
# autres plugins de la suite avec AlfacoLib).
_LOCAL_MODULES = (_constants, _errors, _domain, _engine)


def plugin_loaded():
    for mod in _LOCAL_MODULES:
        importlib.reload(mod)


# Déclenche la découverte des classes *Command par Sublime.
from AlfacoAwsCli.commands.insert_template import AlfacoAwsCliInsertTemplateCommand  # noqa: E402, F401
from AlfacoAwsCli.commands.insert_text import AlfacoAwsCliInsertTextCommand  # noqa: E402, F401
from AlfacoAwsCli.commands.replace_regions import AlfacoAwsCliReplaceRegionsCommand  # noqa: E402, F401
from AlfacoAwsCli.commands.save_snippet import AlfacoAwsCliSaveSnippetCommand  # noqa: E402, F401
