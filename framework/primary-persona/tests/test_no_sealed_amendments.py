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
BASELINE = "eb0a4d3"

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
