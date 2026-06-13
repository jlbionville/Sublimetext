# -*- coding: utf-8 -*-
"""Constantes de configuration du plugin AlfacoAwsCli.

Clés du fichier de settings, valeurs par défaut et identifiants du
package. Aucune logique ici — uniquement la source de vérité des noms.
"""

PLUGIN_NAME = "AlfacoAwsCli"
SETTINGS_FILE = "alfaco-aws-cli.sublime-settings"

# Clés du fichier de settings (source de vérité de la configuration)
KEY_TEMPLATES = "templates"
KEY_PLACEHOLDER_MODE = "placeholder_mode"
KEY_SHOW_DESCRIPTIONS = "show_descriptions"
KEY_TRAILING_NEWLINE = "insert_trailing_newline"
KEY_SELECTION_AS_PARAMS = "selection_as_parameters"
KEY_SNIPPET_DIRS = "snippet_directories"

# Variable de chemin résolue vers sublime.packages_path()
PACKAGES_VAR = "${packages}"
SNIPPET_EXTENSION = ".sublime-snippet"

# Valeurs par défaut (précédence : settings utilisateur > settings package > défaut)
DEFAULT_PLACEHOLDER_MODE = "snippet"
DEFAULT_SHOW_DESCRIPTIONS = True
DEFAULT_TRAILING_NEWLINE = False
DEFAULT_SELECTION_AS_PARAMS = True
DEFAULT_SNIPPET_DIRS = [PACKAGES_VAR + "/" + PLUGIN_NAME + "/snippets"]

MODE_SNIPPET = "snippet"
MODE_GUIDED = "guided"
VALID_MODES = (MODE_SNIPPET, MODE_GUIDED)
