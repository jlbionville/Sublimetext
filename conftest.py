"""Stub du module Sublime Text pour les tests pytest hors Sublime."""
import sys
from unittest.mock import MagicMock

# Stub des modules Sublime utilisés par AlfacoLib et les plugins
sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
