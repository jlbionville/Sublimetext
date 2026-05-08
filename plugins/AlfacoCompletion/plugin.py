# -*- coding: utf-8 -*-
"""Entry point du plugin Completion."""
import importlib
import sublime  # noqa: F401  (réservé pour usages futurs)

from AlfacoLib import config as _alfacolib_config

_LIB_MODULES = (_alfacolib_config,)

config = None


def plugin_loaded():
    global config
    for mod in _LIB_MODULES:
        importlib.reload(mod)
    config = _alfacolib_config.Configuration([
        "alfaco-completion.sublime-settings",
        "Preferences.sublime-settings",
    ])
