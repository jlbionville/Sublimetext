# -*- coding: utf-8 -*-
"""Domain pur du plugin AlfacoShell.

Ne dépend ni de Sublime, ni d'aucune I/O. Construit l'argv d'exécution
selon la plateforme, joliifie la sortie et formate le résultat du buffer.
100 % testable hors de l'éditeur.
"""
import json

from .constants import (
    DEFAULT_EXEC_BY_PLATFORM,
    FALLBACK_PLATFORM,
    KEY_EXEC_BY_PLATFORM,
    KEY_EXEC_PREFIX,
)


def resolve_exec_argv(command_text, settings_like, platform):
    """argv d'exécution = préfixe résolu + [texte de commande].

    Précédence du préfixe :
      1. settings 'exec_prefix' (override global, tous OS) ;
      2. settings 'exec_by_platform'[platform] (override par OS) ;
      3. DEFAULT_EXEC_BY_PLATFORM[platform] (défaut intégré).
    Plateforme inconnue → repli sur FALLBACK_PLATFORM.

    settings_like expose .get(key, default) (compatible sublime.Settings et dict).
    """
    prefix = settings_like.get(KEY_EXEC_PREFIX, None)
    if not prefix:
        by_platform = settings_like.get(KEY_EXEC_BY_PLATFORM, None) or {}
        prefix = by_platform.get(platform)
    if not prefix:
        prefix = DEFAULT_EXEC_BY_PLATFORM.get(
            platform, DEFAULT_EXEC_BY_PLATFORM[FALLBACK_PLATFORM]
        )
    return list(prefix) + [command_text]


def prettify(raw):
    """JSON indenté si parsable, sinon texte brut inchangé."""
    stripped = raw.strip()
    if not stripped:
        return raw
    try:
        return json.dumps(json.loads(stripped), indent=2, ensure_ascii=False)
    except (ValueError, TypeError):
        return raw


def format_result(stdout, stderr, returncode):
    """Texte du buffer : corps prettifié, bloc stderr (si présent), exit code."""
    parts = []
    body = prettify(stdout)
    if body.strip():
        parts.append(body)
    if stderr.strip():
        parts.append("--- stderr ---\n" + stderr.rstrip())
    parts.append("--- exit code: {} ---".format(returncode))
    return "\n".join(parts)
