"""Tests du domaine AlfacoAwsCli : Template et Placeholder."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())
sys.modules.setdefault("sublime_plugin", MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from AlfacoAwsCli.domain import Placeholder, Template  # noqa: E402


def test_placeholder_prompt_without_default():
    assert Placeholder("region").prompt() == "region"


def test_placeholder_prompt_with_default():
    assert Placeholder("region", "eu-west-3").prompt() == "region (défaut : eu-west-3)"


def test_placeholders_extracted_in_order():
    tpl = Template("c", "aws s3 cp ${source} s3://${bucket}/${key}")
    assert [p.name for p in tpl.placeholders()] == ["source", "bucket", "key"]


def test_placeholders_unique_keeps_first_default():
    # ${region} sans défaut puis avec défaut → le défaut est récupéré, une seule entrée
    tpl = Template("c", "a ${region} b ${region:eu-west-3}")
    placeholders = tpl.placeholders()
    assert len(placeholders) == 1
    assert placeholders[0].name == "region"
    assert placeholders[0].default == "eu-west-3"


def test_placeholders_none_when_no_placeholder():
    assert Template("c", "aws sts get-caller-identity").placeholders() == []


def test_from_setting_valid():
    tpl = Template.from_setting({"caption": "C", "command": "aws s3 ls", "description": "D"})
    assert tpl is not None
    assert tpl.caption == "C" and tpl.command == "aws s3 ls" and tpl.description == "D"


def test_from_setting_missing_command_returns_none():
    assert Template.from_setting({"caption": "C"}) is None


def test_from_setting_not_a_dict_returns_none():
    assert Template.from_setting("nope") is None
