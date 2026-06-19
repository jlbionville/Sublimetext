# -*- coding: utf-8 -*-
"""Codes d'erreur applicatifs et libellés UI du plugin AlfacoShell.

Convention des codes : ``DOMAINE_DESCRIPTION``. Les libellés humains
vivent dans :data:`ERROR_CATALOG` ; :func:`error_message` les formate.
"""


class ErrorCode:
    """Codes d'erreur applicatifs (convention : DOMAINE_DESCRIPTION)."""

    SELECTION_EMPTY = "SELECTION_EMPTY"
    EXEC_TIMEOUT = "EXEC_TIMEOUT"
    EXEC_FAILED = "EXEC_FAILED"


ERROR_CATALOG = {
    ErrorCode.SELECTION_EMPTY: "Aucune sélection à exécuter.",
    ErrorCode.EXEC_TIMEOUT: "Délai d'exécution dépassé.",
    ErrorCode.EXEC_FAILED: "Échec du runner.",
}


def error_message(code, detail=""):
    """Formate ``[CODE] libellé`` (+ ``: détail`` si fourni)."""
    base = "[{}] {}".format(code, ERROR_CATALOG[code])
    return "{} : {}".format(base, detail) if detail else base
