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

"""The coverage check + reconcile + gap computation + renderers.

This is the engine behind ``loam guards`` (AC.FMG-CHECK.1/.2, AC.FMG-GAP.1,
AC.FMG-S.1). It:

  1. loads + schema-validates the catalogue (AC.FMG-CAT.1, via
     :mod:`catalogue`);
  2. for every row, RESOLVES the ``guard_ref`` against the real tree
     (AC.FMG-CAT.2 + AC.FMG-CHECK.2 — ground truth, not the catalogue's own
     claim) and records a per-row verdict;
  3. derives ``gap`` (class==floor AND default_on != YES) and asserts the
     FLOOR INVARIANT — every floor row is checked for a default-on guard
     (AC.FMG-S.1);
  4. surfaces DIVERGENCES — a row whose guard_kind obligates a guard_ref but
     whose ref does not resolve (a claimed-but-absent guard);
  5. renders the coverage report (with the distinct GAP section — AC.FMG-GAP.1)
     and the generated human-readable companion doc.

Deterministic — no LLM, no network (feedback_no_anthropic_api_key).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .catalogue import Catalogue, GuardRow, load_catalogue
from .derive import GuardRefResolution, find_repo_root, resolve_guard_ref


@dataclass(frozen=True)
class RowVerdict:
    """The reconcile verdict for one catalogue row."""

    row: GuardRow
    resolution: GuardRefResolution | None  # None for empty-ref rows.

    @property
    def gap(self) -> bool:
        """Derived: a floor-class failure mode without a default-on guard."""
        return self.row.is_floor and self.row.default_on != "YES"

    @property
    def divergence(self) -> bool:
        """A row that CLAIMS a guard the tree does not actually carry.

        Only rows whose guard_kind obligates a guard_ref can diverge; a
        persona-discipline / none row legitimately carries no ref.
        """
        if not self.row.guard_ref_required:
            return False
        return self.resolution is None or not self.resolution.resolved

    def divergence_detail(self) -> str:
        if not self.divergence:
            return ""
        if self.resolution is None:
            return (
                f"{self.row.id}: guard_kind {self.row.guard_kind!r} requires "
                f"a guard_ref but none was given"
            )
        return f"{self.row.id}: {self.resolution.reason()}"


@dataclass(frozen=True)
class CoverageReport:
    """The full coverage verdict (AC.FMG-CHECK.1)."""

    verdicts: tuple[RowVerdict, ...]
    repo_root: Path
    catalogue_path: Path
    checked_on: str

    @property
    def floor_verdicts(self) -> tuple[RowVerdict, ...]:
        return tuple(v for v in self.verdicts if v.row.is_floor)

    @property
    def gaps(self) -> tuple[RowVerdict, ...]:
        """Floor-class failure modes with no default-on guard (the gaps)."""
        return tuple(v for v in self.verdicts if v.gap)

    @property
    def divergences(self) -> tuple[RowVerdict, ...]:
        """Rows claiming a guard the tree does not carry (over-claims)."""
        return tuple(v for v in self.verdicts if v.divergence)

    @property
    def floor_invariant_checked(self) -> bool:
        """True iff EVERY floor row was checked for a default-on guard.

        The invariant is "checked", not "satisfied" — the gaps are the
        normal, honest reporting state (FORK F-2/F-3 rulings). Every floor
        row gets a verdict, so this holds whenever the report was produced.
        """
        return all(v.row.default_on in {"YES", "NO-PROGRAMMATIC", "NONE"}
                   for v in self.floor_verdicts)


def run_coverage_check(
    *, catalogue_path: Path | None = None, repo_root: Path | None = None
) -> CoverageReport:
    """Run the full coverage check against GROUND TRUTH (AC.FMG-CHECK.*).

    Loads + validates the catalogue, resolves every row's guard_ref against
    the real tree, and computes per-row verdicts (gap + divergence). With no
    arguments this runs against the SHIPPED catalogue + the live tree — the
    surface the outcome-altitude AC drives (AC.FMG-S.1: no pre-arranged
    state).
    """
    cat: Catalogue = load_catalogue(catalogue_path)
    root = repo_root or find_repo_root()
    verdicts: list[RowVerdict] = []
    for row in cat.rows:
        resolution: GuardRefResolution | None = None
        if row.guard_ref:
            resolution = resolve_guard_ref(row.id, row.guard_ref, root)
        verdicts.append(RowVerdict(row=row, resolution=resolution))
    return CoverageReport(
        verdicts=tuple(verdicts),
        repo_root=root,
        catalogue_path=cat.source_path,
        checked_on=date.today().isoformat(),
    )


# --- renderers -------------------------------------------------------------


def _default_on_label(row: GuardRow) -> str:
    return {
        "YES": "default-on",
        "NO-PROGRAMMATIC": "NO programmatic guard",
        "NONE": "no guard",
    }[row.default_on]


def render_report(report: CoverageReport) -> str:
    """Render the human-readable coverage report (AC.FMG-CHECK.1 output).

    Includes a DISTINCT gap section (AC.FMG-GAP.1) and a divergence section
    (AC.FMG-CHECK.2 — claimed-but-absent guards). The gaps are the actionable
    output; the report is a REPORTER first (FORK F-2: exit 0 even with gaps).
    """
    lines: list[str] = []
    floor = report.floor_verdicts
    gaps = report.gaps
    divs = report.divergences

    lines.append("loam guards — protection-pillar coverage report")
    lines.append(f"  checked on : {report.checked_on}")
    lines.append(f"  catalogue  : {report.catalogue_path}")
    lines.append(f"  tree root  : {report.repo_root}")
    lines.append(
        f"  rows       : {len(report.verdicts)} "
        f"({len(floor)} floor-class)"
    )
    lines.append("")

    lines.append("FLOOR-CLASS COVERAGE (the non-negotiable floor):")
    for v in floor:
        mark = "GAP " if v.gap else "ok  "
        lines.append(
            f"  [{mark}] {v.row.id:<32} {_default_on_label(v.row):<22} "
            f"{v.row.guard_kind}"
        )
    lines.append("")

    # The distinct GAP section (AC.FMG-GAP.1).
    lines.append("=" * 70)
    if gaps:
        lines.append(
            f"GAPS — {len(gaps)} floor-class failure mode(s) with NO "
            f"default-on guard:"
        )
        lines.append(
            "  (the actionable output — each is a structural-enforcement "
            "candidate)"
        )
        lines.append("")
        for v in gaps:
            lines.append(f"  * {v.row.id} — {v.row.name}")
            lines.append(f"      betrayal : {v.row.description.strip()}")
            lines.append(f"      guard    : {v.row.guard.strip()}")
            lines.append(f"      why-gap  : {v.row.verification.strip()}")
            lines.append("")
    else:
        lines.append("GAPS — none. Every floor-class failure mode has a "
                     "default-on guard.")
        lines.append("")

    lines.append("=" * 70)
    if divs:
        lines.append(
            f"DIVERGENCES — {len(divs)} row(s) CLAIM a guard the tree does "
            f"not carry:"
        )
        lines.append(
            "  (a manifest over-claim — the protection pillar must not "
            "hallucinate its own coverage)"
        )
        for v in divs:
            lines.append(f"  ! {v.divergence_detail()}")
    else:
        lines.append(
            "DIVERGENCES — none. Every claimed guard resolves against the "
            "real tree."
        )

    return "\n".join(lines)


def render_companion_doc(report: CoverageReport) -> str:
    """Render the GENERATED human-readable companion (docs/design/...).

    Rendered from the catalogue + the live coverage verdict — NEVER
    hand-edited (no second drift surface; doctrine §"Always expose the
    substance; adapt only the vocabulary").
    """
    lines: list[str] = []
    lines.append(
        "<!-- GENERATED by `loam guards --refresh` from "
        "framework/protection-matrix/data/failure-mode-guard-matrix.yaml. -->"
    )
    lines.append("<!-- DO NOT hand-edit — regenerate from the YAML. -->")
    lines.append("")
    lines.append("# loam protection matrix — failure mode × guard")
    lines.append("")
    lines.append(
        "loam's *protection pillar* (doctrine §\"The two sides of leg 2 — "
        "translation in, protection around\"): each known way an AI betrays "
        "a user by default, loam's actual guard against it, whether that "
        "guard is on by default for everyone, whether the failure mode is "
        "**floor-class** (non-negotiable) or **proportional**, and how we "
        "verify the guard fires."
    )
    lines.append("")
    lines.append(
        "This page is generated from the machine-checkable catalogue and "
        "reflects the live coverage verdict as of the date below. The "
        "**gaps** — floor-class failure modes guarded today only by persona "
        "discipline — are the actionable output, not a defect to hide."
    )
    lines.append("")
    lines.append(f"*Coverage checked: {report.checked_on}. "
                 f"{len(report.gaps)} floor-class gap(s) open.*")
    lines.append("")

    lines.append("## The matrix")
    lines.append("")
    lines.append(
        "| Failure mode | Guard | Kind | Class | Default-on | Gap |"
    )
    lines.append("|---|---|---|---|---|---|")
    for v in report.verdicts:
        r = v.row
        gap_cell = "**YES**" if v.gap else "—"
        lines.append(
            f"| **{r.id}** — {r.name} | {r.guard} | {r.guard_kind} | "
            f"{r.klass} | {r.default_on} | {gap_cell} |"
        )
    lines.append("")

    gaps = report.gaps
    lines.append("## The gaps (floor-class, no default-on guard)")
    lines.append("")
    if gaps:
        lines.append(
            "Each of these floor-class failure modes is today guarded only "
            "by persona discipline (or partially) — a prose rule the "
            "doctrine itself says \"decays first under pressure.\" Each is a "
            "structural-enforcement candidate "
            "(`feedback_structural_enforcement_on_recurrence`):"
        )
        lines.append("")
        for v in gaps:
            r = v.row
            lines.append(f"### {r.id} — {r.name}")
            lines.append("")
            lines.append(f"- **Betrayal:** {r.description.strip()}")
            lines.append(f"- **Today's guard:** {r.guard.strip()}")
            lines.append(f"- **Source:** {r.source.strip()}")
            lines.append(f"- **Why it's a gap:** {r.verification.strip()}")
            lines.append("")
    else:
        lines.append(
            "None — every floor-class failure mode has a default-on guard."
        )
        lines.append("")

    divs = report.divergences
    if divs:
        lines.append("## Divergences (claimed-but-absent guards)")
        lines.append("")
        for v in divs:
            lines.append(f"- {v.divergence_detail()}")
        lines.append("")

    return "\n".join(lines)


def companion_doc_path(repo_root: Path) -> Path:
    """The generated companion's canonical path."""
    return repo_root / "docs" / "design" / "protection-matrix.md"
