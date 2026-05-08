"""AC.F.S — F's amendment touches no sealed-component-owned path.

F is dev-discipline (sub-plan F's §2). The amendment lives at:

  - ``tools/loam-mode/`` (new tool — F's primary surface)
  - ``plugins/dev-sdlc/dev-mode-manifest.yaml`` (the partition data)
  - ``docs/plans/two-modes-and-multi-workspace/F-auto-load-partition.md``
    (this plan's §14 method-decision register)
  - ``CLAUDE.md`` + ``CLAUDE.dev.md`` + ``README.md`` +
    ``docs/CLAUDE_CAPABILITIES.md`` + ``docs/duration-estimation-rubric.md``
    (always-loaded scrub for AC.F3 + dev-extension surface)
  - ``docs/FUTURE_IDEAS_DRAFT.md`` (post-build observations)

This test checks F's amendment-commit diff (HEAD vs HEAD~1) when HEAD
is recognisably an F-amendment commit. It is informative (skips) when
run in any other state — pre-commit dry-runs, post-seal post-followup
state, etc. AC.F.S is a structural assertion that fires on the
amendment-commit window itself.

Mirrors the dev-discipline pattern from ``tools/loam/tests/`` —
no BASELINE / SEAL_COMMIT (those exist inside sealed-component
fences).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


# Post-M6b.0: tests at plugins/dev-sdlc/tools/loam-mode/tests/
# (parents[5] = workspace).
REPO_ROOT = Path(__file__).resolve().parents[5]


# Paths F's amendment is permitted to touch. The historical F
# amendment landed before loam-mode moved into the plugin, so the
# legacy prefix is preserved as a name; the post-M6b.0 location is
# also admitted so the test's diff window is consistent if F's
# amendment commit is ever re-tested in the future.
ALLOWED_PREFIXES = (
    "tools/loam-mode/",
    "framework/tools/loam-mode/",
    "plugins/dev-sdlc/tools/loam-mode/",
    "plugins/dev-sdlc/dev-mode-manifest.yaml",
    "docs/plans/two-modes-and-multi-workspace/F-auto-load-partition",
    "docs/FUTURE_IDEAS_DRAFT.md",
)
ALLOWED_FILES = {
    "CLAUDE.md",
    "CLAUDE.dev.md",
    "README.md",
    "docs/CLAUDE_CAPABILITIES.md",
    # Post-M6b.0: duration-estimation-rubric MOVED into the plugin.
    "plugins/dev-sdlc/docs/duration-estimation-rubric.md",
}


def _git(args: list[str]) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, text=True
    ).strip()


def _is_f_amendment_commit() -> bool:
    """The HEAD commit's subject identifies it as F's amendment."""
    try:
        subject = _git(["log", "-1", "--format=%s", "HEAD"])
    except subprocess.CalledProcessError:
        return False
    # F's amendment subjects: feat(loam-mode|tools): ... or
    # docs(rebuild): dev-mode partition (sub-plan F)
    s = subject.lower()
    return (
        "loam-mode" in s
        or "auto-load partition" in s
        or "dev-mode partition" in s
        or "sub-plan f" in s
    )


def test_AC_F_S_no_sealed_component_paths_changed() -> None:
    """When HEAD is F's amendment commit, the diff against HEAD~1
    touches only F's allowed surfaces."""
    if not _is_f_amendment_commit():
        pytest.skip(
            "HEAD is not an F-amendment commit "
            "(seal-diff window not active)."
        )

    out = _git(["diff", "--name-only", "HEAD~1..HEAD"])
    changed = [ln for ln in out.splitlines() if ln.strip()]

    offending: list[str] = []
    for path in changed:
        if any(path.startswith(p) for p in ALLOWED_PREFIXES):
            continue
        if path in ALLOWED_FILES:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sub-plan F touched paths outside its dev-discipline scope: "
        f"{offending}. Halt-signal condition — these are sealed-component "
        f"or otherwise-owned surfaces F is not authorised to edit."
    )


def test_AC_F_S_allowed_surfaces_register_is_complete() -> None:
    """Sanity check: every path enumerated in ALLOWED_PREFIXES /
    ALLOWED_FILES exists or is a recognised future surface. Catches
    typos in the register."""
    for prefix in ALLOWED_PREFIXES:
        # Prefixes must point at paths that exist OR plausibly will.
        candidate = REPO_ROOT / prefix
        if candidate.exists():
            continue
        # Allow plan-doc prefix that ends mid-name.
        if "F-auto-load-partition" in prefix:
            continue
        if "FUTURE_IDEAS_DRAFT" in prefix:
            continue
        # Pre-M6b.0 historical locations preserved as names so this
        # register matches F's amendment commit if ever re-tested.
        # The post-M6b.0 prefix `plugins/dev-sdlc/tools/loam-mode/`
        # (also in the register) covers today's actual location.
        if prefix in ("tools/loam-mode/", "framework/tools/loam-mode/"):
            continue
        if candidate.with_suffix(".md").exists():
            continue
        # A glob-style prefix that resolves at the parent.
        parent = candidate.parent
        assert parent.exists(), f"register prefix unresolvable: {prefix}"
    for fname in ALLOWED_FILES:
        candidate = REPO_ROOT / fname
        # Allowed-files may be created by F itself; existence at test
        # time is sufficient evidence.
        assert candidate.exists() or "CLAUDE.dev.md" in fname, (
            f"register file missing: {fname}"
        )
