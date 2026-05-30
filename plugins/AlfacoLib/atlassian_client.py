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


def wrap_description_as_adf(payload):
    """Convertit payload["fields"]["description"] en Atlassian Document Format
    si c'est encore une chaîne.

    L'API Jira v3 refuse les descriptions plain-string et exige un document ADF
    (`{type:"doc", version:1, content:[{type:"paragraph",content:[...]}]}`).
    Pour permettre à l'utilisateur d'écrire du texte plat dans le snippet, on
    enveloppe automatiquement avant POST.

    Idempotent : si la description est déjà un dict (déjà ADF), absente, ou
    si le payload n'a pas de `fields`, on retourne le payload tel quel.
    Sépare en paragraphes sur les doubles-newlines.
    """
    fields = payload.get("fields")
    if not isinstance(fields, dict):
        return payload
    desc = fields.get("description")
    if not isinstance(desc, str):
        return payload
    paragraphs = [p for p in desc.split("\n\n") if p.strip()]
    fields["description"] = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": p}]}
            for p in paragraphs
        ] or [{"type": "paragraph", "content": []}],
    }
    return payload


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


def parse_issue_type_names(data):
    """Extrait les noms de types d'issues d'une réponse Jira.

    `data` est l'objet projet décodé (dict) issu de
    `GET /project/{key}?expand=issueTypes`, avec une clé `issueTypes` (liste).
    Tolère aussi une liste de types passée directement.

    Retourne la liste des noms, dédupliquée (premier vu gagné) et dans l'ordre
    d'apparition. Inclut les types `subtask`. Ignore les entrées sans `name`
    non vide. Retourne `[]` si `data` est None/vide/mal formé.
    """
    if isinstance(data, dict):
        types = data.get("issueTypes") or []
    elif isinstance(data, list):
        types = data
    else:
        return []

    names = []
    seen = set()
    for t in types:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names
