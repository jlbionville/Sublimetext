"""Tests de la logique applicative AlfacoAwsCli (engine)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from AlfacoAwsCli.domain import Template  # noqa: E402
from AlfacoAwsCli import engine  # noqa: E402


class _Settings:
    """Faux sublime.Settings : un simple dict avec .get(key, default)."""

    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)


# ── tokenize_selection ───────────────────────────────────────────────────


def test_tokenize_simple_spaces():
    assert engine.tokenize_selection("i-0abc eu-west-1") == ["i-0abc", "eu-west-1"]


def test_tokenize_quotes_group_token():
    assert engine.tokenize_selection('vol-0 "avant migration"') == ["vol-0", "avant migration"]


def test_tokenize_unbalanced_quote_falls_back_to_split():
    # shlex lève ValueError sur guillemet non fermé → repli sur split()
    assert engine.tokenize_selection('a "b c') == ["a", '"b', "c"]


# ── assign_tokens ──────────────────────────────────────────────────────────


def test_assign_tokens_maps_in_order_and_counts_extra():
    tpl = Template("c", "${a} ${b}")
    values, extra = engine.assign_tokens(tpl.placeholders(), ["1", "2", "3"])
    assert values == {"a": "1", "b": "2"}
    assert extra == 1


def test_assign_tokens_partial_no_extra():
    tpl = Template("c", "${a} ${b}")
    values, extra = engine.assign_tokens(tpl.placeholders(), ["1"])
    assert values == {"a": "1"} and extra == 0


# ── fill_command ───────────────────────────────────────────────────────────


def test_fill_command_uses_values():
    tpl = Template("c", "aws ec2 start-instances --instance-ids ${id} --region ${region:eu-west-3}")
    assert engine.fill_command(tpl, {"id": "i-0", "region": "eu-west-1"}) == (
        "aws ec2 start-instances --instance-ids i-0 --region eu-west-1"
    )


def test_fill_command_falls_back_to_default_then_name():
    tpl = Template("c", "${id} ${region:eu-west-3}")
    # id sans valeur ni défaut → son nom ; region sans valeur → son défaut
    assert engine.fill_command(tpl, {}) == "id eu-west-3"


# ── to_sublime_snippet ─────────────────────────────────────────────────────


def test_to_sublime_snippet_numbers_fields():
    tpl = Template("c", "aws s3 cp ${source} s3://${bucket}/${key}")
    assert engine.to_sublime_snippet(tpl) == "aws s3 cp ${1:source} s3://${2:bucket}/${3:key}"


def test_to_sublime_snippet_uses_defaults_as_field_values():
    tpl = Template("c", "x ${region:eu-west-3}")
    assert engine.to_sublime_snippet(tpl) == "x ${1:eu-west-3}"


def test_to_sublime_snippet_prefilled_value_is_literal():
    tpl = Template("c", "${a} ${b}")
    assert engine.to_sublime_snippet(tpl, {"a": "X"}) == "X ${1:b}"


def test_to_sublime_snippet_escapes_literal_dollar():
    tpl = Template("c", "echo $HOME ${name}")
    # le $HOME littéral est échappé pour ne pas être interprété par Sublime
    assert engine.to_sublime_snippet(tpl) == "echo \\$HOME ${1:name}"


# ── batch_fill ─────────────────────────────────────────────────────────────


def test_batch_fill_one_command_per_line():
    tpl = Template("c", "aws ec2 stop-instances --instance-ids ${id} --region ${region:eu-west-3}")
    lines = ["i-0abc eu-west-1", "i-0def"]
    commands, extra, incomplete = engine.batch_fill(tpl, lines)
    assert commands == [
        "aws ec2 stop-instances --instance-ids i-0abc --region eu-west-1",
        "aws ec2 stop-instances --instance-ids i-0def --region eu-west-3",
    ]
    assert extra == 0
    assert incomplete == 1  # 2e ligne : region manquante → défaut appliqué


def test_batch_fill_counts_extra_tokens():
    tpl = Template("c", "${id}")
    commands, extra, incomplete = engine.batch_fill(tpl, ["a b c"])
    assert commands == ["a"] and extra == 2 and incomplete == 0


# ── load_templates ─────────────────────────────────────────────────────────


def test_load_templates_filters_invalid_entries():
    settings = _Settings({"templates": [
        {"caption": "ok", "command": "aws s3 ls"},
        {"caption": "bad"},          # pas de command → ignoré
        {"command": "aws ec2 ..."},  # pas de caption → ignoré
    ]})
    templates = engine.load_templates(settings)
    assert len(templates) == 1 and templates[0].caption == "ok"


def test_load_templates_empty_when_missing_key():
    assert engine.load_templates(_Settings({})) == []
