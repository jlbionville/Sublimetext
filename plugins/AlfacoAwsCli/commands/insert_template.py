# -*- coding: utf-8 -*-
"""Commande principale : choisir un template AWS CLI puis l'insérer.

Déclenchée par clic droit, menu Tools → Alfaco → AWS CLI, ou Command
Palette. Gère les deux modes de placeholders (``snippet`` / ``guided``),
la sélection → paramètres et le mode batch (une commande par ligne).
"""
import logging
from typing import List

import sublime
import sublime_plugin

from AlfacoAwsCli import constants, engine
from AlfacoAwsCli.domain import Placeholder, Template
from AlfacoAwsCli.errors import (
    BATCH_SUMMARY_LABEL,
    ErrorCode,
    error_message,
)

logger = logging.getLogger(__name__)


class AlfacoAwsCliInsertTemplateCommand(sublime_plugin.WindowCommand):
    """Affiche le quick panel des templates puis insère la sélection.

    Déclenchée par : clic droit, menu Tools, Command Palette.
    """

    def run(self) -> None:
        settings = sublime.load_settings(constants.SETTINGS_FILE)
        self._templates = (
            engine.load_templates(settings)
            + engine.load_snippet_templates(settings)
        )
        self._mode = engine.resolve_mode(settings)
        self._trailing_newline = bool(
            settings.get(constants.KEY_TRAILING_NEWLINE, constants.DEFAULT_TRAILING_NEWLINE)
        )
        self._selection_as_params = bool(
            settings.get(constants.KEY_SELECTION_AS_PARAMS, constants.DEFAULT_SELECTION_AS_PARAMS)
        )
        show_descriptions = bool(
            settings.get(constants.KEY_SHOW_DESCRIPTIONS, constants.DEFAULT_SHOW_DESCRIPTIONS)
        )

        if not self._templates:
            sublime.error_message(error_message(ErrorCode.TEMPLATES_EMPTY))
            return

        if show_descriptions:
            items = []
            for t in self._templates:
                is_snippet = t.source == Template.SOURCE_SNIPPET
                items.append(
                    sublime.QuickPanelItem(
                        trigger=t.caption,
                        details=t.description,
                        annotation=(
                            "snippet"
                            if is_snippet
                            else (t.command if len(t.command) <= 80 else "")
                        ),
                        kind=(
                            sublime.KIND_SNIPPET
                            if is_snippet
                            else sublime.KIND_AMBIGUOUS
                        ),
                    )
                )
        else:
            items = [t.caption for t in self._templates]

        self.window.show_quick_panel(
            items,
            self._on_template_chosen,
            placeholder="Template AWS CLI…",
        )

    def is_enabled(self) -> bool:
        view = self.window.active_view()
        return view is not None and not view.is_read_only()

    # ── Sélection du template ────────────────────────────────────────────

    def _on_template_chosen(self, index: int) -> None:
        if index < 0:  # panel annulé (Échap)
            return
        view = self.window.active_view()
        if view is None:
            sublime.error_message(error_message(ErrorCode.VIEW_NOT_FOUND))
            return
        if view.is_read_only():
            sublime.error_message(error_message(ErrorCode.VIEW_READ_ONLY))
            return

        template = self._templates[index]

        # Mode batch : la sélection couvre plusieurs lignes non vides
        # (ou plusieurs régions multi-curseurs) → une commande par ligne.
        if self._selection_as_params and self._run_batch(view, template):
            return

        initial_values = self._values_from_selection(view, template)
        placeholders = template.placeholders()
        remaining = [p for p in placeholders if not initial_values.get(p.name)]

        if self._mode == constants.MODE_GUIDED and remaining:
            self._run_guided(view, template, initial_values, remaining)
        elif remaining:
            self._insert_snippet(view, template, initial_values)
        else:
            # Tous les placeholders sont couverts par la sélection
            self._insert_filled(view, template, initial_values)

    # ── Sélection de l'éditeur → valeurs de placeholders ─────────────────

    def _run_batch(self, view: sublime.View, template: Template) -> bool:
        """Applique le template à chaque ligne non vide de la sélection.

        Chaque région de sélection est traitée indépendamment (support
        multi-curseurs) et remplacée par ses commandes générées, une par
        ligne de paramètres.

        Returns:
            True si le mode batch s'applique (≥ 2 lignes non vides au
            total), False sinon — l'appelant poursuit en mode normal.
        """
        regions = [r for r in view.sel() if not r.empty()]
        if not regions:
            return False
        lines_per_region = [
            [line for line in view.substr(r).splitlines() if line.strip()]
            for r in regions
        ]
        total = sum(len(lines) for lines in lines_per_region)
        if total < 2:
            return False

        texts = []  # type: List[str]
        extra_total = 0
        incomplete_total = 0
        for lines in lines_per_region:
            commands, extra, incomplete = engine.batch_fill(template, lines)
            extra_total += extra
            incomplete_total += incomplete
            text = "\n".join(commands)
            if self._trailing_newline:
                text += "\n"
            texts.append(text)

        view.run_command("alfaco_aws_cli_replace_regions", {"texts": texts})
        summary = BATCH_SUMMARY_LABEL.format(
            plugin=constants.PLUGIN_NAME,
            count=total,
            extra=extra_total,
            incomplete=incomplete_total,
        )
        logger.info(summary)
        sublime.status_message(summary)
        return True

    def _values_from_selection(self, view: sublime.View, template: Template) -> dict:
        """Mappe les tokens de la sélection sur les placeholders du template.

        Les tokens (séparés par des espaces, guillemets supportés) sont
        affectés aux placeholders dans leur ordre d'apparition. Les
        tokens excédentaires sont ignorés avec un avertissement.
        """
        if not self._selection_as_params:
            return {}
        selected = ""
        for region in view.sel():
            if not region.empty():
                selected = view.substr(region)
                break
        if not selected.strip():
            return {}
        placeholders = template.placeholders()
        values, extra = engine.assign_tokens(placeholders, engine.tokenize_selection(selected))
        if extra:
            message = error_message(
                ErrorCode.SELECTION_EXTRA_TOKENS,
                extra=extra,
                expected=len(placeholders),
            )
            logger.warning(message)
            sublime.status_message(message)
        return values

    # ── Insertion directe (tous les placeholders résolus) ────────────────

    def _insert_filled(self, view: sublime.View, template: Template, values: dict) -> None:
        command = engine.fill_command(template, values)
        if self._trailing_newline:
            command += "\n"
        view.run_command("alfaco_aws_cli_insert_text", {"text": command})

    # ── Mode snippet : champs Tab natifs ─────────────────────────────────

    def _insert_snippet(self, view: sublime.View, template: Template, values=None) -> None:
        snippet = engine.to_sublime_snippet(template, values)
        if self._trailing_newline:
            snippet += "\n"
        view.run_command("insert_snippet", {"contents": snippet})

    # ── Mode guidé : un input panel par placeholder restant ──────────────

    def _run_guided(
        self,
        view: sublime.View,
        template: Template,
        initial_values: dict,
        remaining: List[Placeholder],
    ) -> None:
        values = dict(initial_values)

        def ask(position: int) -> None:
            if position >= len(remaining):
                self._insert_filled(view, template, values)
                return
            placeholder = remaining[position]

            def on_done(value: str) -> None:
                values[placeholder.name] = value.strip()
                ask(position + 1)

            self.window.show_input_panel(
                placeholder.prompt(),
                placeholder.default or "",
                on_done,
                None,  # on_change
                None,  # on_cancel → abandon silencieux
            )

        ask(0)
