"""Domain inference + batching for incremental-mode proposals.

Per AC.WATCHOBJ.3 (v0.2.3 Cycle 3) — `infer_domain(objective)` runs
the heuristic:

  1. **Objective ID prefix path (primary):** parse ``objective_id`` for
     shape ``O.<domain>.<n>`` (per Cycle 1's ID convention); return
     ``<domain>`` lowercased.
  2. **File-path-prefix fallback (rare):** longest common prefix across
     backing-row paths when the objective_id regex misses (defensive;
     Cycle 1's ID validator enforces shape).
  3. ``_uncategorised`` fallback.

Cycle 1's :class:`Objective` ID regex is ``^O\\.[a-z][a-z0-9-]*\\.\\d+$``
— domain is the middle segment, lowercase a-z + digits + hyphen,
inherently human-readable. No loam-internal blocklist needed at
objective altitude (loam-internal ACs were the v0.1.8 problem; Cycle
1's ID convention sidesteps it).

`group_proposals_by_domain(proposals)` is pure: deterministic for
fixed input (sorted-key output dict). Determinism is load-bearing
for AC.RELSMOKE.2 idempotency.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .proposals import IncrementalProposal
    from .spec import Objective


# Cycle 1 objective_id shape: "O.<domain>.<n>" — domain is lowercase
# letters/digits/hyphens, n is one or more digits.
_OBJECTIVE_ID_DOMAIN_RE = re.compile(
    r"^O\.([a-z][a-z0-9-]*)\.\d+$"
)

# v0.2.0 retained for backward compat by anyone constructing custom
# AC IDs against the watch — preserves the exported set for legacy
# imports. Cycle 3 retires AC ID inference; this remains as a
# documented constant to avoid breaking imports of
# ``LOAM_INTERNAL_AC_NAMESPACES``.
LOAM_INTERNAL_AC_NAMESPACES: frozenset[str] = frozenset(
    {
        "OREK",
        "BANDS",
        "SYNTH",
        "FIXTURES",
        "DPS1",
        "DPS2",
        "PRSG",
        "WATCH",
        "WATCHOBJ",
        "SKILLCAP",
        "PPM",
        "QSURF",
        "SAFETY",
        "BUDGET",
        "MFBM",
        "PRGATE",
        "RELSMOKE",
        "D-sa",
        "D-np",
        "D-st",
    }
)


_UNCATEGORISED = "_uncategorised"


def _objective_id_domain(objective_id: str) -> str | None:
    """Extract the ``<domain>`` segment from an objective_id."""
    if not objective_id:
        return None
    m = _OBJECTIVE_ID_DOMAIN_RE.match(objective_id)
    if m is None:
        return None
    return m.group(1)


def _common_path_prefix(paths: list[str]) -> str | None:
    """Return the last non-empty segment of the longest common
    path-prefix across `paths`, or None if no common prefix exists.

    Splits each path on '/'; takes element-wise common prefix; the
    last non-empty segment becomes the domain. Empty input → None.
    """
    if not paths:
        return None
    # Strip leading "./" and normalise.
    normalised = [
        p.lstrip("./").replace("\\", "/")
        for p in paths
        if p
    ]
    if not normalised:
        return None
    # Split each into segments.
    parts = [p.split("/") for p in normalised]
    # Drop empty segments (e.g., from trailing slashes).
    parts = [[seg for seg in plist if seg] for plist in parts]
    parts = [plist for plist in parts if plist]
    if not parts:
        return None
    # Element-wise common prefix.
    common: list[str] = []
    for tup in zip(*parts):
        first = tup[0]
        if all(seg == first for seg in tup):
            common.append(first)
        else:
            break
    if not common:
        return None
    # The last segment of the common prefix that is NOT a filename
    # (i.e., excluding the file basename when only one path is
    # present). With multiple paths, the common prefix is by
    # definition the directory shared by all; the last segment is
    # the most-specific shared directory name.
    #
    # Special case: a single path like "app/payment/charge.rb"
    # produces common=["app", "payment", "charge.rb"] which would
    # incorrectly use the filename. Drop the last segment if it
    # contains a dot (suggests filename) AND there's at least one
    # earlier segment available.
    candidate = common[-1]
    if "." in candidate and len(common) > 1:
        candidate = common[-2]
    return candidate or None


def infer_domain(objective: "Objective") -> str:
    """Infer a domain slug for ``objective``.

    Per AC.WATCHOBJ.3 — primary path is objective_id regex
    (``O.<domain>.<n>``); fallback is ``_uncategorised`` (Cycle 1's
    ID validator enforces the regex shape on construction; the
    fallback is defensive for malformed legacy data).

    Pure function (no side effects).
    """
    domain = _objective_id_domain(objective.objective_id)
    if domain:
        return domain
    return _UNCATEGORISED


def group_proposals_by_domain(
    proposals: list["IncrementalProposal"],
) -> "OrderedDict[str, list[IncrementalProposal]]":
    """Group ``proposals`` by their objective's inferred domain.

    Per AC.WATCHOBJ.3 — deterministic: same input always produces the
    same dict (keys sorted; insertion-order preserved within each
    value list). Load-bearing for AC.RELSMOKE.2 idempotency.
    """
    buckets: dict[str, list["IncrementalProposal"]] = {}
    for proposal in proposals:
        domain = infer_domain(proposal.objective)
        buckets.setdefault(domain, []).append(proposal)
    return OrderedDict(sorted(buckets.items()))


# Backward-compat alias for callers using the v0.2.0 name.
def group_by_domain(
    proposals: list["IncrementalProposal"],
) -> "OrderedDict[str, list[IncrementalProposal]]":
    """Alias of :func:`group_proposals_by_domain` for legacy callers."""
    return group_proposals_by_domain(proposals)
