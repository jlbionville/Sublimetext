# -*- coding: utf-8 -*-
"""Wrapper REST minimal pour les API Atlassian.

Substitut moderne de modules/tools.py :
- verify TLS configurable (defaut True)
- timeout configurable (defaut connect=5s, read=30s, somme passee a urllib)
- exceptions remontees au lieu d'etre masquees

Implemente avec urllib (stdlib) : le plugin host Sublime Text 4 ne livre
pas `requests`, et on ne veut pas dependre d'une installation Package
Control supplementaire.
"""
from __future__ import annotations

import base64
import json as _json
import ssl
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = (5, 30)


class Response:
    """Reponse HTTP minimale, interface compatible avec ce qu'attendent les
    consommateurs : `status_code`, `text`, `json()`."""

    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return _json.loads(self.text)


def _basic_auth_header(auth):
    login, password = auth
    raw = f"{login}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _ssl_context(verify):
    ctx = ssl.create_default_context()
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _to_seconds(timeout):
    if isinstance(timeout, tuple):
        return sum(timeout)
    return timeout


def call_rest(url, body, auth, headers, verb="GET", verify=True, timeout=DEFAULT_TIMEOUT):
    """Effectue une requete HTTP authentifiee et retourne une `Response`.

    `body` peut etre str, bytes ou None.
    Les erreurs HTTP (4xx/5xx) sont retournees comme une `Response` ; les
    erreurs reseau remontent telles quelles (URLError, socket.timeout, ...).
    """
    h = dict(headers or {})
    h["Authorization"] = _basic_auth_header(auth)

    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body

    req = Request(url, data=data, headers=h, method=verb.upper())
    try:
        with urlopen(req, timeout=_to_seconds(timeout), context=_ssl_context(verify)) as resp:
            return Response(resp.status, resp.read().decode("utf-8"))
    except HTTPError as e:
        return Response(e.code, e.read().decode("utf-8", errors="replace"))


def list_projects(url, auth, headers, verify=True, timeout=DEFAULT_TIMEOUT):
    """Recupere la liste des projets Jira sous la forme ['KEY-Nom', ...].

    Raise:
        RuntimeError si le serveur ne repond pas 200.
    """
    response = call_rest(
        url,
        body=None,
        auth=auth,
        headers=headers,
        verb="GET",
        verify=verify,
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"GET {url} -> {response.status_code} : {response.text[:200]}"
        )
    return [f"{p['key']}-{p['name']}" for p in response.json()]
