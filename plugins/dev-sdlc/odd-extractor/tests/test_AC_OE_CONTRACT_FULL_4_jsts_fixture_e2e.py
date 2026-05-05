"""AC.OE.CONTRACT-FULL.4 — Real-fixture end-to-end regression:
production-pipeline write produces a contract whose pr-safety gate
classifies a synthetic VERIFIED-AC-touching diff as ``HARD_BLOCK``.

This is the critical test the v0.2.1 Cycle 3 HARD smoke surfaced as
missing. Pre-fix: synthetic test fixtures construct
:class:`BandedContract` directly via pr-safety's conftest fixtures,
bypassing the YAML round-trip the production pipeline uses; this
masked F1 across v0.1.9 + v0.2.0 + v0.2.1 release-level smoke. This
test exercises the actual production write path (RawACs → verify_contract
→ contract-draft.yaml → read_contract → classifier → decide) and pins
the HARD_BLOCK behavior end-to-end.

Methodology choice (per plan-doc §4 halt-trigger): the test uses a
pre-constructed :class:`RawACs` carrying one VERIFIED AC + a tmp git
repo with a backing file, not the jsts-playwright-app fixture's
adapter-driven extraction. Rationale: the test's purpose is to verify
the contract YAML round-trip + gate classification on the production
write path (i.e., what F1 broke); the JS/TS adapter's own VERIFIED-AC
count is unrelated to F1's failure mode. The pre-constructed RawACs
goes through the SAME ``verify_contract()`` writer the live extraction
uses — ergo the same write path under test.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from loam_odd_extractor import (
    RawACs,
    default_budget,
    init_extraction,
    verify_contract,
)
from loam_pr_safety.classifier import classify
from loam_pr_safety.contract import read_contract
from loam_pr_safety.diff import parse_unified_diff
from loam_pr_safety.gate import decide
from loam_pr_safety.spec import GateAction


FIXED_TS = "2026-05-04T12:00:00+00:00"


def _verified_banded_ac_dict(
    *,
    ac_id: str,
    backing_file: str,
    line_range: tuple[int, int],
    repo_sha: str,
) -> dict:
    """Build a VERIFIED banded-AC dict pinning a specific line range
    in a backing file. Mirrors the JS/TS adapter's VERIFIED shape
    (test-citation + source-citation + repo_sha + backing_files).
    """
    start, end = line_range
    return {
        "ac_id": ac_id,
        "text": (
            f"VERIFIED AC backed by tests/{ac_id}.spec.ts pinned to "
            f"{backing_file}:{start}-{end}."
        ),
        "confidence": "VERIFIED",
        "evidence": {
            "kind": "test",
            "citations": [
                f"tests/{ac_id}.spec.ts::{ac_id}_passes",
                f"{backing_file}:{start}-{end}",
            ],
            "repo_sha": repo_sha,
            "rationale": None,
        },
        "backing_files": [backing_file],
    }


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def test_production_pipeline_round_trip_yields_hard_block(
    workspace_root: Path, tmp_path: Path
) -> None:
    """End-to-end: production verify_contract() write + pr-safety
    read + classify + decide. Synthetic VERIFIED-AC-touching diff
    must produce GateAction.HARD_BLOCK.
    """
    # ---- Set up a tmp git repo with the backing file ----------------
    target_repo = tmp_path / "target-repo"
    target_repo.mkdir()
    _git(target_repo, "init", "-q", "-b", "main")
    _git(target_repo, "config", "user.email", "test@example.com")
    _git(target_repo, "config", "user.name", "Test User")

    backing_file = "src/auth.ts"
    backing_path = target_repo / backing_file
    backing_path.parent.mkdir(parents=True, exist_ok=True)
    initial_content = textwrap.dedent(
        """\
        // line 1
        // line 2
        // line 3
        // line 4
        // line 5
        export function validateLogin(pw: string): boolean {
          return pw.length >= 8;
        }
        // line 9
        // line 10
        """
    )
    backing_path.write_text(initial_content, encoding="utf-8")
    _git(target_repo, "add", backing_file)
    _git(target_repo, "commit", "-q", "-m", "initial: add validateLogin")
    repo_sha = _git(target_repo, "rev-parse", "HEAD").strip()

    # ---- Run the production write path (verify_contract) -----------
    config = init_extraction(
        repo_path=target_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    raw = RawACs(
        extraction_id=config.repo_id,
        acs=[
            _verified_banded_ac_dict(
                ac_id="AC.VERIFIED.LOGIN",
                backing_file=backing_file,
                line_range=(6, 8),  # the validateLogin function body
                repo_sha=repo_sha,
            ),
        ],
        unhandled_paths=[],
        per_slice_costs={},
        created_at=FIXED_TS,
    )
    verify_contract(config=config, raw=raw, timestamp=FIXED_TS)

    # ---- Consumer side: pr-safety reads the production-written
    # ---- contract-draft.yaml + classifies + decides ----------------
    contract = read_contract(
        repo_id=config.repo_id,
        workspace_root=workspace_root,
    )
    assert len(contract.acs) == 1, (
        "Pre-fix this would be 0; post-fix it must be 1. F1 root "
        "cause: extractor wrote no `acs` field; consumer parsed "
        "zero ACs; gate classified everything as novel."
    )
    assert contract.acs[0].ac_id == "AC.VERIFIED.LOGIN"

    # ---- Synthetic VERIFIED-AC-touching diff ------------------------
    # Modify line 7 (inside the cited 6-8 range) to invert the
    # password-length check — the kind of regression VERIFIED ACs
    # exist to block.
    synth_diff = textwrap.dedent(
        """\
        diff --git a/src/auth.ts b/src/auth.ts
        index abc1234..def5678 100644
        --- a/src/auth.ts
        +++ b/src/auth.ts
        @@ -7 +7 @@ export function validateLogin(pw: string): boolean {
        -  return pw.length >= 8;
        +  return pw.length < 8;
        """
    )
    diff = parse_unified_diff(synth_diff)
    assert diff.entries, "synthetic diff must parse to at least one entry"

    # ---- Classify against the round-tripped contract ---------------
    classification = classify(diff, contract)
    assert classification.touched_acs, (
        "Synthetic diff at src/auth.ts:7 must touch AC.VERIFIED.LOGIN "
        "(citation range 6-8). Pre-fix this would be empty because "
        "BandedContract.acs was empty."
    )
    touched_ids = [t.ac.ac_id for t in classification.touched_acs]
    assert "AC.VERIFIED.LOGIN" in touched_ids

    # ---- Decision must be HARD_BLOCK -------------------------------
    decision = decide(
        classification,
        safety_profile="production-stake",
        extraction_id=config.repo_id,
    )
    assert decision.action is GateAction.HARD_BLOCK, (
        f"VERIFIED-AC-touching diff must produce HARD_BLOCK; got "
        f"{decision.action.value}. Pre-fix smoke saw SURFACE_DECISION "
        f"because the contract loader received zero ACs and the diff "
        f"classified as novel-only — F1's stable failure mode."
    )
    assert decision.requires_ratification is True
    assert "AC.VERIFIED.LOGIN" in decision.reason
