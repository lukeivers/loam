"""Sub-plan B — AC.B4.

Mode-aware session-start corpus.

In user mode the persona receives only F's ``always_loaded``
partition. In dev mode the persona additionally receives F's
``dev_only`` partition. Mechanism is the builder's call (per
post-#42 AC.B4 tightening); the test asserts the OUTCOME — that the
SessionStart payload composes correctly with F's selector and
includes the dev-extension content in dev mode but not in user mode.

The composition shape: F's ``select_corpus(manifest, root, mode)``
produces the path list; B's ``emit_session_start_context`` delivers
the dev-extension fragment as additionalContext when the selector
identifies dev mode. This test verifies the AC.B4 outcome —
``dev_only`` content reaches the persona iff mode == dev.
"""

from __future__ import annotations

from pathlib import Path

from loam_mode.manifest import load_manifest
from loam_mode.selector import select_corpus
from loam_mode.session_start import emit_session_start_context


def _scaffold_workspace(tmp_path: Path, dev_intent: str) -> Path:
    ws = tmp_path / "ws"
    (ws / "personas" / "primary").mkdir(parents=True)
    (ws / "personas" / "primary" / "contract.yaml").write_text(
        f"handle: primary\nis_primary: true\ndev_intent: {dev_intent}\n",
        encoding="utf-8",
    )
    return ws


def test_AC_B4_dev_mode_payload_includes_dev_only_content(
    tmp_path: Path,
) -> None:
    """End-to-end: dev workspace + CLAUDE.dev.md → SessionStart
    payload contains dev_only content."""
    ws = _scaffold_workspace(tmp_path, "yes")
    (ws / "CLAUDE.dev.md").write_text(
        "DEV-ONLY-CORPUS-MARKER\nsession-start discipline goes here.\n",
        encoding="utf-8",
    )
    payload = emit_session_start_context(ws)
    assert "DEV-ONLY-CORPUS-MARKER" in payload


def test_AC_B4_user_mode_payload_excludes_dev_only_content(
    tmp_path: Path,
) -> None:
    """End-to-end: user workspace + CLAUDE.dev.md present → payload
    does NOT contain dev_only content."""
    ws = _scaffold_workspace(tmp_path, "no")
    (ws / "CLAUDE.dev.md").write_text(
        "DEV-ONLY-CORPUS-MARKER\nshould-not-appear\n",
        encoding="utf-8",
    )
    payload = emit_session_start_context(ws)
    assert "DEV-ONLY-CORPUS-MARKER" not in payload
    assert payload == ""


def test_AC_B4_select_corpus_user_mode_excludes_claude_dev_md(
    tmp_path: Path,
) -> None:
    """F's selector + B's emitter agree: ``CLAUDE.dev.md`` is in
    F's ``dev_only`` partition; in user mode F's ``select_corpus``
    excludes it AND B's ``emit_session_start_context`` returns empty.
    """
    repo_root = Path(__file__).resolve().parents[3]
    manifest = load_manifest(
        repo_root / "docs" / "rebuild" / "dev-mode-manifest.yaml"
    )
    user_paths = select_corpus(manifest, repo_root, "user")
    dev_paths = select_corpus(manifest, repo_root, "dev")
    # CLAUDE.dev.md is dev-only.
    assert "CLAUDE.dev.md" not in user_paths
    assert "CLAUDE.dev.md" in dev_paths


def test_AC_B4_select_corpus_dev_mode_includes_dev_only(
    tmp_path: Path,
) -> None:
    """Sanity check on F's data: dev mode is a strict superset of
    user mode."""
    repo_root = Path(__file__).resolve().parents[3]
    manifest = load_manifest(
        repo_root / "docs" / "rebuild" / "dev-mode-manifest.yaml"
    )
    user_paths = set(select_corpus(manifest, repo_root, "user"))
    dev_paths = set(select_corpus(manifest, repo_root, "dev"))
    assert user_paths.issubset(dev_paths), (
        "AC.B4: dev mode must be a superset of user mode (F's data "
        "shape; B consumes it unchanged)."
    )
    # Dev partition contains content user mode does not.
    assert dev_paths - user_paths, (
        "AC.B4: dev_only must be non-empty for the AC to be meaningful."
    )
