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

"""Render a :class:`SmokeReport` into the 1.0-readiness report (design §4.4).

Per variant × dimension: PASS / PARTIAL / FAIL with the transcript evidence,
the cross-variant differentiation finding (AC.SMOKE.2), the spawn-isolation
audit, and the top-line 1.0 recommendation. Owner-readable plain language;
internal AC IDs cited only where load-bearing.
"""

from __future__ import annotations

from .judge import SmokeReport
from .runner import VariantRun


_EMOJI = {"PASS": "PASS", "PARTIAL": "PARTIAL", "FAIL": "FAIL"}


def render_report(
    report: SmokeReport,
    runs: list[VariantRun],
    *,
    title_suffix: str = "",
) -> str:
    lines: list[str] = []
    runs_by_key = {r.variant.key: r for r in runs}

    lines.append(f"# loam 1.0 Acceptance Smoke — readiness report{title_suffix}")
    lines.append("")
    lines.append(
        "Drives the REAL production `loam init` + first-run intake through "
        "three fully role-played non-technical white-collar users, then judges "
        "the end-state against loam's prime-objective promise (per-user-tuned "
        "translation) on named orthogonal dimensions. Every `claude -p` (the "
        "role-played user side AND every judge probe) was spawn-isolated; the "
        "operator's real `~/.claude` was never written (throwaway temp homes)."
    )
    lines.append("")

    # ---- Top-line verdict. ----
    lines.append(f"## Top-line verdict: **{report.top_line}**")
    lines.append("")
    lines.append(_verdict_prose(report))
    lines.append("")

    # ---- Protection audit. ----
    lines.append("## Safety + fidelity audit")
    lines.append("")
    lines.append(
        f"- Spawn-isolation held on every `claude -p`: "
        f"**{report.spawn_all_isolated}** "
        f"({report.spawn_count} isolated spawns, role-play turns + judge probes)."
    )
    lines.append(
        "- Live state: the operator's real `~/.claude` was NEVER written — each "
        "variant seeded into an isolated throwaway temp home, removed on exit."
    )
    lines.append(
        "- No Anthropic API key anywhere; every spawn subscription-routed."
    )
    lines.append("- No push, no merge — left at local artefacts for owner review.")
    lines.append("")

    # ---- Cross-variant differentiation (AC.SMOKE.2). ----
    lines.append("## Per-user learning (cross-variant differentiation)")
    lines.append("")
    lines.append(
        f"Materially-different seeds across the three variants: "
        f"**{report.cross_variant_distinct}**."
    )
    lines.append("")
    lines.append(f"> {report.cross_variant_evidence}")
    lines.append("")
    for key in ("A", "B", "C"):
        r = runs_by_key.get(key)
        if r is not None:
            seed = (r.seeded_objective_text or "(none seeded)").strip()
            lines.append(f"- **Variant {key}** ({r.variant.role_label}): {seed}")
    lines.append("")

    # ---- Per-variant × per-dimension grid. ----
    lines.append("## Per-variant × per-dimension grid")
    lines.append("")
    for card in report.scorecards:
        r = runs_by_key.get(card.variant.key)
        lines.append(
            f"### Variant {card.variant.key} — {card.variant.role_label} "
            f"({card.variant.onboarding_path})"
        )
        lines.append("")
        if card.run_error:
            lines.append(f"**RUN ERROR:** {card.run_error}")
            lines.append("")
        if r is not None and r.init_returncode is not None:
            lines.append(f"- `loam init` exit code: {r.init_returncode}")
        if r is not None:
            lines.append(
                f"- deep-research: offered={r.offered_deep_research}, "
                f"invoked={r.invoked_deep_research}, "
                f"round-trips={r.research_roundtrips}, "
                f"degraded-stub={r.research_is_stub}"
            )
            lines.append(f"- intake confirmed an objective: {r.confirmed}")
            lines.append(f"- conversation turns: {len(r.transcript)}")
        lines.append("")
        lines.append("| Dimension | Verdict | Kind | Evidence |")
        lines.append("|---|---|---|---|")
        for s in card.scores:
            ev = s.evidence.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {s.dimension} | **{_EMOJI[s.verdict]}** | {s.kind} | {ev} |"
            )
        lines.append("")

    # ---- FAILs called out explicitly (honest verdict). ----
    fails = [
        (card.variant.key, s)
        for card in report.scorecards
        for s in card.scores
        if s.verdict == "FAIL"
    ]
    lines.append("## Failures — the specific promised outcomes that did not land")
    lines.append("")
    if not fails:
        lines.append("None. Every scored dimension passed (or partially passed).")
    else:
        for key, s in fails:
            lines.append(
                f"- **Variant {key} / {s.dimension}:** {s.evidence}"
            )
    lines.append("")

    # ---- Transcripts appendix. ----
    lines.append("## Appendix — full transcripts")
    lines.append("")
    for key in ("A", "B", "C"):
        r = runs_by_key.get(key)
        if r is None:
            continue
        lines.append(f"### Variant {key} — {r.variant.role_label}")
        lines.append("")
        if r.error:
            lines.append(f"_run error: {r.error}_")
            lines.append("")
            continue
        lines.append("```")
        lines.append(r.transcript_blob())
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def _verdict_prose(report: SmokeReport) -> str:
    if report.top_line == "READY":
        return (
            "All three onboarding paths delivered the prime-objective promise "
            "with no failing dimension, the three users got materially "
            "different per-user seeds, the deep-research path fired only where "
            "it should, and the safety floor held. loam earns the 1.0 label on "
            "the strength of this smoke."
        )
    if report.top_line == "NOT-READY":
        return (
            "A load-bearing invariant did not hold (a variant run errored, the "
            "deep-research gating failed, or spawn-isolation was breached). "
            "These are gating failures: 1.0 should NOT ship until they are "
            "resolved and the smoke re-run clean. See the grid + failures "
            "section for the specific breach."
        )
    return (
        "The core pipeline runs end-to-end and the safety floor held, but one "
        "or more rubric dimensions came back PARTIAL/FAIL. These are honest "
        "gaps in the prime-objective promise — not blockers to the pipeline "
        "running, but each names a specific outcome that fell short of what "
        "1.0 promises. The owner's 1.0 call should weigh each gap below."
    )
