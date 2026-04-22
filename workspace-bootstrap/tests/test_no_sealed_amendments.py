"""B20, B23 — git diff against baseline shows only workspace-bootstrap
changes. Zero deltas to any sealed component.

Seal-test pattern (B23 / proposal §3.5): this file defines a BASELINE
constant and reads SEAL_COMMIT from a sidecar file, diffing
`BASELINE..SEAL_COMMIT` — NOT `..HEAD`. The HEAD-based variant is the
defect fixed on `f94d602`; it must not be reintroduced.

BASELINE: the commit immediately preceding the most recent amendment
    window for workspace-bootstrap. Originally ac48a7b at first seal;
    updated to 3780603 when Amendment 4 (hands-off-lifecycle
    first_run_scaffold phase) opened. Each new amendment that opens
    this sealed surface updates BASELINE to the pre-amendment tip so
    the diff scope reflects the amendment, not the full rebuild
    history.
SEAL_COMMIT: populated at seal time. During build, falls back to HEAD.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "3780603"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, tests/SEAL_COMMIT holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_B23_seal_commit_pinning_pattern() -> None:
    """The test file exposes SEAL_COMMIT_PATH and names BASELINE; the
    diff call routes through _seal_commit() (not a hardcoded HEAD)."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_B20_only_workspace_bootstrap_changed() -> None:
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (aggregator spool, cost sqlite).
    allowed_prefixes = ("workspace-bootstrap/", "data/")
    allowed_files: set[str] = set()

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
