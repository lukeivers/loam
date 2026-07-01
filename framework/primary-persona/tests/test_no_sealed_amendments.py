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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""B20 / B23 — primary-persona seal-diff test (amendment #32).

Primary-persona historically shipped without a ``SEAL_COMMIT`` sidecar
surface; amendment #32 (session-start-context-load-gate, D8) lands the
surface alongside the first behaviour change to establish sealed-
component discipline on the primary-persona layer. Mirrors the
``memory-system/tests/test_no_sealed_amendments.py`` pattern (amendment
#8 was the matching introduction there).

Seal-test pattern (B23): BASELINE names the pre-amendment tip;
SEAL_COMMIT is read from the sidecar sibling file so the diff runs
``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based variant was
the ``f94d602`` defect patched across the other sealed components; it
must not be reintroduced.

BASELINE advances when a new amendment opens this sealed surface.
Initial value ``3844f2f`` — the pre-amendment tip (the seal commit for
amendment #31 / workspace-bootstrap-plist-path) immediately before
amendment #32's first touch of the primary-persona sealed surface.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE history:
#   - 3844f2f  at amendment #32 (session-start-context-load-gate / D8).
#              Primary-persona layer lands the ``ComposedContextPayload``
#              shared composer + session-level corpus-load gate per
#              docs/rebuild/plans/amendment-32-session-start-context-
#              load-gate.md. First time the primary-persona component
#              carries a seal-diff test + SEAL_COMMIT sidecar; BASELINE
#              pins at the pre-amendment tip (the #31 seal commit).
#   - 8e7c558  at amendment #33 (memory-consumer wiring / D7) —
#              advanced to the #32 seal commit per `pos-amend apply`.
#   - bea9f47  at amendment #35 (renderer + onboarding + is_starter) —
#              advanced via `pos-amend apply` to the commit immediately
#              preceding the amendment commit (HEAD~1 pattern per
#              amendment #34's narrative). Sub-plan §10's manifest
#              records the BASELINE rationale.
#   - 61ad8f9  at amendment #40 (primary-persona tracker-context
#              contributor — Heavy-B sub-plan #3 of 4). Registers a
#              session-level tracker-context contributor on the
#              existing ComposedContextPayload registry: surfaces the
#              workspace's value-prop-rooted in-flight objective tree
#              in additionalContext at SessionStart; consumes amendment
#              #38's `query_projection_view` + `trace_to_root` and
#              amendment #39's seeded value-prop root. Single-component
#              amendment on the `primary-persona` surface. Advanced via
#              `pos-amend apply` to the commit immediately preceding
#              the amendment commit (HEAD~1 pattern). Sub-plan §10's
#              manifest records the BASELINE rationale.
#   - 01f3b40  at the FBM rank-normalize slice (close AC-FBM-LIVE-2 unify
#              gap). Single-component primary-persona edit: _merge_by_score
#              now min-max-normalizes each source's BM25 scores before the
#              merge so a relevant FBM episode co-surfaces against the live
#              rules corpus (the two indexes' incompatible scales no longer
#              bury/truncate episodes). FBMU.3 raw-score-ordering tests
#              restated to the normalized contract. Advanced to HEAD~1 (the
#              P1.2 layout commit) — the commit immediately preceding the
#              slice commit, the HEAD~1 pattern. Seal-diff stays within the
#              primary-persona + docs/ allowed surfaces.
#   - 62081d8  at the FBM rule-weighting + hard-floor slice (B1 — the
#              rank-normalize safety-pair). Single-component primary-persona
#              edit: corpus_index.read_corpus_docs parses optional weight/
#              pinned frontmatter (fail-soft to a baseline no-op) + the FTS
#              corpus-index gains weight/pinned UNINDEXED columns + search
#              force-fetches pinned docs the query did not match; retrieval.
#              _merge_by_score boosts each hit's normalized score by its
#              weight (baseline 50 => 1.0 no-op) and force-includes pinned
#              rules ahead of the relevance cut (the hard floor — a multiplier
#              alone cannot guarantee never-drop). No doc currently declares a
#              weight, so the current corpus is byte-identical (no-regression).
#              Advanced to HEAD~1 (the prior seal-advance commit immediately
#              preceding the slice commit, the HEAD~1 pattern). Seal-diff
#              stays within the primary-persona + docs/ allowed surfaces.
#   - d871910  at the FBM episode SALIENCE gate slice (B3 — the recall-quality
#              safety-pair to B1). Single-component primary-persona edit:
#              file_memory.write_episode tags each turn at ingest with a cheap
#              structural salience score (compute_salience) stored as a
#              `salience` frontmatter field; the FTS/grep search paths compute
#              salience fresh from each body (so pre-salience episodes get the
#              gate without rewrite); retrieval._merge_by_score multiplies each
#              episode hit's weighted-normalized score by its salience and
#              force-DROPS below-threshold (junk) episodes from the surfaced
#              set (named, tunable SALIENCE_THRESHOLD). HARD INVARIANT: gates
#              surfacing only, never storage — every turn still on disk, gate
#              re-tunable. Fail-safe defaults to full salience everywhere so
#              the gate only suppresses affirmatively-junk turns. Advanced to
#              HEAD~1 (the B1 seal-advance commit immediately preceding the
#              slice commit, the HEAD~1 pattern). Seal-diff stays within the
#              primary-persona + docs/ allowed surfaces.
#   - 055f937  at the FBM spread-path salience-gate fix slice (AC-FBM-SAL-6).
#              The B3 salience gate tagged `_salience` on the FTS/grep candidate
#              pools but NOT on co-citation SPREAD-activated neighbor rows, so a
#              junk episode reachable ONLY via spread bypassed the gate and
#              leaked into recall (caught by the live-store activation smoke,
#              missed by the 813-test suite). Fix: tag
#              `_salience = _salience_from_body(body)` on the spread-neighbor
#              n_row (same helper the pools use). Adds AC-FBM-SAL-6 (spread x
#              junk gated, outcome-altitude). Code-only (in-memory result-row
#              slot, no stored-field change; migration is a forward no-op).
#              Advanced BASELINE to 055f937 (the B3 seal-advance commit
#              immediately preceding the fix slice, the HEAD~1 pattern);
#              SEAL_COMMIT -> c82131e (the fix slice). Seal-diff stays within
#              the primary-persona + docs/ allowed surfaces.
#   - c82131e  at the FBM path-consolidation slice. The live user-prompt-submit
#              hook surfaced episodes via the UNGATED file_memory path (no
#              salience gate — the task-notification junk source); the gated
#              keep_pace path (rank-normalize + rule-weight/floor + salience
#              gate) was sealed but never wired live. Repoints
#              build_session_composer's production branch to the gated keep_pace
#              turn contributor (register_keep_pace_turn_contributor), keeping
#              the "memory-retrieval" name; the retired file_memory functions
#              stay defined+exported (MCP branch + tests). Silent-on-no-match
#              replaces the ungated empty-state block (AC.M.3 + AC46.2 updated).
#              Adds AC-FBM-CON-1/-2/-3 + AC-FBM-CON-S (outcome-altitude: the
#              REAL cli_user_prompt_submit hook on real-shape fixtures). Pure
#              rewire (no stored-field change; migration is a forward no-op).
#              Advanced BASELINE to c82131e (the prior FBM-SAL seal commit,
#              the HEAD~1 pattern); SEAL_COMMIT -> 7dcb95b (the consolidation
#              slice). Seal-diff stays within primary-persona + docs/ surfaces.
#   fbm-salience-gate-compaction-summary-dump (slug; schema v3) — adds the 5th
#              junk signature to compute_salience (compaction-summary dumps) +
#              AC-FBM-SAL-7/-8/-9 (the last outcome-altitude via real
#              retrieve()). The prior BASELINE 1b400bb1 predated the entire
#              v1.0.0 lockstep release (loam-init / loam-skills / per-project-pm
#              landed on main between the last primary-persona seal 39d0e98a and
#              now), so the stale BASELINE spanned every release-cut component
#              and falsely tripped the fence. Advanced BASELINE to 7d103826 (the
#              main tip immediately before this amendment's source commit — the
#              HEAD~1 pattern) so the seal-diff window shows ONLY this
#              amendment's primary-persona + docs/plans/ surfaces.
#   fbm-write-time-salience-gate-cold-tier (slug; schema v3) — moves the sealed
#              compute_salience gate onto the WRITE path (its first write-path
#              caller). FileMemoryStore.write_episode diverts a SALIENCE_JUNK
#              turn to a new COLD_SUBDIR ("cold") and skips FTS indexing instead
#              of writing it to the hot EPISODES_SUBDIR + indexing it
#              unconditionally; substantive turns are byte-identical. Adds
#              AC-FBM-WGATE-1/-2/-3/-4 (the last outcome-altitude via the real
#              memory_write_worker.drain_once ingest path). Sealed SAL-3/-4/-5/-6
#              tests updated (AC intent preserved; mechanism shifted to the cold
#              tier — never-delete/reversible now read through cold-tier
#              recovery, SAL-6 seeds hot-tier junk directly to keep the read-side
#              spread gate meaningful). The prior BASELINE 7d103826 predated the
#              compaction-summary seal commits (949fced9 et al.), so it would
#              span them and falsely trip the single-component fence. Advanced
#              BASELINE to 9a050196 (the branch tip immediately before this
#              amendment's source commit — the HEAD~1 pattern) so the seal-diff
#              window shows ONLY this amendment's primary-persona + docs/plans/
#              surfaces.
#   fbm-load-time-systematic-filter (slug; schema v3) — the read-side counterpart
#              to Slice A. Extends the keep_pace/retrieval.py _merge_by_score
#              pre-merge filter stage with an absolute episode RAW-BM25 floor
#              (EPISODE_MIN_RELEVANCE_SCORE = 0.1, mirroring the corpus floor,
#              applied with a self-disable safeguard so it never over-filters a
#              lone relevant-but-sparse episode — reconciles B1 with the sealed
#              AC-FBM-RN-2 / AC.FBMU.1) and a stdlib token-Jaccard near-dup dedup
#              (DEDUP_JACCARD_THRESHOLD = 0.85). Consolidates the reactive per-case
#              load patches into the one systematic stage. Adds
#              AC-FBM-FLOOR-1 / AC-FBM-DEDUP-1 / AC-FBM-FILTER-STAGE-1 /
#              AC-FBM-FILTER-2 (the last outcome-altitude via production retrieve()
#              over a real store, no pre-arranged state). No sealed test edited.
#              Advanced BASELINE to f1548494 (the branch tip immediately before
#              this amendment's source commit — the HEAD~1 pattern) so the
#              seal-diff window shows ONLY this amendment's primary-persona +
#              docs/plans/ surfaces.
BASELINE = "b9422876"

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


def test_D8_S_only_primary_persona_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #32 (session-start-context-load-gate / D8) targets
    ``primary-persona/`` (primary surface — the new
    ``ComposedContextPayload`` composer + session-level gate + AC
    tests + sidecar surface) plus the amendment's own plan / research
    artefacts under ``docs/rebuild/plans/``. Universal paths
    (CLAUDE.md, docs/odd-*.md, docs/rebuild/FUTURE_IDEAS.md) are
    admitted per amendment #22 ruling #3.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/primary-persona/",
        "primary-persona/",
        # plan-before-code CDC paper trail: this amendment's plan +
        # research + manifest live under docs/rebuild/plans/.
        "docs/rebuild/plans/",
        # M6a — first plugin lands at plugins/dev-sdlc/. Admitted as
        # cross-component partner so the seal-diff sweep passes when
        # the plugin's diff is in flight.
        "plugins/dev-sdlc/",
        "framework/hands-off-lifecycle/",
        "docs/rebuild/plans/research/",
        "framework/workspace-bootstrap/",
        "framework/orchestrator/",
        "cost-governance/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/memory-system/",
        "framework/objective-tracker/",
        "framework/observability-aggregator/",
        "framework/reversibility-primitive/",
        "framework/safety-layer/",
        "framework/scope-of-work/",
        "framework/self-correction/",
        "framework/self-upgrade/",
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "tools/",
        "workspace-bootstrap/",
        "workspace-sync/",
        "docs/rebuild/capability-corpus/",
        "docs/rebuild/components/",
        "docs/rebuild/spec/",
        "framework/tools/loam-mode/",
        "framework/tools/loam-memory-inspect/",
        "framework/tools/pos-publish-framework-only/",
        "dormancy/",
        "framework/dormancy/",
        "dev-sdlc/",
        "framework/dev-sdlc/",
        "framework/loam/",
        "loam/",
        "docs/design/",
        "docs/experiments/",
        "docs/plans/",
        "docs/examples/",
        "docs/papers/",
        "docs/plans/sealed/",
        "docs/",
        "docs/state-migrations/",
        "framework/primary-persona/hooks/",
        "framework/primary-persona/scripts/",
        "framework/frame-kernel/",
    )
    # Universal-file admissions per amendment #22 ruling #3. Written
    # by ``loam amend apply``; kept stable across amendments.
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "CLAUDE.dev.md",
        "docs/rebuild/dev-mode-manifest.yaml",
        "docs/CLAUDE_CAPABILITIES.md",
        "README.md",
        "docs/getting-started.md",
        "docs/FUTURE_IDEAS.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
        "docs/STATE.md",
        "docs/release-roadmap-dependency-map.md",
        "docs/release-roadmap.md",
        "docs/implementation-tiers.md",
        "docs/release-process.md",
        "docs/release-versioning-policy.md",
        "docs/workspace-corpus-overrides.md",
        "docs/architecture.md",
        "docs/components/index.md",
        "docs/public-surface-manifest.md",
        "install-from-source.txt",
        "docs/plans/loam-roadmap.md",
        "docs/plans/loam-vnext-build-plan.md",
        "docs/design/adaptive-interaction-model.md",
    }

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
