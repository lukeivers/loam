# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PBRET.5 (outcome-altitude) — zero unaccounted live ProgramBench
references, structurally enforced.

ProgramBench was fully retired per the 2026-06-11 owner ruling
(plan: docs/plans/programbench-full-retirement.md). A retired-work
mention regressing INTO live artefacts is exactly the stale-context
failure that caused the retirement candidate, so closure is enforced
structurally (D-PBRET.7): this sweep runs in the default suite,
permanently.

The sweep walks the tracked tree CASE-INSENSITIVELY for the
``programbench`` and ``realpb`` stems (both spellings observed in the
wild — plan §1.5) and passes ONLY when every hit is inside
sealed/bannered history (docs/plans/sealed/, docs/experiments/,
seal-record narratives) or an explicitly enumerated justified-keep
from the plan §10 D-PBRET.6 register. An injected stray live mention
makes it fail (mutation-detection test below, per
feedback_test_outcome_altitude_required).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

#: The two stems that cover every observed ProgramBench spelling
#: (``programbench``, ``ProgramBench``, ``realpb``, ``RealPB``, ...).
#: Matching is case-insensitive (plan §16.2: a lowercase-only sweep
#: under-counts).
PB_STEMS: tuple[str, ...] = ("programbench", "realpb")

#: Sealed/bannered-history prefixes — owner carve-out ("I don't mind
#: leaving the sealed stuff"): editing these would rewrite the audit
#: trail (plan §10 D-K1/D-K2).
SEALED_HISTORY_PREFIXES: tuple[str, ...] = (
    "docs/plans/sealed/",
    "docs/experiments/",
)

#: Justified keeps — the plan §10 D-PBRET.6 register, mechanically
#: enforced. Every entry carries its register row; anything NOT here
#: and NOT sealed history is an unaccounted live mention and fails
#: the sweep.
REGISTERED_KEEPS: frozenset[str] = frozenset(
    {
        # D-K4 — shipped-state release-history rows.
        "docs/release-roadmap.md",
        # D-K5 — STATE.md change-log retained-verbatim convention.
        "docs/STATE.md",
        # D-R5 — FIDRAFT entries RETIRED-marked in place (entry IDs
        # are historical anchors; renaming breaks cross-references).
        "docs/FUTURE_IDEAS_DRAFT.md",
        # D-K6 — completed-work plan-docs whose §14 registers anchor
        # seal SHAs (functionally sealed history).
        "docs/plans/v0-3-0-master-plan.md",
        "docs/plans/v0-4-0-master-plan.md",
        "docs/plans/release-roadmap-doc-plan.md",
        "docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md",
        "docs/plans/release-integration-fbm-session-clear-safety-and-stale-status-corrections.md",
        "docs/plans/research/swarming-extraction-composition.md",
        "docs/plans/research/swarming-extraction-composition-plan.md",
        "docs/plans/leverage-discipline-plan.md",
        "docs/plans/loam-1.0-acceptance-smoke-harness.manifest.yaml",
        # D-K7 — provenance citations into kept sealed history (the
        # only why-record for the live tie-breaker design); stems
        # survive only inside the cited sealed paths.
        "plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/build_next.py",
        "plugins/dev-sdlc/odd-extractor/tests/test_AC_V041_3_tie_breaker.py",
        # D-K8 — the retirement record itself.
        "docs/plans/programbench-full-retirement.md",
        "docs/plans/programbench-full-retirement.manifest.yaml",
        "docs/plans/research/programbench-retirement-inventory-2026-06-11.md",
        "plugins/dev-sdlc/tests/test_AC_PBRET_5_programbench_retirement_sweep.py",
        # D-K9 — register additions at build time (halt-trigger-4
        # mechanism; surfaced in the build report): completed-work /
        # bannered docs whose PB mentions are historical records or
        # load-bearing experiment-path provenance.
        "docs/plans/conventional-install-pypi-publish.md",
        "docs/plans/conventional-install-pypi-publish.manifest.yaml",
        "docs/plans/research/harness-landscape-and-roadmap-rerank.md",
        "docs/plans/research/harness-landscape-and-roadmap-rerank-plan.md",
        "docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md",
        # D-K10 — completed-work plan-doc whose parent-context line +
        # §14 register cite the (now-sealed) PB-retirement plan path as
        # provenance; the stem survives only inside that citation.
        # Register-row note: the plan §10 register sealed with the
        # PB-retirement plan (docs/plans/sealed/), so per D-K9
        # precedent this entry lives here and is surfaced in the build
        # report (guard-breach-inventory 2026-06-12, RED #1).
        "docs/plans/broken-suite-family-fixes.md",
    }
)


def _is_seal_narrative(relpath: str) -> bool:
    """Seal-record narratives (``<component>/seals/SEAL_COMMIT.*``) are
    amendment-machinery audit trail — append-only by the machinery,
    banner-only under retirement (plan §10 D-K3/D-PBRET.8)."""
    parts = relpath.split("/")
    return (
        len(parts) >= 2
        and parts[-2] == "seals"
        and parts[-1].startswith("SEAL_COMMIT.")
    )


def _is_accounted(relpath: str) -> bool:
    if relpath.startswith(SEALED_HISTORY_PREFIXES):
        return True
    if _is_seal_narrative(relpath):
        return True
    return relpath in REGISTERED_KEEPS


def find_unaccounted_pb_hits(repo_root: Path) -> list[str]:
    """Walk *repo_root*'s tracked tree (production mechanism:
    ``git grep``) case-insensitively for the PB stems; return every
    hit file NOT accounted for by sealed history or the register."""
    cmd = ["git", "grep", "-I", "-i", "-l"]
    for stem in PB_STEMS:
        cmd += ["-e", stem]
    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    # rc 0 = matches found; rc 1 = no matches (also a pass); >1 = error.
    if proc.returncode > 1:
        raise RuntimeError(
            f"git grep failed in {repo_root}: {proc.stderr.strip()}"
        )
    hits = [line for line in proc.stdout.splitlines() if line.strip()]
    return sorted(h for h in hits if not _is_accounted(h))


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "docs" / "STATE.md").is_file() and (
            ancestor / ".git"
        ).exists():
            return ancestor
    raise RuntimeError("could not locate the loam repo root")


def test_AC_PBRET_5_no_unaccounted_live_pb_references() -> None:
    """The production sweep: zero live PB references outside sealed
    history + the justified-keep register."""
    unaccounted = find_unaccounted_pb_hits(_find_repo_root())
    assert unaccounted == [], (
        "ProgramBench is RETIRED (2026-06-11, "
        "docs/plans/programbench-full-retirement.md) but live "
        "artefacts still reference it outside the plan §10 register: "
        f"{unaccounted} — remove/reword the mention(s), or (only if "
        "genuinely expensive to remove) add a justified row to the "
        "plan §10 D-PBRET.6 register AND this test's "
        "REGISTERED_KEEPS, surfacing the addition to the owner."
    )


def _git(tmp_repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=tmp_repo, check=True, capture_output=True
    )


def test_AC_PBRET_5_mutation_injected_stray_mention_goes_red(
    tmp_path: Path,
) -> None:
    """Mutation-detection (outcome-altitude proof the sweep is not a
    no-op): in a temp tracked tree, an injected stray live mention —
    in EITHER stem, mixed case — is flagged, while the same mention
    inside sealed history is not."""
    repo = tmp_path / "repo"
    (repo / "docs" / "plans" / "sealed").mkdir(parents=True)
    _git(repo, "init", "-q")

    # Sealed-history mention: accounted, must NOT flag.
    (repo / "docs" / "plans" / "sealed" / "old-plan.md").write_text(
        "historical ProgramBench plan text\n"
    )
    # Stray LIVE mentions: one per stem, mixed case (case-insensitivity
    # is load-bearing — plan §16.2).
    (repo / "docs" / "notes.md").write_text(
        "next up: resume ProgramBench work\n"
    )
    (repo / "live_module.py").write_text(
        "# tuned for the RealPB arm\n"
    )
    _git(repo, "add", "-A")

    flagged = find_unaccounted_pb_hits(repo)
    assert flagged == ["docs/notes.md", "live_module.py"], (
        "the sweep must flag exactly the stray live mentions "
        f"(case-insensitively, both stems); got {flagged}"
    )
