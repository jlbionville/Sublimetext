# -*- coding: utf-8 -*-
"""Entry point du plugin Templates (suite Alfaco).

Plugin autonome : insère des templates de commandes depuis un
quick panel, avec gestion des placeholders (modes ``snippet`` / ``guided``),
sélection → paramètres, mode batch et import/export de fichiers
``.sublime-snippet``. Toute la config vit dans
``alfaco-templates.sublime-settings`` (User/), zéro valeur métier en dur.

Contrairement aux autres plugins consommateurs, AlfacoTemplates ne dépend
pas d'``AlfacoLib`` (rien à voir avec Atlassian) et lit ses settings via
``sublime.load_settings`` à chaque exécution, pour refléter à chaud les
éditions de la liste de templates.

Compatibilité : Sublime Text 4, plugin host Python 3.8 (.python-version).
"""
import importlib

import sublime  # noqa: F401  (réservé pour usages futurs)

from AlfacoTemplates import constants as _constants
from AlfacoTemplates import errors as _errors
from AlfacoTemplates import domain as _domain
from AlfacoTemplates import engine as _engine

# Sublime ne cascade pas les reloads des sous-modules d'un package : on les
# recharge explicitement au chargement du plugin (mêmes raisons que les
# autres plugins de la suite avec AlfacoLib).
_LOCAL_MODULES = (_constants, _errors, _domain, _engine)


def plugin_loaded():
    for mod in _LOCAL_MODULES:
        importlib.reload(mod)


# Déclenche la découverte des classes *Command par Sublime.
from AlfacoTemplates.commands.insert_template import AlfacoTemplatesInsertTemplateCommand  # noqa: E402, F401
from AlfacoTemplates.commands.insert_text import AlfacoTemplatesInsertTextCommand  # noqa: E402, F401
from AlfacoTemplates.commands.replace_regions import AlfacoTemplatesReplaceRegionsCommand  # noqa: E402, F401
from AlfacoTemplates.commands.save_snippet import AlfacoTemplatesSaveSnippetCommand  # noqa: E402, F401
