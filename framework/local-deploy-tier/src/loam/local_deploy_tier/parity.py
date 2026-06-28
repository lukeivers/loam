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

"""AC.LOCAL.3 — when a LOCAL backing service differs from a downstream env's,
the divergence is surfaced in plain language before any promotion is offered.

Dev/prod parity is the whole reason the LOCAL tier exists (local-target
research §0): keep the gap between what runs on the user's machine and what
runs downstream SMALL, so bugs surface locally (cheap, private, reversible)
instead of downstream (expensive, public). The two parity axes the research
names as the dangerous ones (§3): the backing-service **engine** (SQLite local
vs Postgres prod is the classic silent break) and its **pinned version**
(Postgres 14 vs 16; ``latest`` is a silent parity break).

This module diffs a LOCAL environment's declared backing services against a
downstream environment's, aligning services by their logical ``name`` (``db``
to ``db``), and renders each divergence in the owner's vocabulary — never a raw
diff. A service present in only one side is itself a gap (a service the local
run never exercises, or a local service with no downstream counterpart).

The honest-residual rule (research §3 rule 4 / §8.1): even at full declared
parity, real divergences remain (host OS, CPU arch, managed-service behaviour).
:func:`parity_report` carries that caveat so a clean diff never over-claims
"local green guarantees downstream green".

The contract bridge (shared-contract §4): this surface is a PRECONDITION shown
before a promotion is OFFERED — it does not itself promote (P2 owns promotion).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .local_config import BackingService, EnvProfile


# Honest-residual caveat — always surfaced, even when the declared diff is
# clean, so the tier never implies total parity (research §8.1, F2).
RESIDUAL_PARITY_CAVEAT: str = (
    "Even when everything below matches, your machine is not identical to the "
    "live setup (different operating system, chip, and real-world data). A "
    "clean check here is strong evidence, not a guarantee."
)


@dataclass(frozen=True)
class ParityGap:
    """One backing-service divergence between LOCAL and a downstream env."""

    service: str           # the logical service name the gap is about
    axis: str              # "engine" | "version" | "missing-downstream" | "missing-local"
    local_detail: str      # what LOCAL declares (may be "—")
    downstream_detail: str # what the downstream env declares (may be "—")
    plain_language: str    # the owner-facing sentence


@dataclass(frozen=True)
class ParityReport:
    """The full plain-language parity surface for LOCAL vs one downstream env."""

    local_env: str
    downstream_env: str
    gaps: tuple[ParityGap, ...] = field(default_factory=tuple)
    caveat: str = RESIDUAL_PARITY_CAVEAT

    @property
    def has_gaps(self) -> bool:
        return bool(self.gaps)

    def plain_language_summary(self) -> str:
        """The owner-facing summary — what differs between this machine and the
        downstream environment, in their words, plus the honest-residual
        caveat. Never a raw config diff (Lens 0 — expose substance, adapt
        vocabulary)."""
        if not self.gaps:
            head = (
                f"Your local setup matches '{self.downstream_env}' on every "
                "service it declares."
            )
            return f"{head}\n\n{self.caveat}"
        lines = [
            f"Before going to '{self.downstream_env}', here is where your "
            f"machine differs from it:",
            "",
        ]
        for gap in self.gaps:
            lines.append(f"  - {gap.plain_language}")
        lines.append("")
        lines.append(self.caveat)
        return "\n".join(lines)


def _index(services: tuple[BackingService, ...]) -> dict[str, BackingService]:
    return {s.name: s for s in services}


def compute_parity_gaps(
    local: tuple[BackingService, ...],
    downstream: tuple[BackingService, ...],
) -> tuple[ParityGap, ...]:
    """Diff *local* against *downstream* backing services on the engine +
    version axes, aligned by service name. Returns one ParityGap per
    divergence, each carrying a plain-language sentence."""
    local_idx = _index(local)
    down_idx = _index(downstream)
    gaps: list[ParityGap] = []

    # Stable order: downstream services first (the target shape), then any
    # local-only service.
    seen: set[str] = set()
    ordered_names = [s.name for s in downstream] + [
        s.name for s in local if s.name not in down_idx
    ]
    for name in ordered_names:
        if name in seen:
            continue
        seen.add(name)
        l = local_idx.get(name)
        d = down_idx.get(name)

        if d is not None and l is None:
            gaps.append(
                ParityGap(
                    service=name,
                    axis="missing-local",
                    local_detail="—",
                    downstream_detail=f"{d.kind} {d.version}".strip(),
                    plain_language=(
                        f"'{name}': the live setup uses "
                        f"{_engine_phrase(d)}, but your machine does not run it "
                        "at all — code that depends on it is untested locally."
                    ),
                )
            )
            continue
        if l is not None and d is None:
            gaps.append(
                ParityGap(
                    service=name,
                    axis="missing-downstream",
                    local_detail=f"{l.kind} {l.version}".strip(),
                    downstream_detail="—",
                    plain_language=(
                        f"'{name}': your machine runs {_engine_phrase(l)}, but "
                        "the live setup has no matching service — it will not "
                        "exist there."
                    ),
                )
            )
            continue
        # Both present — compare engine then version.
        assert l is not None and d is not None
        if l.kind.lower() != d.kind.lower():
            gaps.append(
                ParityGap(
                    service=name,
                    axis="engine",
                    local_detail=_engine_phrase(l),
                    downstream_detail=_engine_phrase(d),
                    plain_language=(
                        f"'{name}': your machine uses {_engine_phrase(l)} but "
                        f"the live setup uses {_engine_phrase(d)}. These behave "
                        "differently — something can pass here and fail there."
                    ),
                )
            )
            continue
        if _normalise_version(l.version) != _normalise_version(d.version):
            gaps.append(
                ParityGap(
                    service=name,
                    axis="version",
                    local_detail=_engine_phrase(l),
                    downstream_detail=_engine_phrase(d),
                    plain_language=(
                        f"'{name}': both use {l.kind}, but different versions "
                        f"(yours {_version_phrase(l)}, live {_version_phrase(d)}). "
                        "Version gaps cause surprises — pin them to match."
                    ),
                )
            )
    return tuple(gaps)


def parity_report(local_env: EnvProfile, downstream_env: EnvProfile) -> ParityReport:
    """Build the full plain-language parity surface for *local_env* vs
    *downstream_env* (AC.LOCAL.3). Always carries the honest-residual caveat."""
    gaps = compute_parity_gaps(
        local_env.backing_services, downstream_env.backing_services
    )
    return ParityReport(
        local_env=local_env.name,
        downstream_env=downstream_env.name,
        gaps=gaps,
    )


def _normalise_version(version: str) -> str:
    """``latest`` and an empty/unpinned version both read as 'unpinned' — and an
    unpinned version is itself a parity risk, so it never silently equals a
    pinned one."""
    v = (version or "").strip().lower()
    if v in ("", "latest"):
        return "\x00unpinned"
    return v


def _version_phrase(s: BackingService) -> str:
    v = (s.version or "").strip()
    if not v or v.lower() == "latest":
        return "no fixed version"
    return v


def _engine_phrase(s: BackingService) -> str:
    v = (s.version or "").strip()
    if not v or v.lower() == "latest":
        return f"{s.kind} (no fixed version)"
    return f"{s.kind} {v}"
