"""TG23: git diff against the true-first-run-sealed baseline shows
only telegram-interface/ changes (plus optionally the runtime data/
generated-artifact directory). Zero deltas to any sealed component.

Mirror of cost-governance/tests/test_no_sealed_amendments.py — same
sidecar SEAL_COMMIT pattern for a build-time test that keeps working
before the owner seals the component.

BASELINE: e1686e1 (true-first-run SEAL_COMMIT — the previous seal).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "e1686e1"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_tg23_only_telegram_interface_changed() -> None:
    """Halt-signal check: no sealed source touched."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # data/observability/spans.jsonl is test-run output, not source.
    # docs/ is workspace-level content.
    allowed_prefixes = (
        "telegram-interface/",
        "data/",
        "docs/rebuild/components/telegram-interface/",
    )
    allowed_files: set[str] = set()

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. Halt-signal."
    )
