"""Tests du parser Markdown → Jira (ADF)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from AlfacoLib.markdown_to_adf import (  # noqa: E402
    _parse_inline,
    _markdown_to_adf,
    _split_fields,
    KNOWN_FIELDS,
    parse_markdown_jira_template,
)


_DEFAULTS = {
    "project_key": "SDAL",
    "startdate": "2026-05-27",
    "duedate": "2026-06-06",
    "type": "Task",
    "priority": "High",
    "labels": ["important", "urgent"],
}


def test_parse_inline_plain_text():
    """Texte sans marks → un seul text node sans marks."""
    assert _parse_inline("hello world") == [
        {"type": "text", "text": "hello world"}
    ]


def test_parse_inline_empty_string():
    assert _parse_inline("") == []


def test_parse_inline_bold_double_asterisk():
    assert _parse_inline("**bold**") == [
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]}
    ]


def test_parse_inline_bold_double_underscore():
    assert _parse_inline("__bold__") == [
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]}
    ]


def test_parse_inline_bold_with_surrounding_text():
    assert _parse_inline("voici **important** ici") == [
        {"type": "text", "text": "voici "},
        {"type": "text", "text": "important", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " ici"},
    ]


def test_parse_inline_italic_single_asterisk():
    assert _parse_inline("*ital*") == [
        {"type": "text", "text": "ital", "marks": [{"type": "em"}]}
    ]


def test_parse_inline_italic_single_underscore():
    assert _parse_inline("_ital_") == [
        {"type": "text", "text": "ital", "marks": [{"type": "em"}]}
    ]


def test_parse_inline_strong_then_em():
    """**bold** et *italic* → 4 nodes (bold, ' et ', italic) + texte autour."""
    assert _parse_inline("**A** et *B*") == [
        {"type": "text", "text": "A", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " et "},
        {"type": "text", "text": "B", "marks": [{"type": "em"}]},
    ]


def test_parse_inline_code():
    assert _parse_inline("voir `git pull`") == [
        {"type": "text", "text": "voir "},
        {"type": "text", "text": "git pull", "marks": [{"type": "code"}]},
    ]


def test_parse_inline_link():
    assert _parse_inline("[Atlassian](https://x.io)") == [
        {
            "type": "text",
            "text": "Atlassian",
            "marks": [{"type": "link", "attrs": {"href": "https://x.io"}}],
        }
    ]


def test_parse_inline_link_with_surrounding_text():
    assert _parse_inline("voir [doc](http://a) ici") == [
        {"type": "text", "text": "voir "},
        {
            "type": "text",
            "text": "doc",
            "marks": [{"type": "link", "attrs": {"href": "http://a"}}],
        },
        {"type": "text", "text": " ici"},
    ]


def test_block_single_paragraph():
    assert _markdown_to_adf("hello world") == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "hello world"}],
            }
        ],
    }


def test_block_two_paragraphs_separated_by_blank_line():
    md = "para 1\n\npara 2"
    doc = _markdown_to_adf(md)
    assert len(doc["content"]) == 2
    assert doc["content"][0]["content"][0]["text"] == "para 1"
    assert doc["content"][1]["content"][0]["text"] == "para 2"


def test_block_heading_level_2():
    doc = _markdown_to_adf("## Sub-section")
    assert doc["content"] == [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Sub-section"}],
        }
    ]


def test_block_heading_levels_1_to_6():
    for level in range(1, 7):
        md = "#" * level + " Titre"
        doc = _markdown_to_adf(md)
        assert doc["content"][0]["type"] == "heading"
        assert doc["content"][0]["attrs"]["level"] == level


def test_block_paragraph_joins_soft_lines():
    """Sans ligne vide, deux lignes Markdown = un seul paragraphe (joint par espace)."""
    doc = _markdown_to_adf("ligne 1\nligne 2")
    assert doc["content"] == [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "ligne 1 ligne 2"}],
        }
    ]


def test_block_bullet_list_dash():
    doc = _markdown_to_adf("- item 1\n- item 2")
    assert doc["content"] == [
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "item 1"}
                        ]}
                    ],
                },
                {
                    "type": "listItem",
                    "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "item 2"}
                        ]}
                    ],
                },
            ],
        }
    ]


def test_block_bullet_list_star_or_plus():
    """`*` et `+` sont aussi valides comme bullets."""
    for marker in ("*", "+"):
        doc = _markdown_to_adf(f"{marker} foo\n{marker} bar")
        assert doc["content"][0]["type"] == "bulletList"
        assert len(doc["content"][0]["content"]) == 2


def test_block_ordered_list():
    doc = _markdown_to_adf("1. premier\n2. second")
    assert doc["content"][0]["type"] == "orderedList"
    assert len(doc["content"][0]["content"]) == 2
    assert doc["content"][0]["content"][0]["content"][0]["content"][0]["text"] == "premier"


def test_block_list_items_with_inline_marks():
    """Les items conservent les marks inline."""
    doc = _markdown_to_adf("- **bold** item")
    item_para = doc["content"][0]["content"][0]["content"][0]
    assert item_para["content"] == [
        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " item"},
    ]


def test_block_code_block_with_language():
    md = "```python\nprint('hi')\n```"
    doc = _markdown_to_adf(md)
    assert doc["content"] == [
        {
            "type": "codeBlock",
            "attrs": {"language": "python"},
            "content": [{"type": "text", "text": "print('hi')"}],
        }
    ]


def test_block_code_block_without_language():
    md = "```\nfoo\nbar\n```"
    doc = _markdown_to_adf(md)
    assert doc["content"][0]["type"] == "codeBlock"
    assert "attrs" not in doc["content"][0] or doc["content"][0].get("attrs") == {}
    assert doc["content"][0]["content"][0]["text"] == "foo\nbar"


def test_block_code_block_preserves_indentation():
    md = "```\n    indented\n```"
    doc = _markdown_to_adf(md)
    assert doc["content"][0]["content"][0]["text"] == "    indented"


def test_known_fields_constants():
    """Les 8 champs réservés du template."""
    assert KNOWN_FIELDS == [
        "Summary", "Project", "Type", "Priority", "Labels",
        "Startdate", "Duedate", "Description",
    ]


def test_split_fields_minimal_template():
    template = "# Summary\nfoo\n\n# Description\nbar"
    result = _split_fields(template)
    assert result == {"Summary": "foo", "Description": "bar"}


def test_split_fields_all_fields():
    template = (
        "# Summary\nS\n\n"
        "# Project\nPRJ\n\n"
        "# Type\nTask\n\n"
        "# Priority\nHigh\n\n"
        "# Labels\nimportant, urgent\n\n"
        "# Startdate\n2026-05-27\n\n"
        "# Duedate\n2026-06-06\n\n"
        "# Description\nbody"
    )
    result = _split_fields(template)
    assert set(result.keys()) == set(KNOWN_FIELDS)
    assert result["Labels"] == "important, urgent"


def test_split_fields_description_captures_until_eof():
    """Tout ce qui suit `# Description` est dans Description, y compris h2+."""
    template = (
        "# Summary\nfoo\n\n"
        "# Description\nintro\n\n## Sub-section\n- item\n"
    )
    result = _split_fields(template)
    assert result["Description"] == "intro\n\n## Sub-section\n- item"


def test_split_fields_unknown_field_raises():
    template = "# Summary\nfoo\n\n# Bogus\nx\n\n# Description\nbar"
    try:
        _split_fields(template)
    except ValueError as e:
        assert "Bogus" in str(e)
        assert "Summary" in str(e)
    else:
        assert False, "ValueError attendue"


def test_split_fields_trims_field_body():
    template = "# Summary\n  foo  \n\n# Description\nbar"
    result = _split_fields(template)
    assert result["Summary"] == "foo"


def test_parse_full_template_returns_payload_with_adf():
    template = (
        "# Summary\nDevelopper feature\n\n"
        "# Description\nLe contexte.\n\n- item 1\n- item 2"
    )
    payload = parse_markdown_jira_template(template, _DEFAULTS)
    fields = payload["fields"]
    assert fields["summary"] == "Developper feature"
    assert fields["project"] == {"key": "SDAL"}
    assert fields["issuetype"] == {"name": "Task", "subtask": False}
    assert fields["priority"] == {"name": "High"}
    assert fields["labels"] == ["important", "urgent"]
    assert fields["startdate"] == "2026-05-27"
    assert fields["duedate"] == "2026-06-06"
    assert fields["description"]["type"] == "doc"
    assert len(fields["description"]["content"]) == 2


def test_parse_template_overrides_defaults():
    template = (
        "# Summary\nS\n# Project\nFOO\n# Type\nBug\n# Priority\nLow\n"
        "# Labels\na, b\n# Startdate\n2026-01-01\n# Duedate\n2026-01-10\n"
        "# Description\nbody"
    )
    payload = parse_markdown_jira_template(template, _DEFAULTS)
    fields = payload["fields"]
    assert fields["project"] == {"key": "FOO"}
    assert fields["issuetype"] == {"name": "Bug", "subtask": False}
    assert fields["priority"] == {"name": "Low"}
    assert fields["labels"] == ["a", "b"]
    assert fields["startdate"] == "2026-01-01"
    assert fields["duedate"] == "2026-01-10"


def test_parse_template_summary_required():
    template = "# Description\nbar"
    try:
        parse_markdown_jira_template(template, _DEFAULTS)
    except ValueError as e:
        assert "Summary" in str(e)
    else:
        assert False, "ValueError attendue"


def test_parse_template_description_required():
    template = "# Summary\nfoo"
    try:
        parse_markdown_jira_template(template, _DEFAULTS)
    except ValueError as e:
        assert "Description" in str(e)
    else:
        assert False, "ValueError attendue"


def test_parse_template_project_required_without_default():
    template = "# Summary\nS\n\n# Description\nbody"
    no_project = dict(_DEFAULTS)
    no_project["project_key"] = ""
    try:
        parse_markdown_jira_template(template, no_project)
    except ValueError as e:
        assert "Project" in str(e) or "project_key" in str(e)
    else:
        assert False, "ValueError attendue"


def test_parse_template_labels_csv_split():
    template = (
        "# Summary\nS\n\n# Labels\nfoo,  bar ,baz  \n\n"
        "# Description\nbody"
    )
    payload = parse_markdown_jira_template(template, _DEFAULTS)
    assert payload["fields"]["labels"] == ["foo", "bar", "baz"]
