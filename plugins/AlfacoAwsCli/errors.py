# -*- coding: utf-8 -*-
"""Codes d'erreur applicatifs et libellés UI du plugin AlfacoAwsCli.

Convention des codes : ``DOMAINE_DESCRIPTION``. Les libellés humains
vivent dans :data:`ERROR_CATALOG` ; :func:`error_message` les formate.
"""
from .constants import (
    DEFAULT_PLACEHOLDER_MODE,
    KEY_PLACEHOLDER_MODE,
    KEY_TEMPLATES,
    SETTINGS_FILE,
    VALID_MODES,
)


class ErrorCode:
    """Codes d'erreur applicatifs (convention : DOMAINE_DESCRIPTION)."""

    TEMPLATES_EMPTY = "TEMPLATES_EMPTY"
    TEMPLATE_INVALID_ENTRY = "TEMPLATE_INVALID_ENTRY"
    VIEW_NOT_FOUND = "VIEW_NOT_FOUND"
    VIEW_READ_ONLY = "VIEW_READ_ONLY"
    CONFIG_INVALID_MODE = "CONFIG_INVALID_MODE"
    SELECTION_EXTRA_TOKENS = "SELECTION_EXTRA_TOKENS"
    SNIPPET_DIR_NOT_FOUND = "SNIPPET_DIR_NOT_FOUND"
    SNIPPET_PARSE_FAILED = "SNIPPET_PARSE_FAILED"
    SELECTION_EMPTY = "SELECTION_EMPTY"
    SNIPPET_WRITE_FAILED = "SNIPPET_WRITE_FAILED"


ERROR_CATALOG = {
    ErrorCode.TEMPLATES_EMPTY: (
        "Aucun template défini. Ajoutez des entrées dans la clé "
        "'{key}' de {settings}."
    ).format(key=KEY_TEMPLATES, settings=SETTINGS_FILE),
    ErrorCode.TEMPLATE_INVALID_ENTRY: (
        "Template invalide ignoré (clés 'caption' et 'command' requises)."
    ),
    ErrorCode.VIEW_NOT_FOUND: "Aucun fichier actif pour insérer la commande.",
    ErrorCode.VIEW_READ_ONLY: "Le fichier actif est en lecture seule.",
    ErrorCode.CONFIG_INVALID_MODE: (
        "Mode '{{mode}}' invalide pour '{key}' (valeurs possibles : {modes}). "
        "Mode '{default}' utilisé."
    ).format(
        key=KEY_PLACEHOLDER_MODE,
        modes=", ".join(VALID_MODES),
        default=DEFAULT_PLACEHOLDER_MODE,
    ),
    ErrorCode.SELECTION_EXTRA_TOKENS: (
        "Sélection : {extra} valeur(s) en trop ignorée(s) "
        "(le template attend {expected} paramètre(s))."
    ),
    ErrorCode.SNIPPET_DIR_NOT_FOUND: (
        "Répertoire de snippets introuvable, ignoré : {path}"
    ),
    ErrorCode.SNIPPET_PARSE_FAILED: (
        "Snippet illisible, ignoré : {path} ({reason})"
    ),
    ErrorCode.SELECTION_EMPTY: (
        "Sélectionnez d'abord la commande à enregistrer comme snippet."
    ),
    ErrorCode.SNIPPET_WRITE_FAILED: (
        "Impossible d'écrire le snippet : {path} ({reason})"
    ),
}

# Libellés UI de la commande « Enregistrer comme snippet »
SAVE_PROMPT_DESCRIPTION = "Description du snippet"
SAVE_PROMPT_FILENAME = "Nom du fichier"
SAVE_OVERWRITE_QUESTION = "Le fichier existe déjà :\n{path}\n\nL'écraser ?"
SAVE_DONE_LABEL = "{plugin} : snippet enregistré → {path}"

# Libellé du récapitulatif affiché après une génération batch
BATCH_SUMMARY_LABEL = (
    "{plugin} : {count} commande(s) générée(s)"
    " — {extra} token(s) en trop ignoré(s),"
    " {incomplete} ligne(s) incomplète(s) (défauts appliqués)."
)


def error_message(code, **fmt):
    """Retourne le libellé humain associé à un code d'erreur.

    Args:
        code: Code d'erreur (voir :class:`ErrorCode`).
        **fmt: Valeurs d'interpolation optionnelles du libellé.

    Returns:
        Message formaté ``[CODE] libellé``.
    """
    label = ERROR_CATALOG.get(code, code)
    if fmt:
        label = label.format(**fmt)
    return "[{}] {}".format(code, label)
