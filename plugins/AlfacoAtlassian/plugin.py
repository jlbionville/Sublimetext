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
from AlfacoAtlassian.commands.create_jira_issue import CreateJiraIssueCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.open_jira_projects import OpenJiraProjectsCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.init_json_jira import InitJsonJiraCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.set_jira_project_in_snippet import SetJiraProjectInSnippetCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.init_markdown_jira import InitMarkdownJiraCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.create_jira_from_markdown import CreateJiraFromMarkdownCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.insert_current_project import InsertCurrentProjectCommand  # noqa: E402, F401
from AlfacoAtlassian.commands.insert_current_organisation import InsertCurrentOrganisationCommand  # noqa: E402, F401
