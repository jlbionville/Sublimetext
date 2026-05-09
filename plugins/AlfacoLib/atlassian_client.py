# -*- coding: utf-8 -*-
"""Wrapper REST minimal pour les API Atlassian.

Substitut moderne de modules/tools.py :
- verify TLS configurable (défaut True)
- timeout configurable (défaut connect=5s, read=30s)
- exceptions remontées au lieu d'être masquées
"""
from __future__ import annotations

import requests


DEFAULT_TIMEOUT = (5, 30)


def call_rest(url, body, auth, headers, verb="GET", verify=True, timeout=DEFAULT_TIMEOUT):
    """Effectue une requête HTTP authentifiée et retourne la `requests.Response`.

    Aucun parsing : l'appelant décide quoi faire de la réponse.
    """
    return requests.request(
        verb,
        url,
        headers=headers,
        auth=auth,
        data=body,
        verify=verify,
        timeout=timeout,
    )


def list_projects(url, auth, headers, verify=True, timeout=DEFAULT_TIMEOUT):
    """Récupère la liste des projets Jira sous la forme ['KEY-Nom', ...].

    Raise:
        RuntimeError si le serveur ne répond pas 200.
    """
    response = requests.get(url, auth=auth, headers=headers, verify=verify, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"GET {url} → {response.status_code} : {response.text[:200]}"
        )
    return [f"{p['key']}-{p['name']}" for p in response.json()]
