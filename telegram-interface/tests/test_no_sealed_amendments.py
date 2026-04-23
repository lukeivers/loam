"""TG23: git diff against the true-first-run-sealed baseline shows
only telegram-interface/ changes (plus optionally the runtime data/
generated-artifact directory). Zero deltas to any sealed component.

Mirror of cost-governance/tests/test_no_sealed_amendments.py — same
sidecar SEAL_COMMIT pattern for a build-time test that keeps working
before the owner seals the component.

BASELINE advances each time telegram-interface opens a new amendment
window:
  - e1686e1  at the true-first-run SEAL_COMMIT — the previous seal
             and this component's first BASELINE.
  - b9e1f96  when the telegram-interface-framework-integration
             amendment (#9) opened. Amendment #9 composes
             telegram-interface as the thirteenth foundational
             adapter via a new workspace-bootstrap adapter; per AC7
             the amendment ships ZERO edits under
             `telegram-interface/src/`. This BASELINE advance +
             allowed-prefix extension admits the multi-component
             amendment's workspace-bootstrap, hands-off-lifecycle,
             and docs surfaces without weakening the src-untouched
             invariant. b9e1f96 is the pre-amendment tip — the
             amendment-#8 audit-closure seal commit immediately
             before this amendment's code commit. Amendment number
             (#9) is proposal-assigned; #10 and #11 landed first.
  - 3b128c3  when the S3 silent-except bundle amendment (#21) opened.
             The 2026-04-22 audit + classifier surfaced one remaining
             AC:none silent catch inside `telegram-interface/src/
             allowlist.py::AccessFile.identities()` (loop skip on
             malformed `pos_identities` records). Per ODD §8 rule 8 +
             the audit-triage-by-severity CDC (bucket d — outright
             violation), the fix replaces the silent skip with a new
             `allowlist_record_malformed` OTel emitter while
             preserving the `continue` (unrecoverable drop still
             correct). Multi-component amendment (scope-of-work,
             telegram-interface, memory-system, hands-off-lifecycle).
             This amendment also adds `scope-of-work/` and
             `memory-system/` to the allowed-prefix tuple because the
             amendment's full diff spans those surfaces too. Sites 4
             + 5 (`first_run_inventory.py::_parse_scalar`) were
             re-classified bucket (a) during research and dropped;
             the former Site 3 in `availability.py` stayed dropped
             per the re-dispatch note. 3b128c3 is the pre-amendment
             tip — the pyyaml-reachability seal commit immediately
             before amendment #21's code commit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "3b128c3"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_tg23_only_telegram_interface_changed() -> None:
    """Halt-signal check: no sealed source touched.

    Per AC7 (telegram-interface-framework-integration proposal) the
    telegram-interface/src/ tree is untouched by the amendment —
    asserted structurally by a dedicated AC7 test below.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # data/observability/spans.jsonl is test-run output, not source.
    # docs/ is workspace-level content. Amendment #9
    # (telegram-interface-framework-integration) extends the allowed
    # prefixes with the three multi-component surfaces it touches —
    # workspace-bootstrap/ (the new adapter), hands-off-lifecycle/
    # (BASELINE bump in cross-cutting seal test), and
    # docs/rebuild/components/telegram-interface-framework-integration/
    # (the proposal + plan). docs/rebuild/plans/ is admitted because
    # the plan-before-code CDC lives alongside the amendment commit.
    # Amendment #21 (S3 silent-except bundle) extends with
    # `scope-of-work/` and `memory-system/` — the other two source-
    # editing partners in that multi-component amendment.
    allowed_prefixes = (
        "telegram-interface/",
        "data/",
        "docs/rebuild/components/telegram-interface/",
        "docs/rebuild/components/telegram-interface-framework-integration/",
        "docs/rebuild/plans/",
        "workspace-bootstrap/",
        "hands-off-lifecycle/",
        "scope-of-work/",
        "memory-system/",
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


def test_AC7_no_telegram_interface_src_edits() -> None:
    """AC7 (telegram-interface-framework-integration proposal): the
    amendment consumes telegram-interface's public API only. Any edit
    under `telegram-interface/src/` is a halt condition — signals the
    public surface needs a new constructor or factory, which is out of
    scope.

    This test is the structural enforcement of the sealed-API
    invariant. It fires at seal tip; during the build it also fires
    against HEAD since the sidecar falls back to HEAD.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            f"{BASELINE}..{seal}",
            "--",
            "telegram-interface/src/",
        ],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    assert changed == [], (
        "telegram-interface/src/ modified by amendment — halt-signal. "
        f"Changed paths: {changed}"
    )
