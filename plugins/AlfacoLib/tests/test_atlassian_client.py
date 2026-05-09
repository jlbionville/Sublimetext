"""Tests du wrapper REST Atlassian."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("sublime", MagicMock())

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.atlassian_client import call_rest, list_projects  # noqa: E402

import requests_mock


def test_call_rest_get_passes_auth_headers_and_returns_response():
    auth = ("alice", "tok")
    with requests_mock.Mocker() as m:
        m.get("https://acme.atlassian.net/rest/api/3/issue/X-1", json={"key": "X-1"})
        result = call_rest(
            "https://acme.atlassian.net/rest/api/3/issue/X-1",
            body=None,
            auth=auth,
            headers={"Accept": "application/json"},
            verb="GET",
        )
    assert result.status_code == 200
    assert result.json() == {"key": "X-1"}
    assert m.last_request.headers["Authorization"].startswith("Basic ")


def test_call_rest_post_sends_body():
    with requests_mock.Mocker() as m:
        m.post("https://acme.atlassian.net/rest/api/3/issue/", json={"key": "X-2"}, status_code=201)
        result = call_rest(
            "https://acme.atlassian.net/rest/api/3/issue/",
            body='{"fields": {}}',
            auth=("alice", "tok"),
            headers={"Content-type": "application/json"},
            verb="POST",
        )
    assert result.status_code == 201
    assert m.last_request.text == '{"fields": {}}'


def test_call_rest_passes_timeout(monkeypatch):
    captured = {}

    def fake_request(verb, url, **kwargs):
        captured.update(kwargs)
        resp = MagicMock(status_code=200)
        return resp

    monkeypatch.setattr("AlfacoLib.atlassian_client.requests.request", fake_request)
    call_rest("u", body=None, auth=("a", "b"), headers={}, verb="GET")
    assert captured["timeout"] == (5, 30)
    assert captured["verify"] is True


def test_call_rest_verify_can_be_overridden(monkeypatch):
    captured = {}

    def fake_request(verb, url, **kwargs):
        captured.update(kwargs)
        return MagicMock(status_code=200)

    monkeypatch.setattr("AlfacoLib.atlassian_client.requests.request", fake_request)
    call_rest("u", body=None, auth=("a", "b"), headers={}, verb="GET", verify=False)
    assert captured["verify"] is False


def test_list_projects_returns_key_name_pairs():
    with requests_mock.Mocker() as m:
        m.get(
            "https://acme.atlassian.net/rest/api/3/project/",
            json=[{"key": "BUS", "name": "Business"}, {"key": "DEV", "name": "Dev"}],
        )
        result = list_projects(
            "https://acme.atlassian.net/rest/api/3/project/",
            auth=("alice", "tok"),
            headers={"Accept": "application/json"},
        )
    assert result == ["BUS-Business", "DEV-Dev"]


def test_list_projects_raises_on_http_error():
    with requests_mock.Mocker() as m:
        m.get("https://acme.atlassian.net/rest/api/3/project/", status_code=401, text="unauth")
        try:
            list_projects(
                "https://acme.atlassian.net/rest/api/3/project/",
                auth=("alice", "tok"),
                headers={},
            )
        except RuntimeError as e:
            assert "401" in str(e)
        else:
            assert False, "RuntimeError attendue"
