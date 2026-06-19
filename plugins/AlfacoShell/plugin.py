# -*- coding: utf-8 -*-
"""Entry point du plugin AlfacoShell (suite Alfaco).

Plugin autonome : exécute la sélection courante comme commande shell et
affiche le résultat dans un buffer scratch. Exécution multi-OS (zsh sur
macOS, bash sur Linux, WSL sur Windows), surchargeable dans
``alfaco-shell.sublime-settings`` (User/).

Contrairement aux plugins consommateurs d'``AlfacoLib``, AlfacoShell ne
dépend de rien d'autre que la stdlib, et lit ses settings via
``sublime.load_settings`` à chaque exécution.

Compatibilité : Sublime Text 4, plugin host Python 3.8 (.python-version).
"""
import importlib

import sublime  # noqa: F401  (réservé pour usages futurs)

from AlfacoShell import constants as _constants
from AlfacoShell import errors as _errors
from AlfacoShell import domain as _domain

# Sublime ne cascade pas les reloads des sous-modules d'un package : on les
# recharge explicitement au chargement du plugin.
_LOCAL_MODULES = (_constants, _errors, _domain)


def plugin_loaded():
    for mod in _LOCAL_MODULES:
        importlib.reload(mod)


# Déclenche la découverte de la classe *Command par Sublime.
from AlfacoShell.commands.run_selection import AlfacoShellRunSelectionCommand  # noqa: E402, F401
