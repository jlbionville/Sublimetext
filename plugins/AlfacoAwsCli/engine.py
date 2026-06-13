# -*- coding: utf-8 -*-
"""Logique applicative d'AlfacoAwsCli : placeholders, sélection, snippets.

Conversion ``${nom}`` → snippet Sublime, tokenisation de la sélection,
remplissage des commandes (guidé / batch), génération et chargement des
fichiers ``.sublime-snippet``. Le seul lien avec l'API Sublime est
:func:`expand_directory` / :func:`resolve_mode` (résolution de chemins et
de settings) — le reste est du Python pur, testable hors Sublime.
"""
import logging
import os
import re
import shlex
import unicodedata
import xml.etree.ElementTree as ET
from typing import List, Optional
from xml.sax.saxutils import escape as xml_escape

import sublime

from .constants import (
    DEFAULT_PLACEHOLDER_MODE,
    DEFAULT_SNIPPET_DIRS,
    KEY_PLACEHOLDER_MODE,
    KEY_SNIPPET_DIRS,
    KEY_TEMPLATES,
    PACKAGES_VAR,
    SNIPPET_EXTENSION,
    VALID_MODES,
)
from .domain import PLACEHOLDER_RE, Placeholder, Template
from .errors import ErrorCode, error_message

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Conversion snippet / résolution des placeholders
# ─────────────────────────────────────────────────────────────────────────────


def escape_snippet_literal(text: str) -> str:
    """Échappe les caractères spéciaux de la syntaxe snippet Sublime ($, \\, })."""
    return text.replace("\\", "\\\\").replace("$", "\\$").replace("}", "\\}")


def to_sublime_snippet(template: Template, values: Optional[dict] = None) -> str:
    """Convertit ``${nom}``/``${nom:def}`` en champs numérotés ``${N:valeur}``.

    Les placeholders dont une valeur est fournie dans ``values`` sont
    insérés en texte littéral ; les autres deviennent des champs
    navigables avec Tab. Le texte littéral est échappé pour que la
    syntaxe snippet de Sublime ne l'interprète pas.
    """
    values = values or {}
    order = {}  # type: dict
    parts = []  # type: List[str]
    last_end = 0
    for match in PLACEHOLDER_RE.finditer(template.command):
        parts.append(escape_snippet_literal(template.command[last_end:match.start()]))
        name = match.group(1)
        if values.get(name):
            parts.append(escape_snippet_literal(values[name]))
        else:
            if name not in order:
                order[name] = len(order) + 1
            default = match.group(2) or name
            parts.append("${%d:%s}" % (order[name], escape_snippet_literal(default)))
        last_end = match.end()
    parts.append(escape_snippet_literal(template.command[last_end:]))
    return "".join(parts)


def tokenize_selection(text: str) -> List[str]:
    """Découpe la sélection en tokens séparés par des espaces.

    Les guillemets permettent de grouper un token contenant des espaces
    (parsing shlex). En cas de guillemets non fermés, repli sur un
    découpage simple par espaces.
    """
    try:
        return shlex.split(text)
    except ValueError:
        logger.debug("tokenize_selection: shlex a échoué, repli sur split()")
        return text.split()


def assign_tokens(placeholders: List[Placeholder], tokens: List[str]):
    """Affecte les tokens aux placeholders dans l'ordre d'apparition.

    Returns:
        Tuple ``(values, extra)`` : dict {nom: valeur} et nombre de
        tokens excédentaires ignorés.
    """
    values = {}  # type: dict
    for placeholder, token in zip(placeholders, tokens):
        values[placeholder.name] = token
    return values, max(len(tokens) - len(placeholders), 0)


def fill_command(template: Template, values: dict) -> str:
    """Remplace chaque placeholder par la valeur saisie (mode guidé).

    Si la valeur saisie est vide, repli sur la valeur par défaut du
    placeholder (déclarée sur n'importe laquelle de ses occurrences),
    ou, à défaut, sur son nom (pour rester visible et corrigeable).
    """
    defaults = {p.name: p.default for p in template.placeholders() if p.default}

    def _replace(match) -> str:
        name = match.group(1)
        return (
            values.get(name)
            or defaults.get(name)
            or match.group(2)
            or name
        )

    return PLACEHOLDER_RE.sub(_replace, template.command)


def batch_fill(template: Template, lines: List[str]):
    """Génère une commande par ligne de paramètres (mode batch).

    Chaque ligne est tokenisée puis affectée aux placeholders dans
    l'ordre. Les placeholders manquants retombent sur leur valeur par
    défaut (sinon leur nom) ; les tokens excédentaires sont ignorés.

    Returns:
        Tuple ``(commands, extra_total, incomplete_total)`` : liste des
        commandes générées, nombre total de tokens excédentaires et
        nombre de lignes incomplètes.
    """
    placeholders = template.placeholders()
    commands = []  # type: List[str]
    extra_total = 0
    incomplete_total = 0
    for line in lines:
        tokens = tokenize_selection(line)
        values, extra = assign_tokens(placeholders, tokens)
        extra_total += extra
        if len(tokens) < len(placeholders):
            incomplete_total += 1
        commands.append(fill_command(template, values))
    return commands, extra_total, incomplete_total


# ─────────────────────────────────────────────────────────────────────────────
# Génération de fichiers .sublime-snippet
# ─────────────────────────────────────────────────────────────────────────────

SNIPPET_FILE_TEMPLATE = """<snippet>
    <content><![CDATA[{content}]]></content>
    <description>{description}</description>
</snippet>
"""


def slugify_filename(text: str) -> str:
    """Transforme un libellé en nom de fichier sûr (ascii, minuscules, tirets)."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "snippet"


def build_snippet_xml(content: str, description: str) -> str:
    """Génère le XML .sublime-snippet (round-trip avec parse_snippet_file).

    La description est échappée (XML) ; la séquence ``]]>`` dans le
    contenu est découpée pour rester valide dans la section CDATA.
    """
    safe_content = content.replace("]]>", "]]]]><![CDATA[>")
    return SNIPPET_FILE_TEMPLATE.format(
        content=safe_content,
        description=xml_escape(description),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chargement des templates (settings + fichiers .sublime-snippet)
# ─────────────────────────────────────────────────────────────────────────────


def load_templates(settings) -> List[Template]:
    """Charge et valide les templates depuis les settings."""
    raw_list = settings.get(KEY_TEMPLATES, []) or []
    templates = []  # type: List[Template]
    for raw in raw_list:
        template = Template.from_setting(raw)
        if template is not None:
            templates.append(template)
    return templates


def expand_directory(path: str) -> str:
    """Résout ${packages}, ~ et les variables d'environnement d'un chemin."""
    if PACKAGES_VAR in path:
        path = path.replace(PACKAGES_VAR, sublime.packages_path())
    return os.path.normpath(os.path.expandvars(os.path.expanduser(path)))


def parse_snippet_file(path: str) -> Optional[Template]:
    """Construit un Template depuis un fichier .sublime-snippet (XML).

    Format officiel : <snippet><content><![CDATA[...]]></content>
    <description>...</description></snippet>.
    Caption = <description> si présente, sinon le nom du fichier.

    Returns:
        Le Template, ou None si le fichier est illisible (warning loggé).
    """
    try:
        root = ET.parse(path).getroot()
        content = root.findtext("content")
        if content is None or not content.strip():
            raise ValueError("balise <content> absente ou vide")
    except (ET.ParseError, OSError, ValueError) as exc:
        logger.warning(
            error_message(ErrorCode.SNIPPET_PARSE_FAILED, path=path, reason=exc)
        )
        return None
    filename = os.path.basename(path)
    stem = filename[: -len(SNIPPET_EXTENSION)]
    description = (root.findtext("description") or "").strip()
    return Template(
        caption=description or stem,
        command=content.strip(),
        description=filename,
        source=Template.SOURCE_SNIPPET,
    )


def load_snippet_templates(settings) -> List[Template]:
    """Charge les templates depuis les répertoires de snippets configurés.

    Les répertoires inexistants sont ignorés avec un warning ; les
    fichiers sont chargés par ordre alphabétique.
    """
    directories = settings.get(KEY_SNIPPET_DIRS, DEFAULT_SNIPPET_DIRS) or []
    templates = []  # type: List[Template]
    for raw_dir in directories:
        directory = expand_directory(str(raw_dir))
        if not os.path.isdir(directory):
            logger.warning(
                error_message(ErrorCode.SNIPPET_DIR_NOT_FOUND, path=directory)
            )
            continue
        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(SNIPPET_EXTENSION):
                continue
            template = parse_snippet_file(os.path.join(directory, filename))
            if template is not None:
                templates.append(template)
    return templates


def resolve_mode(settings) -> str:
    """Résout le mode de placeholders avec validation et repli sur défaut."""
    mode = settings.get(KEY_PLACEHOLDER_MODE, DEFAULT_PLACEHOLDER_MODE)
    if mode not in VALID_MODES:
        logger.warning(error_message(ErrorCode.CONFIG_INVALID_MODE, mode=mode))
        sublime.status_message(error_message(ErrorCode.CONFIG_INVALID_MODE, mode=mode))
        return DEFAULT_PLACEHOLDER_MODE
    return mode
