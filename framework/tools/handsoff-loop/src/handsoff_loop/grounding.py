"""In-pipeline domain-grounding research (S2 — AC.DGR.*).

Between intent confirmation and gate-freeze, the pipeline researches
how practitioners ACTUALLY do the work the ask names — the standards
and expectations the deliverable should align with — via bounded web
research performed DURING the run, and writes the result as a durable,
indexable record at a predictable workspace path.

Honesty contract (AC.DGR.3, the claim-or-cite discipline):

  * citations are VERIFIED live in-run: every cited URL is resolved
    over HTTP before it enters the record; an unverifiable citation is
    dropped (recorded in the transcript), never presented as grounded;
  * research failure (no web access, timeout, unusable output, zero
    verifiable citations) degrades to an EXPLICITLY-FLAGGED ungrounded
    build the user is told about in plain language — never silent fake
    grounding, never invented citations;
  * the research budget is named and bounded: ONE research dispatch
    under :data:`GROUNDING_TIMEOUT_S`.

The record is packs-compatible (D3): YAML frontmatter + markdown body
at ``<workspace>/grounding/<stamp>-grounding.md`` — durable and
indexable now, carryable by the dispatch memory packs the moment that
cycle activates, with zero coupling today.

Where research cannot settle a judgment standard, the record carries
EXPERT-GATE FLAGS in plain language (AC.DGR.2's honest half) instead
of inventing a standard; S3's generated gate cites the record's norm
ids (``N1``, ``N2``, …) so gate criteria are traceable to named
practitioner norms.

Zero vertical code (AC.GEN.2): this module is domain-blind — the
domain enters ONLY through the live objective text.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from .intake import _claude_json

# The named, bounded research budget (AC.DGR.3): one dispatch, one
# generous ceiling. Terminal on timeout — never retried.
GROUNDING_TIMEOUT_S = 900
GROUNDING_MAX_DISPATCHES = 1

# Citation-resolution probe budget: per-URL HTTP timeout.
CITATION_PROBE_TIMEOUT_S = 15

# A citation "resolves live" when the host answered the in-run probe
# with any HTTP status below this (a 403 is a bot-blocked but live,
# real source; a 5xx / DNS failure / timeout is not a resolution).
CITATION_RESOLVED_BELOW_STATUS = 500


@dataclass(frozen=True)
class PractitionerNorm:
    """One researched norm with its live-verified citation."""

    norm_id: str          # "N1", "N2", ... — the gate-traceability key
    norm: str             # the practitioner norm, plain language
    source_url: str
    source_title: str
    http_status: int      # the in-run resolution evidence


@dataclass(frozen=True)
class GroundingOutcome:
    """The S2 stage outcome — grounded record or an explicit flag.

    ``grounded`` False ALWAYS carries a plain-language
    ``ungrounded_reason`` the user is told (AC.DGR.3) — there is no
    silent middle state.  ``record_path`` is the durable record when
    grounded ("" otherwise).  ``dropped_citations`` records every
    model-cited URL that failed the live probe (claim-or-cite: the
    drop is logged, never papered over).
    """

    grounded: bool
    objective: str
    summary: str = ""
    norms: list[PractitionerNorm] = field(default_factory=list)
    expert_gate_flags: list[str] = field(default_factory=list)
    record_path: str = ""
    ungrounded_reason: str = ""
    dropped_citations: list[dict] = field(default_factory=list)

    def as_evidence(self) -> dict:
        return {
            "grounded": self.grounded,
            "objective": self.objective,
            "summary": self.summary,
            "norms": [vars(n) for n in self.norms],
            "expert_gate_flags": list(self.expert_gate_flags),
            "record_path": self.record_path,
            "ungrounded_reason": self.ungrounded_reason,
            "dropped_citations": list(self.dropped_citations),
        }


_RESEARCH_PROMPT = """\
You are the domain-research step of a build pipeline. The confirmed
build objective is:

\"\"\"{objective}\"\"\"

Research, USING LIVE WEB SEARCH NOW, how practitioners in the relevant
field actually do this work: the standards, conventions, and quality
expectations a deliverable like this should align with. Fetch real
sources; cite ONLY pages you actually retrieved during this research —
NEVER cite from memory.

Return ONLY a JSON object (no prose, no code fence) with EXACTLY:
  - "summary": 2-4 plain-language sentences on how this work is done
    in practice and what a good result looks like to a practitioner.
  - "norms": an array of 3-6 objects, each
    {{"norm": <one plain-language practitioner norm or standard the
    deliverable should meet>, "source_url": <the URL you fetched>,
    "source_title": <its title>}}.
  - "expert_gate_flags": an array (possibly empty) of plain-language
    sentences naming any judgment standard your research could NOT
    settle — points where a human expert in the field should decide.
    NEVER invent a standard to fill a gap; flag it here instead.

Honesty rules: if you could not perform live web research, return
{{"research_failed": true, "reason": <plain sentence>}} instead.
"""


def _probe_url(url: str) -> int:
    """Resolve a citation live, in-run.  Returns the HTTP status, or
    -1 when the URL did not answer (DNS/timeout/scheme failure)."""
    if not re.match(r"^https?://", url or ""):
        return -1
    req = urllib.request.Request(
        url, method="HEAD",
        headers={"User-Agent": "loam-grounding-citation-probe/1.0"})
    try:
        with urllib.request.urlopen(
                req, timeout=CITATION_PROBE_TIMEOUT_S) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:  # noqa: BLE001 — any non-HTTP failure: no resolution
        try:
            # Some hosts reject HEAD; one GET attempt before giving up.
            req2 = urllib.request.Request(
                url, headers={
                    "User-Agent": "loam-grounding-citation-probe/1.0"})
            with urllib.request.urlopen(
                    req2, timeout=CITATION_PROBE_TIMEOUT_S) as resp:
                return int(resp.status)
        except urllib.error.HTTPError as exc:
            return int(exc.code)
        except Exception:  # noqa: BLE001
            return -1


def write_grounding_record(
    outcome: GroundingOutcome, *, workspace_dir: Path
) -> Path:
    """Write the durable, indexable grounding record (D3).

    Predictable path: ``<workspace>/grounding/<stamp>-grounding.md``.
    YAML frontmatter (kind/date/objective/counts) + markdown body —
    packs-compatible, packs-independent.
    """
    rec_dir = Path(workspace_dir) / "grounding"
    rec_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = rec_dir / f"{stamp}-grounding.md"
    lines = [
        "---",
        "kind: domain-grounding-record",
        f"date: {time.strftime('%Y-%m-%d')}",
        f"objective: {json.dumps(outcome.objective)}",
        f"citations: {len(outcome.norms)}",
        f"expert_gate_flags: {len(outcome.expert_gate_flags)}",
        "---",
        "",
        "# How practitioners do this work",
        "",
        outcome.summary.strip(),
        "",
        "## Practitioner norms (live-verified citations)",
        "",
    ]
    for n in outcome.norms:
        lines.append(
            f"- **{n.norm_id}** — {n.norm}  \n"
            f"  Source: [{n.source_title}]({n.source_url}) "
            f"(resolved in-run, HTTP {n.http_status})"
        )
    if outcome.expert_gate_flags:
        lines += ["", "## Where a human expert is needed", ""]
        lines += [f"- {f}" for f in outcome.expert_gate_flags]
    if outcome.dropped_citations:
        lines += ["", "## Citations dropped (did not resolve in-run)", ""]
        lines += [
            f"- {d.get('source_url', '?')} (status {d.get('http_status')})"
            for d in outcome.dropped_citations
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _ungrounded(objective: str, reason: str) -> GroundingOutcome:
    """The explicit, plain-language ungrounded outcome (AC.DGR.3)."""
    return GroundingOutcome(
        grounded=False,
        objective=objective,
        ungrounded_reason=(
            "I wasn't able to do the background research for this build "
            f"({reason}), so it is NOT grounded in how practitioners "
            "usually do this work. I can still build it, but you should "
            "know that up front."
        ),
    )


def research_domain(
    objective: str,
    *,
    workspace_dir: Path,
    model: str = "sonnet",
    llm_json_fn=None,
    url_probe_fn=None,
    timeout: int = GROUNDING_TIMEOUT_S,
) -> GroundingOutcome:
    """The bounded in-pipeline research step (AC.DGR.1/.2/.3).

    ONE dispatch (web-capable, spawn-isolated) under the named ceiling;
    every model-cited URL is probed live in-run; unverifiable citations
    are dropped and logged; zero surviving citations degrades to the
    explicitly-flagged ungrounded outcome.  On success the durable
    record is written under ``<workspace>/grounding/``.

    ``llm_json_fn`` / ``url_probe_fn`` are the injectable seams for
    deterministic tests; production uses the sealed spawn-isolated
    dispatch + a real HTTP probe.
    """
    if not (objective or "").strip():
        return _ungrounded(objective, "no confirmed objective to research")
    dispatch = llm_json_fn if llm_json_fn is not None else _claude_json
    probe = url_probe_fn if url_probe_fn is not None else _probe_url

    try:
        envelope = dispatch(
            _RESEARCH_PROMPT.format(objective=objective.strip()),
            model=model, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 — research failure is honest
        return _ungrounded(objective, f"the research step failed: {exc}")

    text = str((envelope or {}).get("result") or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return _ungrounded(objective, "the research output was unreadable")
    if not isinstance(payload, dict):
        return _ungrounded(objective, "the research output was unreadable")
    if payload.get("research_failed"):
        return _ungrounded(
            objective,
            str(payload.get("reason") or "live web research unavailable"))

    summary = str(payload.get("summary") or "").strip()
    raw_norms = payload.get("norms") or []
    norms: list[PractitionerNorm] = []
    dropped: list[dict] = []
    for raw in raw_norms if isinstance(raw_norms, list) else []:
        if not isinstance(raw, dict):
            continue
        norm = str(raw.get("norm") or "").strip()
        url = str(raw.get("source_url") or "").strip()
        title = str(raw.get("source_title") or url).strip()
        if not norm or not url:
            continue
        status = probe(url)
        if 0 <= status < CITATION_RESOLVED_BELOW_STATUS:
            norms.append(PractitionerNorm(
                norm_id=f"N{len(norms) + 1}",
                norm=norm, source_url=url, source_title=title,
                http_status=status))
        else:
            # Claim-or-cite: an unresolvable citation never enters the
            # record as grounding — dropped AND logged.
            dropped.append({"norm": norm, "source_url": url,
                            "http_status": status})

    if not norms or not summary:
        out = _ungrounded(
            objective,
            "no research citation could be verified live this run")
        return GroundingOutcome(
            grounded=False, objective=objective,
            ungrounded_reason=out.ungrounded_reason,
            dropped_citations=dropped)

    flags = [str(f).strip()
             for f in (payload.get("expert_gate_flags") or [])
             if str(f).strip()]
    outcome = GroundingOutcome(
        grounded=True, objective=objective, summary=summary,
        norms=norms, expert_gate_flags=flags,
        dropped_citations=dropped)
    record = write_grounding_record(outcome, workspace_dir=workspace_dir)
    return GroundingOutcome(
        grounded=True, objective=objective, summary=summary,
        norms=norms, expert_gate_flags=flags,
        record_path=str(record), dropped_citations=dropped)
