# -*- coding: utf-8 -*-
"""Commande : exécuter la sélection courante comme commande shell.

Adapter Sublime : lit la sélection, lance le process en async (subprocess),
écrit le résultat dans un buffer scratch. Toute la logique pure vit dans
:mod:`AlfacoShell.domain`.
"""
import subprocess

import sublime
import sublime_plugin

from AlfacoShell import constants
from AlfacoShell.domain import format_result, resolve_exec_argv
from AlfacoShell.errors import ErrorCode, error_message


class AlfacoShellRunSelectionCommand(sublime_plugin.TextCommand):
    """Exécute la sélection courante comme commande shell (multi-OS)."""

    def run(self, edit):
        cmd_text = self._selected_text()
        if not cmd_text:
            sublime.status_message(error_message(ErrorCode.SELECTION_EMPTY))
            return
        sublime.status_message(constants.PLUGIN_NAME + " : exécution…")
        sublime.set_timeout_async(lambda: self._run_async(cmd_text), 0)

    def is_enabled(self):
        return any(not r.empty() for r in self.view.sel())

    def _selected_text(self):
        regions = [r for r in self.view.sel() if not r.empty()]
        return "\n".join(self.view.substr(r) for r in regions).strip()

    def _run_async(self, cmd_text):
        settings = sublime.load_settings(constants.SETTINGS_FILE)
        argv = resolve_exec_argv(cmd_text, settings, sublime.platform())
        timeout = settings.get(constants.KEY_TIMEOUT, constants.DEFAULT_TIMEOUT_SECONDS)
        try:
            proc = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            out = proc.stdout.decode("utf-8", "replace")
            err = proc.stderr.decode("utf-8", "replace")
            result = format_result(out, err, proc.returncode)
        except subprocess.TimeoutExpired:
            result = error_message(ErrorCode.EXEC_TIMEOUT)
        except Exception as exc:  # noqa: BLE001 — reporté dans le buffer
            result = error_message(ErrorCode.EXEC_FAILED, str(exc))
        sublime.set_timeout(lambda: self._show(cmd_text, result), 0)

    def _show(self, cmd_text, result):
        window = self.view.window()
        out = window.new_file()
        out.set_scratch(True)
        out.set_name(constants.OUTPUT_TITLE_PREFIX + cmd_text[: constants.OUTPUT_TITLE_MAXLEN])
        out.assign_syntax(constants.OUTPUT_SYNTAX)
        out.run_command("append", {"characters": result})
        out.set_read_only(True)
