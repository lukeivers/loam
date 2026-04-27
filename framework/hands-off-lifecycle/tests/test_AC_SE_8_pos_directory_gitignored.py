"""AC.SE.8 — ``<workspace>/.pos/`` sentinel directory is gitignored.

Per the locked plan-doc §4 AC.SE.8: the workspace-local sentinel
directory at ``.pos/`` is gitignored so the structural-enforcement
substrate's runtime-written files (active-scope sentinel, session-
state sentinels, first-run state) never accumulate as tracked
artefacts.

The plan-doc D-build.7 chose top-level ``.gitignore`` entry — single
addition under the universal-paths admission per amendment #44's
precedent.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_AC_SE_8_root_gitignore_names_pos_directory() -> None:
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), "root .gitignore must exist"
    text = gitignore.read_text(encoding="utf-8")
    # Match either ``.pos/`` or ``.pos`` as a standalone line — both
    # ignore the directory's contents under git's pattern semantics.
    lines = {ln.strip() for ln in text.splitlines()}
    assert (".pos/" in lines or ".pos" in lines), (
        "AC.SE.8: root .gitignore must list `.pos/` (or `.pos`) so "
        "workspace-local sentinel files do not accumulate as tracked "
        "artefacts. Found lines: " + ", ".join(sorted(lines))
    )
