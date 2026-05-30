"""Tests du wrapper REST Atlassian (urllib-based)."""
import io
import ssl
import sys
from pathlib import Path
from unittest.mock import MagicMock
from urllib.error import HTTPError

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.atlassian_client import (  # noqa: E402
    call_rest,
    list_projects,
    wrap_description_as_adf,
    _basic_auth_header,
)
from AlfacoLib import atlassian_client  # noqa: E402


def _fake_urlopen_cm(status, body):
    """Fabrique un context manager qui imite urlopen()."""
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = body.encode("utf-8") if isinstance(body, str) else body
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


def test_basic_auth_header_format():
    # alice:tok -> base64("alice:tok") = "YWxpY2U6dG9r"
    assert _basic_auth_header(("alice", "tok")) == "Basic YWxpY2U6dG9r"


def test_call_rest_get_passes_auth_headers_and_returns_response(monkeypatch):
    captured = {}

    def fake(req, timeout=None, context=None):
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        captured["method"] = req.get_method()
        return _fake_urlopen_cm(200, '{"key": "X-1"}')

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    result = call_rest(
        "https://acme.atlassian.net/rest/api/3/issue/X-1",
        body=None,
        auth=("alice", "tok"),
        headers={"Accept": "application/json"},
        verb="GET",
    )
    assert result.status_code == 200
    assert result.json() == {"key": "X-1"}
    assert captured["headers"]["authorization"].startswith("Basic ")
    assert captured["headers"]["accept"] == "application/json"
    assert captured["method"] == "GET"


def test_call_rest_post_sends_body(monkeypatch):
    captured = {}

    def fake(req, timeout=None, context=None):
        captured["data"] = req.data
        captured["method"] = req.get_method()
        return _fake_urlopen_cm(201, '{"key": "X-2"}')

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    result = call_rest(
        "https://acme.atlassian.net/rest/api/3/issue/",
        body='{"fields": {}}',
        auth=("alice", "tok"),
        headers={"Content-type": "application/json"},
        verb="POST",
    )
    assert result.status_code == 201
    assert captured["data"] == b'{"fields": {}}'
    assert captured["method"] == "POST"


def test_call_rest_passes_default_timeout_and_verify(monkeypatch):
    captured = {}

    def fake(req, timeout=None, context=None):
        captured["timeout"] = timeout
        captured["context"] = context
        return _fake_urlopen_cm(200, "")

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    call_rest("https://x", body=None, auth=("a", "b"), headers={}, verb="GET")
    # default DEFAULT_TIMEOUT=(5, 30) -> sum = 35
    assert captured["timeout"] == 35
    # default verify=True -> hostname check active
    assert captured["context"].check_hostname is True
    assert captured["context"].verify_mode == ssl.CERT_REQUIRED


def test_call_rest_verify_false_disables_tls_check(monkeypatch):
    captured = {}

    def fake(req, timeout=None, context=None):
        captured["context"] = context
        return _fake_urlopen_cm(200, "")

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    call_rest("https://x", body=None, auth=("a", "b"), headers={}, verb="GET", verify=False)
    assert captured["context"].check_hostname is False
    assert captured["context"].verify_mode == ssl.CERT_NONE


def test_call_rest_returns_response_on_http_error(monkeypatch):
    def fake(req, timeout=None, context=None):
        raise HTTPError(req.full_url, 404, "Not Found", {}, io.BytesIO(b'{"err":"x"}'))

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    result = call_rest("https://x/a", body=None, auth=("a", "b"), headers={}, verb="GET")
    assert result.status_code == 404
    assert result.json() == {"err": "x"}


def test_list_projects_returns_key_name_pairs(monkeypatch):
    def fake(req, timeout=None, context=None):
        body = '[{"key":"BUS","name":"Business"},{"key":"DEV","name":"Dev"}]'
        return _fake_urlopen_cm(200, body)

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    result = list_projects(
        "https://acme.atlassian.net/rest/api/3/project/",
        auth=("alice", "tok"),
        headers={"Accept": "application/json"},
    )
    assert result == ["BUS-Business", "DEV-Dev"]


def test_wrap_description_converts_string_to_adf():
    """L'API Jira v3 exige description au format ADF (doc/paragraph/text).
    On laisse l'utilisateur écrire du texte plat dans le snippet et on
    enveloppe automatiquement avant POST."""
    payload = {"fields": {"description": "hello", "summary": "x"}}
    result = wrap_description_as_adf(payload)
    assert result["fields"]["description"] == {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}
        ],
    }
    assert result["fields"]["summary"] == "x"


def test_wrap_description_keeps_existing_adf_dict_unchanged():
    """Si l'utilisateur a déjà fourni une description ADF (dict),
    on ne touche à rien — idempotent."""
    adf = {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "x"}]}],
    }
    payload = {"fields": {"description": adf}}
    result = wrap_description_as_adf(payload)
    assert result["fields"]["description"] is adf


def test_wrap_description_noop_when_missing():
    payload = {"fields": {"summary": "x"}}
    result = wrap_description_as_adf(payload)
    assert "description" not in result["fields"]


def test_wrap_description_splits_paragraphs_on_double_newline():
    payload = {"fields": {"description": "para 1\n\npara 2"}}
    result = wrap_description_as_adf(payload)
    content = result["fields"]["description"]["content"]
    assert len(content) == 2
    assert content[0]["content"][0]["text"] == "para 1"
    assert content[1]["content"][0]["text"] == "para 2"


def test_wrap_description_handles_empty_string():
    """Une description vide donne un doc avec un paragraphe vide
    (Jira refuse un `content` totalement vide)."""
    payload = {"fields": {"description": ""}}
    result = wrap_description_as_adf(payload)
    assert result["fields"]["description"] == {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": []}],
    }


def test_wrap_description_noop_when_fields_missing():
    """Payload mal formé : pas de `fields`. Ne pas planter."""
    payload = {"foo": "bar"}
    result = wrap_description_as_adf(payload)
    assert result == {"foo": "bar"}


def test_list_projects_raises_on_http_error(monkeypatch):
    def fake(req, timeout=None, context=None):
        raise HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"unauth"))

    monkeypatch.setattr("AlfacoLib.atlassian_client.urlopen", fake)
    try:
        list_projects(
            "https://acme.atlassian.net/rest/api/3/project/",
            auth=("alice", "tok"),
            headers={},
        )
    except RuntimeError as e:
        assert "401" in str(e)
        assert "unauth" in str(e)
    else:
        assert False, "RuntimeError attendue"


def test_parse_issue_type_names_from_project_object():
    data = {
        "key": "GDQ",
        "issueTypes": [
            {"id": "1", "name": "Tâche", "subtask": False},
            {"id": "2", "name": "Sous-tâche", "subtask": True},
            {"id": "3", "name": "Story", "subtask": False},
        ],
    }
    assert atlassian_client.parse_issue_type_names(data) == [
        "Tâche",
        "Sous-tâche",
        "Story",
    ]


def test_parse_issue_type_names_deduplicates_by_name_preserving_order():
    data = {
        "issueTypes": [
            {"id": "10105", "name": "Tâche"},
            {"id": "10179", "name": "Story"},
            {"id": "10180", "name": "Tâche"},
            {"id": "10181", "name": "Epic"},
        ]
    }
    assert atlassian_client.parse_issue_type_names(data) == [
        "Tâche",
        "Story",
        "Epic",
    ]


def test_parse_issue_type_names_accepts_direct_list():
    data = [{"name": "Bug"}, {"name": "Task"}]
    assert atlassian_client.parse_issue_type_names(data) == ["Bug", "Task"]


def test_parse_issue_type_names_empty_or_missing():
    assert atlassian_client.parse_issue_type_names({}) == []
    assert atlassian_client.parse_issue_type_names({"issueTypes": []}) == []
    assert atlassian_client.parse_issue_type_names(None) == []


def test_parse_issue_type_names_ignores_entries_without_name():
    data = {"issueTypes": [{"id": "1"}, {"name": "Task"}, {"name": ""}]}
    assert atlassian_client.parse_issue_type_names(data) == ["Task"]
