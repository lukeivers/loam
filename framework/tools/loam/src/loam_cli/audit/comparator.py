"""The substrate-audit comparator (AC.SOL-GATE.* / AC.SOL-RECONCILE.*).

The R-3 enforcement: compare a CLAIMED status against the derived
record (:mod:`loam_cli.audit.record`) and surface a DIVERGENCE — the
specific claim plus the ground-truth contradiction.

ONE comparator, two entry points. The doc-status caller extracts
structured status fields from a doc (D4 = structured fields only; NL
"rides existing X" prose-scanning is a separate later slice) and feeds
each as a :class:`ClaimedStatus`; the FBM caller
(:mod:`loam_cli.audit.reconcile`) feeds a stored memory claim. Both
route through :func:`compare_claim`.

The agree/diverge decision is made on the :class:`probe.Liveness`
LIVE_CLASSES / DARK_CLASSES partition: a doc that CLAIMS a component is
"dark"/"unbuilt" while ground truth puts it in a LIVE class is a
divergence; a doc that claims "live"/"merged" while ground truth is a
DARK class is a divergence; agreement (claim's class matches the
ground-truth side) passes clean (AC.SOL-GATE.2 — low false-positive,
the load-bearing risk: a noisy gate gets disabled).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from loam_cli.audit.probe import (
    DARK_CLASSES,
    LIVE_CLASSES,
    Liveness,
    normalize_claim_token,
)
from loam_cli.audit.record import ComponentState, StateOfLoam


@dataclass(frozen=True)
class ClaimedStatus:
    """A structured status claim extracted from a doc / task / memory.

    *component* names the subject; *claim_token* is the raw asserted
    status word (``"dark"`` / ``"live"`` / ``"merged"`` / ...);
    *source* is a human-readable provenance string (the doc path + a
    line hint) so the divergence report can name WHERE the stale claim
    lives.
    """

    component: str
    claim_token: str
    source: str


@dataclass(frozen=True)
class Divergence:
    """A detected claim-vs-reality divergence.

    Carries the offending claim, the ground-truth verdict it
    contradicts, and a rendered one-line explanation naming both — so a
    consumer (the gate, the verb, the reconcile caller) surfaces the
    specific claim + the contradiction, never a bare "mismatch".
    """

    component: str
    claimed: str
    derived: Liveness
    source: str
    detail: str


def _claim_side(claim: Liveness) -> str | None:
    """Return ``"live"`` / ``"dark"`` for the side a claim asserts, or
    ``None`` when the claim is not on either side (e.g. a ``BUILT``
    claim that asserts neither live-nor-dark for the agree/diverge
    decision)."""
    if claim in LIVE_CLASSES:
        return "live"
    if claim in DARK_CLASSES:
        return "dark"
    return None


def _derived_side(derived: Liveness) -> str | None:
    if derived in LIVE_CLASSES:
        return "live"
    if derived in DARK_CLASSES:
        return "dark"
    return None


def compare_claim(
    claim: ClaimedStatus,
    record: StateOfLoam,
) -> Divergence | None:
    """Compare one structured claim against the derived record.

    Returns a :class:`Divergence` when the claim's asserted side
    (live/dark) contradicts the ground-truth side, else ``None``
    (agreement OR not-decidable — the comparator never false-flags).

    The decision:

      * The claimed token is normalised to a :class:`Liveness` class.
        An unrecognised token → no divergence (we do not flag a claim
        we cannot interpret — that is the NL surface, out of scope).
      * The named component is looked up in the record. A component the
        record does not cover → no divergence (cannot compare against an
        absent ground truth — surfaced separately as a coverage gap, not
        a false flag).
      * The derived verdict is :attr:`Liveness.UNKNOWN` → no divergence
        (fail-safe: an indeterminate probe never produces a divergence —
        it degrades to "could not determine", never a false RED).
      * Claim asserts ``dark`` while ground truth is ``live`` → DIVERGE
        (today's literal case: a doc claims dark for a live component).
      * Claim asserts ``live`` while ground truth is ``dark`` → DIVERGE.
      * Same side → clean pass (AC.SOL-GATE.2).
    """
    claimed = normalize_claim_token(claim.claim_token)
    if claimed is None:
        return None
    row: ComponentState | None = record.by_name(claim.component)
    if row is None:
        return None
    if row.liveness is Liveness.UNKNOWN:
        return None
    claim_side = _claim_side(claimed)
    derived_side = _derived_side(row.liveness)
    if claim_side is None or derived_side is None:
        return None
    if claim_side == derived_side:
        return None
    detail = (
        f"{claim.component}: doc/claim says {claim.claim_token!r} "
        f"({claim_side}) but ground truth says {row.liveness.value} "
        f"({derived_side}) — {row.evidence}"
    )
    return Divergence(
        component=claim.component,
        claimed=claim.claim_token,
        derived=row.liveness,
        source=claim.source,
        detail=detail,
    )


def compare_claims(
    claims: list[ClaimedStatus],
    record: StateOfLoam,
) -> list[Divergence]:
    """Compare a batch of claims; return every divergence found."""
    out: list[Divergence] = []
    for claim in claims:
        d = compare_claim(claim, record)
        if d is not None:
            out.append(d)
    return out


# --------------------------------------------------------------------
# Structured claim extraction (D4 = structured status-fields only).
# --------------------------------------------------------------------

# A structured status line: ``<component>: <status>`` or
# ``status(<component>): <status>`` or a YAML-ish ``status: <token>``
# preceded by a ``component:`` field. The bounded, low-false-positive
# surface — NOT free-prose "rides existing X" scanning (a separate
# later slice with its own tighter AC).
#
# Matches lines of the form (case-insensitive on the status token):
#   FBM: dark
#   FBM status: dark
#   - FBM — dark
#   status(FBM): dark
_STATUS_LINE_RE = re.compile(
    r"""(?im)
    ^\s*[-*]?\s*                       # optional list bullet
    (?:status\(\s*)?                   # optional 'status(' prefix
    (?P<component>[A-Za-z][\w.\-/ ]*?) # the component name
    \s*\)?                             # optional ')'
    \s*(?:status)?\s*[:—-]\s*          # separator (: — -) maybe 'status'
    (?P<status>[A-Za-z][\w\- ]*?)      # the asserted status token
    \s*$
    """,
    re.VERBOSE,
)


def extract_claims_from_doc(
    text: str,
    *,
    source: str,
    components: frozenset[str] | None = None,
) -> list[ClaimedStatus]:
    """Extract STRUCTURED status claims from a doc body (D4-A).

    Scans for ``<component>: <status>`` structured status lines and
    returns a :class:`ClaimedStatus` for each whose component is in
    *components* (when supplied — the bounded set of components the
    record covers) AND whose status token is a recognised liveness
    claim. This is the bounded surface: it does NOT scan free prose for
    "rides existing X / X already does Y" claims (the unbounded,
    false-positive-prone surface, deferred to a later slice per D4).

    *source* labels every extracted claim's provenance (the doc path).
    """
    out: list[ClaimedStatus] = []
    for m in _STATUS_LINE_RE.finditer(text):
        component = m.group("component").strip()
        status = m.group("status").strip()
        if normalize_claim_token(status) is None:
            continue
        if components is not None and component not in components:
            continue
        line_no = text[: m.start()].count("\n") + 1
        out.append(
            ClaimedStatus(
                component=component,
                claim_token=status,
                source=f"{source}:{line_no}",
            )
        )
    return out
