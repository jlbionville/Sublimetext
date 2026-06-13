# -*- coding: utf-8 -*-
"""Entités du domaine AlfacoAwsCli : Template et Placeholder (Python pur).

Aucune dépendance à l'API Sublime — ce module est testable hors Sublime.
"""
import logging
import re
from typing import List, Optional

from .errors import ErrorCode, error_message

logger = logging.getLogger(__name__)

# ${nom} ou ${nom:valeur_par_defaut}
PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z0-9_\-]+)(?::([^}]*))?\}")


class Placeholder:
    """Placeholder d'un template : nom + valeur par défaut optionnelle."""

    def __init__(self, name: str, default: Optional[str] = None) -> None:
        self.name = name
        self.default = default

    def prompt(self) -> str:
        """Libellé affiché dans l'input panel en mode guidé."""
        if self.default:
            return "{} (défaut : {})".format(self.name, self.default)
        return self.name


class Template:
    """Template de commande AWS CLI (depuis les settings ou un fichier snippet)."""

    SOURCE_SETTINGS = "settings"
    SOURCE_SNIPPET = "snippet"

    def __init__(
        self,
        caption: str,
        command: str,
        description: str = "",
        source: str = SOURCE_SETTINGS,
    ) -> None:
        self.caption = caption
        self.command = command
        self.description = description
        self.source = source

    def placeholders(self) -> List[Placeholder]:
        """Extrait les placeholders uniques, dans l'ordre d'apparition.

        Si un même placeholder apparaît plusieurs fois, sa valeur par
        défaut est retenue depuis la première occurrence qui en déclare une.
        """
        by_name = {}  # type: dict
        ordered = []  # type: List[Placeholder]
        for match in PLACEHOLDER_RE.finditer(self.command):
            name, default = match.group(1), match.group(2)
            if name not in by_name:
                placeholder = Placeholder(name, default)
                by_name[name] = placeholder
                ordered.append(placeholder)
            elif default and not by_name[name].default:
                by_name[name].default = default
        return ordered

    @classmethod
    def from_setting(cls, raw: dict) -> Optional["Template"]:
        """Construit un Template depuis une entrée de settings, ou None si invalide."""
        if not isinstance(raw, dict) or "caption" not in raw or "command" not in raw:
            logger.warning(error_message(ErrorCode.TEMPLATE_INVALID_ENTRY))
            return None
        return cls(
            caption=str(raw["caption"]),
            command=str(raw["command"]),
            description=str(raw.get("description", "")),
        )
