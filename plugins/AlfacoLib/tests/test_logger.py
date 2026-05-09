"""Tests du logger Alfaco."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.logger import get_logger  # noqa: E402


def test_logger_silent_when_debug_off(capsys):
    log = get_logger("X", debug=False)
    log.debug("hello")
    log.info("world")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_logger_prints_with_prefix_when_debug_on(capsys):
    log = get_logger("X", debug=True)
    log.debug("hello")
    captured = capsys.readouterr()
    assert "[Alfaco][X] hello" in captured.out


def test_logger_warn_always_prints(capsys):
    log = get_logger("X", debug=False)
    log.warn("oops")
    captured = capsys.readouterr()
    assert "[Alfaco][X][WARN] oops" in captured.out
