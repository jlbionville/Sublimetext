# -*- coding: utf-8 -*-
"""Entry point du plugin AlfacoAtlassian."""
import importlib

from AlfacoLib import config as _alfacolib_config
from AlfacoLib import atlassian_client as _alfacolib_client
from AlfacoLib import io as _alfacolib_io
from AlfacoLib import logger as _alfacolib_logger

_LIB_MODULES = (_alfacolib_config, _alfacolib_client, _alfacolib_io, _alfacolib_logger)

config = None
log = None


def plugin_loaded():
    global config, log
    for mod in _LIB_MODULES:
        importlib.reload(mod)
    config = _alfacolib_config.Configuration([
        "alfaco-atlassian.sublime-settings",
        "Preferences.sublime-settings",
    ])
    log = _alfacolib_logger.get_logger("Atlassian", debug=config.get("debug", False))


from AlfacoAtlassian.commands.select_organisation import SelectOrganisationCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.select_jira_project import SelectJiraProjectCommand  # noqa: E402, F401
