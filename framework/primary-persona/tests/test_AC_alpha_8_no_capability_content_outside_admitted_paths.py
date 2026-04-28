"""AC.α.8 — No capability content outside the corpus tree +
template-tree exception.

Per plan §4 AC.α.8, every file matching the capability-content
shape (Class A or Class B schema markers, the leverage-spine
markers, the authoring-guide markers) lives under one of:

  - ``framework/primary-persona/templates/persona-template/prompt.md``
    (template-tree exception per v1.2 R16);
  - ``docs/rebuild/capability-corpus/AUTHORING.md`` (authoring guide);
  - ``docs/rebuild/capability-corpus/<class-dir>/*.md`` (seed docs).

This test greps the repo for the schema-marker strings + asserts
zero matches outside admitted paths. Negative-shape — verifies α
did not leak content to unintended locations and that no
pre-existing file collides with the new schema names.

Test files under ``framework/primary-persona/tests/`` reference the
schema markers as test-fixture content; the test admits them
explicitly because they encode the schema, they don't carry
capability content.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Schema markers that should appear ONLY in the admitted locations.
# Picked to be distinctive enough to grep on without false positives:
#   - "Capability leverage spine" — the new spine section heading.
#   - "[user-intent phrasings]" — the Class A overlay marker.
#   - "Trust marker" — the Class B trust block marker.
#   - "No-cross-class-write" — the authoring-guide invariant marker.
SCHEMA_MARKERS = (
    "Capability leverage spine",
    "[user-intent phrasings]",
    "No-cross-class-write",
)

# Admitted paths (any path under one of these is OK).
ADMITTED_PREFIXES = (
    "framework/primary-persona/templates/persona-template/",
    "docs/rebuild/capability-corpus/",
    # Plan + builder-plan + manifest + this dispatch's research live
    # under docs/rebuild/plans/ — they discuss the schema markers as
    # specification language.
    "docs/rebuild/plans/",
    # Tests under framework/primary-persona/tests/ encode the schema
    # in assertions; not capability content.
    "framework/primary-persona/tests/",
    # The seal-narrative target lives under
    # framework/primary-persona/seals/ — not capability content but
    # references the schema in narrative prose.
    "framework/primary-persona/seals/",
)


def _grep(pattern: str) -> list[str]:
    """Return paths under REPO_ROOT containing the literal pattern."""
    proc = subprocess.run(
        [
            "git", "grep", "--full-name", "-l",
            "-F", pattern,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode > 1:
        # git grep returns 1 for "no match"; > 1 is real error.
        raise RuntimeError(
            f"git grep failed: {proc.stderr}"
        )
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def _is_admitted(path: str) -> bool:
    return any(path.startswith(p) for p in ADMITTED_PREFIXES)


def test_AC_alpha_8_capability_leverage_spine_marker_only_in_admitted_paths():
    matches = _grep("Capability leverage spine")
    leaked = [p for p in matches if not _is_admitted(p)]
    assert leaked == [], (
        f"'Capability leverage spine' marker found outside admitted "
        f"paths: {leaked}"
    )


def test_AC_alpha_8_user_intent_phrasings_marker_only_in_admitted_paths():
    matches = _grep("[user-intent phrasings]")
    leaked = [p for p in matches if not _is_admitted(p)]
    assert leaked == [], (
        f"'[user-intent phrasings]' marker found outside admitted "
        f"paths: {leaked}"
    )


def test_AC_alpha_8_no_cross_class_write_marker_only_in_admitted_paths():
    matches = _grep("No-cross-class-write")
    leaked = [p for p in matches if not _is_admitted(p)]
    assert leaked == [], (
        f"'No-cross-class-write' marker found outside admitted "
        f"paths: {leaked}"
    )
