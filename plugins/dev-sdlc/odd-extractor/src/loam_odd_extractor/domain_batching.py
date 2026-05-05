"""Domain inference + batching for incremental-mode proposals.

Per AC.WATCH.5 (v0.2.0 Cycle 1) — `infer_domain(ac)` runs the
heuristic:

  1. AC ID prefix path (primary): parse `ac_id` for shape
     `AC.<DOMAIN>.<n>`; return lowercased `<DOMAIN>` unless the
     domain is in the loam-internal blocklist.
  2. File-path-prefix fallback: longest common prefix across
     `backing_files` + citation-file-paths; return the last
     non-empty path segment.
  3. `_uncategorised` fallback: when neither path produces a
     domain.

Per AC.WATCH.5 — `group_by_domain(proposals)` is pure:
deterministic for fixed input (sorted-key output dict; insertion-
order preserved within each value list). Determinism is
load-bearing for AC.WATCH.4 idempotency check (same proposals →
same domain-grouping → same enqueue → no duplicates).

The blocklist is hard-coded in this module per F2 RF gap #7
(plan-doc §10): loam-internal AC namespaces should NOT surface as
domains. Update when adding new loam-internal AC namespaces.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bands import BandedAC
    from .proposals import IncrementalProposal


# AC ID prefix shape: "AC.<DOMAIN>.<n>" — DOMAIN is uppercase
# letters/digits, n is one or more characters (typically digits or
# hyphens). The regex is anchored so partial matches don't bleed.
_AC_ID_PREFIX_RE = re.compile(r"^AC\.([A-Z][A-Z0-9_]*)\.")


# Loam-internal AC namespaces — must NOT surface as domains. When
# matched against this blocklist, fall through to file-path-prefix.
# Update this set when adding new loam-internal AC namespaces. See
# F2 RF gap #7 (plan-doc §10).
LOAM_INTERNAL_AC_NAMESPACES: frozenset[str] = frozenset(
    {
        "OREK",       # odd-extractor scaffold
        "BANDS",      # banded contract types
        "SYNTH",      # synthetic fixtures
        "FIXTURES",   # fixture-management ACs
        "DPS1",       # dev-pattern-simplifications-1
        "DPS2",       # dev-pattern-simplifications-2
        "PRSG",       # PR-safety gate
        "WATCH",      # this cycle (v0.2.0 Cycle 1)
        "SKILLCAP",   # v0.2.0 Cycle 2 (forward; named here so the
                      # blocklist is right BEFORE Cycle 2 ships)
        "PPM",        # per-project-pm core
        "QSURF",      # per-project-pm question-surfacing
        "SAFETY",     # workspace-bootstrap safety_profile
        "BUDGET",     # cost-governance
        "MFBM",       # memory-system / M-FBM
        "D-sa",       # loam-amend seal
        "D-np",       # loam-amend new-plan
        "D-st",       # loam-amend status
    }
)


_UNCATEGORISED = "_uncategorised"


def _ac_id_prefix(ac_id: str) -> str | None:
    """Extract the `<DOMAIN>` segment from an AC ID, or None if the
    AC ID doesn't follow the canonical shape OR the domain is in the
    loam-internal blocklist.
    """
    if not ac_id:
        return None
    m = _AC_ID_PREFIX_RE.match(ac_id)
    if m is None:
        return None
    raw = m.group(1)
    if raw in LOAM_INTERNAL_AC_NAMESPACES:
        return None
    return raw.lower()


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


def _all_path_strings_for_ac(ac: "BandedAC") -> list[str]:
    """Collect all path-bearing strings from an AC: backing_files +
    citation file-paths (the part before ':' or '::').
    """
    paths: list[str] = []
    for bf in ac.backing_files:
        paths.append(str(bf))
    for cite in ac.evidence.citations:
        # Citations of shape "path:start-end" or "path::test_name".
        # Strip the suffix to get just the file path.
        if "::" in cite:
            paths.append(cite.split("::", 1)[0])
        elif ":" in cite:
            paths.append(cite.split(":", 1)[0])
        else:
            paths.append(cite)
    return paths


def infer_domain(ac: "BandedAC") -> str:
    """Infer a domain slug for `ac`.

    Per AC.WATCH.5 — primary path is AC ID prefix
    (`AC.<DOMAIN>.<n>` where DOMAIN is not in the loam-internal
    blocklist); fallback is longest common file-path-prefix across
    backing_files + citation file-paths; final fallback is
    `_uncategorised`.

    Returns a non-empty string. Pure function (no side effects).
    """
    primary = _ac_id_prefix(ac.ac_id)
    if primary:
        return primary
    paths = _all_path_strings_for_ac(ac)
    fallback = _common_path_prefix(paths)
    if fallback:
        return fallback
    return _UNCATEGORISED


def group_by_domain(
    proposals: list["IncrementalProposal"],
) -> "OrderedDict[str, list[IncrementalProposal]]":
    """Group `proposals` by their AC's inferred domain.

    Per AC.WATCH.5 — deterministic: same input always produces the
    same dict (keys sorted; insertion-order preserved within each
    value list). Load-bearing for AC.WATCH.4 idempotency check.

    Returns an :class:`OrderedDict` so callers can iterate in sorted-
    key order.
    """
    buckets: dict[str, list["IncrementalProposal"]] = {}
    for proposal in proposals:
        domain = infer_domain(proposal.ac)
        buckets.setdefault(domain, []).append(proposal)
    # Sort keys for determinism.
    return OrderedDict(sorted(buckets.items()))
