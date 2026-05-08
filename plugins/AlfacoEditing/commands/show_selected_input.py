# -*- coding: utf-8 -*-
"""Ouvre une input panel (correction du bug nput_view du legacy)."""
import sublime
import sublime_plugin


class ShowSelectedInputCommand(sublime_plugin.WindowCommand):
    def run(self):
        input_view = self.window.show_input_panel(
            caption="Example",
            initial_text="Example",
            on_done=None,
            on_change=None,
            on_cancel=None,
        )
        input_view.add_regions(
            "example",
            [sublime.Region(0, 7)],
            scope="region.redish",
            flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SQUIGGLY_UNDERLINE,
        )
