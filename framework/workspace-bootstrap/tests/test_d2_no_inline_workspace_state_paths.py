"""AC.D.2.5 — Path-helper centralisation enforced structurally.

Every framework reader of workspace-state paths must invoke
``workspace_bootstrap.workspace_paths`` helpers rather than compute
the path inline (``workspace_root / ".pos"`` etc.). This test
greps the framework source tree for the inline patterns and asserts
zero matches.

Allow-list:
- ``workspace_paths.py`` itself (defines the constants).
- Test fixtures (under ``tests/``) — fixtures construct fake state
  for tests; the helper consumers' tests use the helper, but the
  fixture path-construction is mechanical.
- Hands-off-lifecycle hooks (per D.2-build.B these duplicate the
  constants because of the stdlib-only contract — they cannot import
  workspace_bootstrap before the .venv exists).
- Universal admissions ``framework/tools/heavy-b-migrate/`` and
  ``framework/tools/pos-amend/`` — these reference ``<repo_root>/
  objective_tracker.sqlite`` for canonical-pos-v2's own tracker DB,
  NOT a derived workspace's workspace-state. Per D.2-build.D they
  stay unchanged.
- Comments / docstrings carrying ``<workspace>/.pos/`` etc. as
  prose; the test pattern requires the inline computation, not the
  prose mention.

Backing AC: AC.D.2.5 (path-helper centralisation enforced
structurally).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
FRAMEWORK_DIR = REPO_ROOT / "framework"


# Inline workspace-state path patterns banned in framework source.
# Each pattern is a raw-string regex applied per line. The regex
# matches the substantive code-form ``<expr> / ".pos"`` etc., not
# prose like ``<workspace>/.pos/`` in a docstring.
BANNED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "workspace_root / \".pos\"",
        re.compile(r"workspace_root\s*/\s*\"\.pos\""),
    ),
    (
        "workspace_root / \"personas\"",
        re.compile(r"workspace_root\s*/\s*\"personas\""),
    ),
    (
        "host.workspace_root / \"data\"",
        re.compile(r"host\.workspace_root\s*/\s*\"data\""),
    ),
    (
        "workspace_root / \"objective_tracker.sqlite\"",
        re.compile(r"workspace_root\s*/\s*\"objective_tracker\.sqlite\""),
    ),
    (
        "workspace_root / \".mcp.json\"",
        re.compile(r"workspace_root\s*/\s*\"\.mcp\.json\""),
    ),
)


# Files exempt from the centralisation rule.
ALLOW_LIST_RELATIVE = frozenset(
    {
        # The helper itself defines the canonical patterns.
        "framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py",
        # The seed function delegates to workspace_paths but documents
        # the path it returns; the docstring contains the prose form.
        # The substantive code is the helper invocation. Allow-listed
        # because the workspace-bootstrap tracker_seed is the seam
        # workspace-bootstrap exposes; D-Q-deferred reconciliation.
    }
)


# Directory prefixes allow-listed:
ALLOW_LIST_PREFIXES = (
    # Hands-off-lifecycle hooks duplicate constants per D.2-build.B
    # (stdlib-only contract before .venv exists).
    "framework/hands-off-lifecycle/hooks/",
    # Test fixtures construct fake state for tests; mechanical.
    "/tests/",
    # heavy-b-migrate + pos-amend reference canonical-pos-v2's own
    # tracker DB (NOT a derived workspace) — per D.2-build.D.
    "framework/tools/heavy-b-migrate/",
    "framework/tools/pos-amend/",
    # Cache directory.
    "/__pycache__/",
)


def _is_allow_listed(rel_path: str) -> bool:
    if rel_path in ALLOW_LIST_RELATIVE:
        return True
    for prefix in ALLOW_LIST_PREFIXES:
        if prefix in rel_path or rel_path.startswith(prefix.lstrip("/")):
            return True
    return False


def _scan_framework() -> list[tuple[str, int, str, str]]:
    """Walk ``framework/`` and return ``(rel_path, line_no, pattern,
    line_text)`` violations.
    """
    violations: list[tuple[str, int, str, str]] = []
    for py_path in FRAMEWORK_DIR.rglob("*.py"):
        rel = py_path.relative_to(REPO_ROOT).as_posix()
        if _is_allow_listed(rel):
            continue
        try:
            text = py_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Skip non-UTF-8 fixture files (e.g. encoding-test fixtures
            # under loam-mode that ship binary / non-UTF-8 content).
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for label, pat in BANNED_PATTERNS:
                if pat.search(line):
                    violations.append((rel, lineno, label, line.rstrip()))
    return violations


def test_d2_no_inline_workspace_state_paths_in_framework_source() -> None:
    """Every framework reader of workspace-state must invoke a helper
    from ``workspace_bootstrap.workspace_paths``. Inline path
    construction (``workspace_root / ".pos"`` etc.) is forbidden by
    AC.D.2.5; the helpers are the single source of truth for the
    workspace-state layout.
    """
    violations = _scan_framework()
    if violations:
        formatted = "\n".join(
            f"  {rel}:{lineno}: matches {pattern!r} — {text!r}"
            for rel, lineno, pattern, text in violations
        )
        pytest.fail(
            "AC.D.2.5: inline workspace-state path constructions found in "
            "framework source. Replace each with the matching helper from "
            "``workspace_bootstrap.workspace_paths``:\n" + formatted
        )
