"""Tests du logger Alfaco."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.logger import get_logger  # noqa: E402


def test_logger_debug_silent_when_debug_off(capsys):
    log = get_logger("X", debug=False)
    log.debug("hello")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_logger_debug_prints_with_prefix_when_debug_on(capsys):
    log = get_logger("X", debug=True)
    log.debug("hello")
    captured = capsys.readouterr()
    assert "[Alfaco][X] hello" in captured.out


def test_logger_info_always_prints(capsys):
    """info() doit toujours sortir : c'est le niveau pour les étapes normales
    (organisation choisie, projet sélectionné, etc.). Le legacy le gateait
    derrière debug, ce qui masquait les commandes user-triggered."""
    log = get_logger("X", debug=False)
    log.info("user did something")
    captured = capsys.readouterr()
    assert "[Alfaco][X][INFO] user did something" in captured.out


def test_logger_warn_always_prints(capsys):
    log = get_logger("X", debug=False)
    log.warn("oops")
    captured = capsys.readouterr()
    assert "[Alfaco][X][WARN] oops" in captured.out


def test_logger_error_always_prints(capsys):
    """error() est utilisé par les commandes pour les échecs HTTP/exceptions
    (souvent combiné avec sublime.error_message côté UI)."""
    log = get_logger("X", debug=False)
    log.error("boom")
    captured = capsys.readouterr()
    assert "[Alfaco][X][ERROR] boom" in captured.out
