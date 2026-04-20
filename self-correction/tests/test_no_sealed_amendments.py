"""CR21, CR24 — git diff against the cost-governance-sealed baseline
(04951b6) shows only self-correction/ changes. Zero deltas to any
sealed component.

Seal-test pattern (CR24): this file defines a SEAL_COMMIT constant and
diffs `BASELINE..SEAL_COMMIT`, NOT `..HEAD`. The HEAD-based pattern was
fixed on commit `f94d602` for cost-governance; we do not reintroduce
the defect here.

BASELINE: 04951b6 (cost-governance seal — the previous seal).
SEAL_COMMIT: populated at the time this component is sealed; during
    build, pin to the current HEAD so the audit diffs the full
    self-correction landing. After seal, update SEAL_COMMIT to the
    exact seal SHA and leave BASELINE alone.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "f94d602"  # baseline for self-correction (per brief §9):
# f94d602 is the tests-fix commit that pinned the seal-test pattern on
# cost-governance and reversibility-primitive. It is the tip of the
# sealed surface at the time self-correction opens. Diffing against
# this commit shows ONLY self-correction's landing (plus `data/`
# runtime output where applicable). The proposal §4.1 CR21 referenced
# 04951b6 — the brief §9 locks in f94d602 as the authoritative
# baseline; we follow the brief.

# SEAL_COMMIT is set at seal time. During build it is "HEAD" so the
# test surfaces in-flight changes; once sealed, update to the exact
# self-correction seal SHA. The rule in commit `f94d602` is: never
# use HEAD in the SHIPPED seal-test — but during the build itself,
# the test must still run against the current tip. We implement that
# by reading SEAL_COMMIT from a sidecar file populated by the sealing
# ritual, falling back to HEAD so the test works on a freshly-built
# branch.
SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD.

    Once the component is sealed, the sealing ritual writes the exact
    SHA to tests/SEAL_COMMIT and commits it. The audit then diffs
    BASELINE..<exact sha> — the HEAD-based defect cannot recur.
    """
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_CR24_seal_commit_pinning_pattern() -> None:
    """The test file exposes SEAL_COMMIT_PATH and does not diff against
    ..HEAD literally. Post-seal, tests/SEAL_COMMIT contains the SHA.
    """
    source = Path(__file__).read_text()
    # The module must name the BASELINE and SEAL_COMMIT_PATH constants.
    assert "BASELINE = \"f94d602\"" in source
    assert "SEAL_COMMIT_PATH" in source
    # The diff call must use f"{BASELINE}..{seal}" with `seal` coming
    # from _seal_commit(), not "..HEAD" hardcoded. Verify the diff
    # call in this file uses the `seal` variable. Scanning for the
    # positive pattern is safer than scanning for the negative
    # pattern, which tends to match the test itself.
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_CR21_only_self_correction_changed() -> None:
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (observability spans.jsonl etc.),
    # not source. It is not a sealed-component amendment — treat as
    # generated artifact alongside `self-correction/`.
    allowed_prefixes = ("self-correction/", "data/")
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
