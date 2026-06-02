# -*- coding: utf-8 -*-
from AlfacoLib.jira_popup import (
    build_browse_url,
    project_from_key,
    build_creation_popup_html,
)


def test_build_browse_url():
    assert build_browse_url("mysite", "MMPO-123") == \
        "https://mysite.atlassian.net/browse/MMPO-123"


def test_project_from_key_standard():
    assert project_from_key("MMPO-123") == "MMPO"


def test_project_from_key_without_dash():
    assert project_from_key("ABC") == "ABC"


def test_project_from_key_multiple_dashes():
    # le projet est le préfixe avant le dernier '-'
    assert project_from_key("MM-PO-123") == "MM-PO"


def test_build_creation_popup_html_contains_key_project_and_href():
    html = build_creation_popup_html(
        "MMPO-123", "MMPO", "https://mysite.atlassian.net/browse/MMPO-123"
    )
    assert "MMPO-123" in html
    assert "MMPO" in html
    assert 'href="https://mysite.atlassian.net/browse/MMPO-123"' in html
