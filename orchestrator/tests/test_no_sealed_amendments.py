"""B20 / B23 — orchestrator seal-diff test (amendment #7).

Mirror of workspace-bootstrap/tests/test_no_sealed_amendments.py.
Orchestrator historically shipped a ``SEAL_COMMIT`` sidecar without a
seal-diff test; amendment #7 (orchestrator-bootstrap-unification,
approved 2026-04-22) lands the test alongside the behaviour change so
the diff scope is enforceable from this point forward.

Seal-test pattern (B23): BASELINE constant names the pre-amendment tip;
SEAL_COMMIT is read from the sidecar sibling file so the diff runs
``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based variant was
the f94d602 defect fixed across the other sealed components; it must
not be introduced here.

BASELINE advances when a new amendment opens this sealed surface.
Initial value ``a5dbf8f`` — the pre-amendment tip (the seal commit for
amendment #6 / namespaced-labels-and-bootout) immediately before
amendment #7's first touch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# BASELINE history:
#   - a5dbf8f  at first orchestrator seal (amendment #7 —
#              orchestrator-bootstrap-unification opens the orchestrator's
#              sealed surface for the first time; the pre-amendment tip
#              is the amendment-#6 seal commit immediately preceding this
#              amendment's code commit).
BASELINE = "a5dbf8f"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, tests/SEAL_COMMIT holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur.
    """
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


def test_B20_only_orchestrator_unification_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #7 is a multi-component amendment covering
    ``orchestrator/`` (primary surface), ``workspace-bootstrap/`` (adapter
    + integration-test edits for the ``require_bootstrap`` field
    removal), ``hands-off-lifecycle/`` (seal baseline advance), and the
    amendment's own proposal directory. ``data/`` is runtime spool.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "orchestrator/",
        "hands-off-lifecycle/",
        "workspace-bootstrap/",
        "docs/rebuild/components/orchestrator-bootstrap-unification/",
        "data/",
    )

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
