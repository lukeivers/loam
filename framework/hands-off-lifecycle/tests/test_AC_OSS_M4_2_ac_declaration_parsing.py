"""AC.OSS-M4.2 — AC-declaration parsing handles well-formed and
malformed input.

Per the locked plan-doc §4 AC.OSS-M4.2: the parser recognises the
``<AC-MANIFEST>`` block (case-sensitive on the marker), parses each
non-empty interior line as ``component,ac_id,source_path_glob`` via
stdlib ``csv.reader``, skips blank + comment (``#``) lines, treats
malformed rows as parse failures that emit NDJSON diagnostics + skip
(do NOT halt), treats a missing block as the AC.DSA.10 backwards-
compat passthrough.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


def _stub_corpus_load_sentinel(monkeypatch, *, mode: str) -> None:
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _wr: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


# ---------------------------------------------------------------------
# Block extraction
# ---------------------------------------------------------------------


def test_AC_OSS_M4_2_extract_block_present() -> None:
    import dispatch_setup_hook

    prompt = (
        "Some prefix.\n"
        "<AC-MANIFEST>\n"
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "</AC-MANIFEST>\n"
        "Some suffix.\n"
    )
    body = dispatch_setup_hook.extract_ac_manifest_block(prompt)
    assert body is not None
    assert "primary-persona,AC.X.1" in body


def test_AC_OSS_M4_2_extract_block_absent() -> None:
    import dispatch_setup_hook

    prompt = "No manifest block here."
    assert dispatch_setup_hook.extract_ac_manifest_block(prompt) is None


def test_AC_OSS_M4_2_extract_block_case_sensitive() -> None:
    """Lowercase marker is NOT recognised — case-sensitive per plan-doc."""
    import dispatch_setup_hook

    prompt = (
        "<ac-manifest>\n"
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "</ac-manifest>\n"
    )
    assert dispatch_setup_hook.extract_ac_manifest_block(prompt) is None


def test_AC_OSS_M4_2_extract_block_non_string_returns_none() -> None:
    import dispatch_setup_hook

    assert dispatch_setup_hook.extract_ac_manifest_block(None) is None  # type: ignore[arg-type]
    assert dispatch_setup_hook.extract_ac_manifest_block(123) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Row parsing
# ---------------------------------------------------------------------


def test_AC_OSS_M4_2_parse_well_formed_multi_row() -> None:
    import dispatch_setup_hook

    body = (
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "hands-off-lifecycle,AC.Y.2,framework/hands-off-lifecycle/hooks/bar.py"
    )
    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        body
    )
    assert len(rows) == 2
    assert diagnostics == []
    assert rows[0].component == "primary-persona"
    assert rows[0].ac_id == "AC.X.1"
    assert rows[0].source_path_glob == (
        "framework/primary-persona/src/foo.py"
    )
    assert rows[1].component == "hands-off-lifecycle"


def test_AC_OSS_M4_2_parse_single_row() -> None:
    import dispatch_setup_hook

    body = "primary-persona,AC.X.1,framework/primary-persona/src/foo.py"
    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        body
    )
    assert len(rows) == 1
    assert diagnostics == []


def test_AC_OSS_M4_2_parse_blank_lines_skipped() -> None:
    import dispatch_setup_hook

    body = (
        "\n"
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "\n"
        "\n"
        "hands-off-lifecycle,AC.Y.2,framework/hands-off-lifecycle/hooks/bar.py\n"
    )
    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        body
    )
    assert len(rows) == 2
    assert diagnostics == []


def test_AC_OSS_M4_2_parse_comment_lines_skipped() -> None:
    import dispatch_setup_hook

    body = (
        "# this is a comment\n"
        "primary-persona,AC.X.1,framework/primary-persona/src/foo.py\n"
        "# another comment\n"
        "hands-off-lifecycle,AC.Y.2,framework/hands-off-lifecycle/hooks/bar.py\n"
    )
    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        body
    )
    assert len(rows) == 2
    assert diagnostics == []


def test_AC_OSS_M4_2_parse_malformed_row_wrong_column_count() -> None:
    import dispatch_setup_hook

    body = (
        "primary-persona,AC.X.1\n"  # too few columns
        "primary-persona,AC.X.2,src/foo.py,extra-col\n"  # too many
        "hands-off-lifecycle,AC.Y.3,framework/hands-off-lifecycle/hooks/bar.py\n"
    )
    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        body
    )
    # Only the well-formed row survives.
    assert len(rows) == 1
    assert rows[0].component == "hands-off-lifecycle"
    # Two diagnostics for the malformed rows.
    assert len(diagnostics) == 2


def test_AC_OSS_M4_2_parse_malformed_row_empty_field() -> None:
    import dispatch_setup_hook

    body = (
        ",AC.X.1,framework/primary-persona/src/foo.py\n"  # empty component
        "primary-persona,,framework/primary-persona/src/foo.py\n"  # empty ac_id
        "primary-persona,AC.X.2,\n"  # empty glob
        "hands-off-lifecycle,AC.Y.3,framework/hands-off-lifecycle/hooks/bar.py\n"
    )
    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        body
    )
    assert len(rows) == 1
    assert len(diagnostics) == 3


def test_AC_OSS_M4_2_parse_empty_block() -> None:
    import dispatch_setup_hook

    rows, diagnostics = dispatch_setup_hook.parse_ac_manifest_block(
        ""
    )
    assert rows == []
    assert diagnostics == []


# ---------------------------------------------------------------------
# Hook-level integration
# ---------------------------------------------------------------------


def test_AC_OSS_M4_2_no_block_passthrough(
    tmp_path: Path, monkeypatch
) -> None:
    """Missing block → passthrough-no-ac decision."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Just a research dispatch, no manifest."},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "passthrough-no-ac"
    assert decision.parsed_acs == []


def test_AC_OSS_M4_2_all_malformed_passthrough(
    tmp_path: Path, monkeypatch
) -> None:
    """Block with all malformed rows → still passthrough-no-ac."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    prompt = (
        "<AC-MANIFEST>\n"
        "primary-persona,AC.X.1\n"
        ",AC.X.2,src/foo.py\n"
        "</AC-MANIFEST>\n"
    )
    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": prompt},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "passthrough-no-ac"
    assert decision.parsed_acs == []
    assert len(decision.parse_diagnostics) == 2


def test_AC_OSS_M4_2_non_task_tool_no_op(
    tmp_path: Path, monkeypatch
) -> None:
    """Non-Task tools short-circuit to no-op."""
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={"prompt": "anything"},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"


def test_AC_OSS_M4_2_missing_prompt_no_op(
    tmp_path: Path, monkeypatch
) -> None:
    _stub_corpus_load_sentinel(monkeypatch, mode="dev-mode")
    import dispatch_setup_hook

    decision = dispatch_setup_hook.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"
