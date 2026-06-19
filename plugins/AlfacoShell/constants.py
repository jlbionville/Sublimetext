# -*- coding: utf-8 -*-
"""Constantes de configuration du plugin AlfacoShell.

Clés du fichier de settings, valeurs par défaut et identifiants du
package. Aucune logique ici — uniquement la source de vérité des noms.
"""

PLUGIN_NAME = "AlfacoShell"
SETTINGS_FILE = "alfaco-shell.sublime-settings"

# Clés du fichier de settings (source de vérité de la configuration)
KEY_EXEC_PREFIX = "exec_prefix"
KEY_EXEC_BY_PLATFORM = "exec_by_platform"
KEY_TIMEOUT = "timeout_seconds"

# Défauts (précédence : exec_prefix > exec_by_platform[os] > défaut intégré).
# Clés de plateforme = valeurs de sublime.platform() : "windows" | "osx" | "linux".
DEFAULT_EXEC_BY_PLATFORM = {
    "windows": ["wsl.exe", "-e", "bash", "-lc"],  # WSL, login shell → ~/.aws + PATH
    "osx": ["/bin/zsh", "-lc"],                    # zsh login → PATH Homebrew (aws)
    "linux": ["bash", "-lc"],
}
FALLBACK_PLATFORM = "linux"
DEFAULT_TIMEOUT_SECONDS = 120

# Buffer de sortie
OUTPUT_TITLE_PREFIX = "Shell ▸ "
OUTPUT_TITLE_MAXLEN = 40
OUTPUT_SYNTAX = "Packages/Text/Plain text.tmLanguage"
