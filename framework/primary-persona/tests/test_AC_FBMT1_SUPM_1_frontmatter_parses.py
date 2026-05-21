"""AC.FBMT1.SUPM.1 — supersession-marker frontmatter parses cleanly.

Memory files carrying ``superseded-by: <relative-path>`` in YAML
frontmatter parse without error; the value is exposed on the parsed
representation. Memory files without the field expose the value as
``None`` / absent.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.SUPM family.
"""

from __future__ import annotations

from loam.primary_persona.file_memory import _split_frontmatter


def test_AC_FBMT1_SUPM_1_field_present_parses_to_string():
    """A memory file with ``superseded-by:`` exposes the value as a
    string on the parsed representation."""
    content = (
        "---\n"
        "name: turn/abc:def\n"
        "source: message\n"
        "reference_time: 2026-05-21T10:00:00+00:00\n"
        "group_id: workspace-slug\n"
        "superseded-by: ../later-rule.md\n"
        "---\n"
        "body content here\n"
    )
    front, body = _split_frontmatter(content)
    assert front.get("superseded-by") == "../later-rule.md"
    assert body.strip() == "body content here"


def test_AC_FBMT1_SUPM_1_field_absent_returns_none():
    """A memory file without ``superseded-by:`` exposes ``None`` on
    the parsed representation (``dict.get`` semantics)."""
    content = (
        "---\n"
        "name: turn/abc:def\n"
        "source: message\n"
        "reference_time: 2026-05-21T10:00:00+00:00\n"
        "group_id: workspace-slug\n"
        "---\n"
        "no supersession marker on this file\n"
    )
    front, _ = _split_frontmatter(content)
    assert front.get("superseded-by") is None


def test_AC_FBMT1_SUPM_1_value_is_string_not_coerced():
    """The supersession value is exposed as a plain string — no
    eager filesystem resolution, no coercion to Path."""
    content = (
        "---\n"
        "superseded-by: deep/nested/path/with/slashes.md\n"
        "---\n"
        "body\n"
    )
    front, _ = _split_frontmatter(content)
    value = front.get("superseded-by")
    assert isinstance(value, str)
    assert value == "deep/nested/path/with/slashes.md"
