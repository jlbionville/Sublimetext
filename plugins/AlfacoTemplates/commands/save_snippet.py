# -*- coding: utf-8 -*-
"""Commande : enregistrer la sélection courante comme fichier .sublime-snippet."""
import logging
import os

import sublime
import sublime_plugin

from AlfacoTemplates import constants, engine
from AlfacoTemplates.errors import (
    SAVE_DONE_LABEL,
    SAVE_OVERWRITE_QUESTION,
    SAVE_PROMPT_DESCRIPTION,
    SAVE_PROMPT_FILENAME,
    ErrorCode,
    error_message,
)

logger = logging.getLogger(__name__)


class AlfacoTemplatesSaveSnippetCommand(sublime_plugin.WindowCommand):
    """Enregistre la sélection comme fichier .sublime-snippet.

    Flux : sélection → description → nom de fichier (slug pré-rempli)
    → écriture dans le premier répertoire de ``snippet_directories``
    (créé si besoin), avec confirmation explicite avant tout écrasement.
    Le snippet apparaît dans le menu dès la prochaine ouverture.
    """

    def run(self) -> None:
        view = self.window.active_view()
        if view is None:
            sublime.error_message(error_message(ErrorCode.VIEW_NOT_FOUND))
            return
        selected = ""
        for region in view.sel():
            if not region.empty():
                selected = view.substr(region)
                break
        if not selected.strip():
            sublime.status_message(error_message(ErrorCode.SELECTION_EMPTY))
            return
        self._content = selected.strip()

        settings = sublime.load_settings(constants.SETTINGS_FILE)
        directories = (
            settings.get(constants.KEY_SNIPPET_DIRS, constants.DEFAULT_SNIPPET_DIRS)
            or constants.DEFAULT_SNIPPET_DIRS
        )
        self._target_dir = engine.expand_directory(str(directories[0]))

        self.window.show_input_panel(
            SAVE_PROMPT_DESCRIPTION, "", self._on_description, None, None
        )

    def is_enabled(self) -> bool:
        view = self.window.active_view()
        return view is not None and any(not r.empty() for r in view.sel())

    def _on_description(self, description: str) -> None:
        self._description = description.strip()
        self.window.show_input_panel(
            SAVE_PROMPT_FILENAME,
            engine.slugify_filename(self._description) + constants.SNIPPET_EXTENSION,
            self._on_filename,
            None,
            None,
        )

    def _on_filename(self, filename: str) -> None:
        filename = os.path.basename(filename.strip())
        if not filename:
            filename = engine.slugify_filename(self._description) + constants.SNIPPET_EXTENSION
        if not filename.endswith(constants.SNIPPET_EXTENSION):
            filename += constants.SNIPPET_EXTENSION
        path = os.path.join(self._target_dir, filename)

        # Confirmation explicite avant tout écrasement — jamais silencieux.
        if os.path.exists(path) and not sublime.ok_cancel_dialog(
            SAVE_OVERWRITE_QUESTION.format(path=path)
        ):
            return

        try:
            os.makedirs(self._target_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(engine.build_snippet_xml(self._content, self._description))
        except OSError as exc:
            sublime.error_message(
                error_message(ErrorCode.SNIPPET_WRITE_FAILED, path=path, reason=exc)
            )
            return

        message = SAVE_DONE_LABEL.format(plugin=constants.PLUGIN_NAME, path=path)
        logger.info(message)
        sublime.status_message(message)
        self.window.open_file(path)
