# -*- coding: utf-8 -*-
"""Logger minimal pour les plugins Alfaco.

Remplace les print() bruts disséminés dans le code legacy.
"""
from __future__ import annotations


class _Logger:
    def __init__(self, name, debug):
        self._name = name
        self._debug = debug

    def debug(self, msg):
        if self._debug:
            print(f"[Alfaco][{self._name}] {msg}")

    def info(self, msg):
        print(f"[Alfaco][{self._name}][INFO] {msg}")

    def warn(self, msg):
        print(f"[Alfaco][{self._name}][WARN] {msg}")

    def error(self, msg):
        print(f"[Alfaco][{self._name}][ERROR] {msg}")


def get_logger(name, debug=False):
    return _Logger(name, bool(debug))
