# -*- coding: utf-8 -*-
"""Entry point du plugin Editing."""
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
        "alfaco-editing.sublime-settings",
        "Preferences.sublime-settings",
    ])


from AlfacoEditing.commands.text_to_table import TextToTableCommand  # noqa: E402, F401
from AlfacoEditing.commands.insert_tag import InsertTagCommand  # noqa: E402, F401
from AlfacoEditing.commands.remove_tag import RemoveTagCommand  # noqa: E402, F401
from AlfacoEditing.commands.select_between_markers import SelectBetweenMarkersCommand  # noqa: E402, F401
