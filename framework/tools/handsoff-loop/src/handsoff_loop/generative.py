"""The generative middle (S3 — AC.GEN.*).

From the confirmed intent + the grounding record, loam DERIVES the
objective and GENERATES the deliverable's design: the tool plan, its
data shape, and its acceptance gate — none of which exists anywhere
before the run.  This is the stage the June-8 demo faked (pre-built
tool, hardcoded objective, single-vertical gate); here it is
real, and structurally domain-blind:

  * ZERO vertical-specific code (AC.GEN.2): this module contains no
    branch keyed to any business domain — the domain enters ONLY
    through the live intent + grounding inputs; one identical code
    path serves materially different domains.
  * The gate is authored DURING the run and handed to the existing
    freeze (``verify.freeze_acceptance``) BEFORE any build agent sees
    work — the frozen-unseen contract is preserved by construction
    (gate artifacts are written OUTSIDE the build work dir; sub-task
    briefs are checked by ``FrozenAcceptance.assert_unseen_by``
    exactly as the sealed spine always has; AC.GEN.1).
  * Gate criteria are TRACEABLE: when a grounding record exists, the
    generation must tie at least one criterion to a named practitioner
    norm (``N1``, ``N2``, …) from THAT record (AC.DGR.2); where the
    record flagged an expert-gate point, the design carries the flag
    forward instead of inventing a standard.
  * The verdict's judge-scope statement (what the gate did and did
    not verify) is generated in plain language (AC.GEN.3).

The held-out anti-overfit input is generated alongside the gate and
appears in no sub-task brief (the sealed anti-overfit contract,
carried through generation).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .grounding import GroundingOutcome
from .intake import _claude_json
from .request_intent import RequestIntent

# The single generous ceiling for the one generation dispatch.
GENERATE_TIMEOUT_S = 900


class GenerationUnavailable(RuntimeError):
    """The generative middle could not produce a usable design.

    Raised on dispatch/parse failure or an unusable design (empty
    gate, no tool plan).  The pipeline surfaces it plainly — a build
    never proceeds on a half-generated design, and there is no
    pre-built fallback (the whole point: nothing exists to fall back
    to)."""


@dataclass(frozen=True)
class GateCriterion:
    """One plain-language gate criterion with its traceability link.

    ``traceable_to`` names the grounding record's norm id ("N1", …)
    the criterion derives from, or "" when the criterion is intrinsic
    to the ask rather than practitioner-norm-derived (AC.DGR.2 needs
    >=1 traceable criterion when a grounding record exists)."""

    criterion: str
    traceable_to: str = ""


@dataclass(frozen=True)
class GeneratedDesign:
    """Everything the generative middle authored for THIS run.

    ``gate_files`` maps relative paths to file contents — the
    verification script + its fixture data, written by the pipeline
    under the run's gate dir (OUTSIDE the build work dir).
    ``check_command`` / ``held_out_command`` are templates carrying
    ``{gate_dir}`` and ``{work_dir}`` placeholders the pipeline
    substitutes at freeze time.  ``sub_tasks`` are the build briefs
    (which never contain the gate text — enforced downstream by
    ``assert_unseen_by``)."""

    objective: str
    tool_plan: str
    data_shape: str
    gate_plain: str
    gate_criteria: list[GateCriterion]
    gate_files: dict[str, str]
    check_command: str
    held_out_command: str
    sub_tasks: list[dict]
    judge_scope: str
    expert_gate_flags: list[str] = field(default_factory=list)

    def as_evidence(self) -> dict:
        return {
            "objective": self.objective,
            "tool_plan": self.tool_plan,
            "data_shape": self.data_shape,
            "gate_plain": self.gate_plain,
            "gate_criteria": [vars(c) for c in self.gate_criteria],
            "gate_files": sorted(self.gate_files),
            "check_command": self.check_command,
            "held_out_command": self.held_out_command,
            "sub_tasks": [st.get("name") for st in self.sub_tasks],
            "judge_scope": self.judge_scope,
            "expert_gate_flags": list(self.expert_gate_flags),
        }


_GENERATE_PROMPT = """\
You are the design-generation step of a build pipeline. Nothing about
this deliverable exists yet — you are authoring its design, its data
shape, and its acceptance gate from scratch, for THIS run only.

The confirmed intent:
\"\"\"{intent_block}\"\"\"

The build objective:
\"\"\"{objective}\"\"\"

{grounding_block}

Return ONLY a JSON object (no prose, no code fence) with EXACTLY:

  - "tool_plan": 2-5 plain sentences describing the tool to build and
    how a person will use it.
  - "data_shape": plain description of the input and output data this
    tool reads/writes (formats, columns/fields, where files live).
  - "gate_plain": a plain-English "done when:" statement a
    non-technical person can read — what the working tool will
    visibly do.
  - "gate_criteria": an array of objects
    {{"criterion": <one checkable plain-language criterion>,
      "traceable_to": <the practitioner-norm id ("N1","N2",...) this
      criterion comes from, or "" if it comes straight from the ask>}}.
    {traceability_rule}
  - "gate_files": an object mapping RELATIVE file paths to full file
    contents — a runnable verification script (python3, stdlib only)
    plus the sample input data it needs and any expected-output
    fixtures. The script must exercise the BUILT tool's real behavior
    (run it on the sample data, check its output), exit 0 only when
    every gate criterion holds, and print a short reason on failure.
    Include a SEPARATE held-out input fixture (different data, same
    shape) under a "held_out/" subpath that a second check run uses.
  - "check_command": a single shell command running the verification
    script against the primary fixture. Use the literal placeholders
    {{gate_dir}} (where gate_files land) and {{work_dir}} (where the
    tool is built) for all paths.
  - "held_out_command": the same check against the held-out fixture
    (same placeholders).
  - "sub_tasks": an array of 1-3 objects
    {{"name": <short-slug>, "brief": <what to build, concretely,
    including the data shape and where files live>,
    "tighter_acceptance": <one sentence, the sub-task's own narrower
    done>}}. Briefs must describe the WORK — they must NOT quote the
    gate_plain text, the gate file contents, or any gate file path
    (the gate stays unseen by builders).
  - "judge_scope": 1-3 plain sentences stating honestly what the gate
    checks and what it does NOT check (e.g. it verifies behavior on
    the sample and held-out data, not on every possible real file).

Hard rules: the verification script must be self-contained and
runnable with python3; never reference files that won't exist; the
tool is built in {{work_dir}} by builders who follow the briefs, so
briefs must name the exact tool filename/entrypoint the verification
script will invoke."""

_GROUNDING_PRESENT = """\
How practitioners actually do this work (researched live this run —
norms carry ids you must use for traceability):

{record_body}
"""

_GROUNDING_ABSENT = """\
NO practitioner grounding is available for this run (the research
step could not produce a verified record). Derive the gate from the
ask alone, and set every "traceable_to" to "". Do NOT invent
practitioner norms or standards.
"""

_TRACE_RULE_PRESENT = (
    "At least ONE criterion must have a non-empty \"traceable_to\" "
    "naming a norm id from the research above; never cite a norm id "
    "that is not in the research."
)
_TRACE_RULE_ABSENT = (
    "No grounding record exists, so every \"traceable_to\" must be \"\"."
)


def _grounding_block(grounding: GroundingOutcome | None) -> tuple[str, str]:
    if grounding is None or not grounding.grounded:
        return _GROUNDING_ABSENT, _TRACE_RULE_ABSENT
    lines = [grounding.summary.strip(), ""]
    for n in grounding.norms:
        lines.append(f"- {n.norm_id}: {n.norm} "
                     f"(source: {n.source_title}, {n.source_url})")
    if grounding.expert_gate_flags:
        lines.append("")
        lines.append("Points research could NOT settle (carry these "
                     "forward as expert-gate flags, do not invent "
                     "standards for them):")
        lines += [f"- {f}" for f in grounding.expert_gate_flags]
    return (_GROUNDING_PRESENT.format(record_body="\n".join(lines)),
            _TRACE_RULE_PRESENT)


def generate_design(
    intent: RequestIntent,
    grounding: GroundingOutcome | None,
    *,
    answers: dict[str, str] | None = None,
    model: str = "sonnet",
    llm_json_fn=None,
    timeout: int = GENERATE_TIMEOUT_S,
) -> GeneratedDesign:
    """Generate the deliverable's design for THIS run (AC.GEN.1).

    One bounded dispatch.  The output is validated structurally —
    an empty gate, missing verification files, or briefs that quote
    the gate raise :class:`GenerationUnavailable` (a half-generated
    design never reaches the freeze)."""
    intent_block = intent.inferred_intent
    if answers:
        qa = "; ".join(f"{q} -> {a}" for q, a in answers.items()
                       if str(a).strip())
        if qa:
            intent_block += f"\nClarifications from the user: {qa}"
    g_block, trace_rule = _grounding_block(grounding)
    prompt = _GENERATE_PROMPT.format(
        intent_block=intent_block,
        objective=intent.objective,
        grounding_block=g_block,
        traceability_rule=trace_rule,
    )
    dispatch = llm_json_fn if llm_json_fn is not None else _claude_json
    try:
        envelope = dispatch(prompt, model=model, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        raise GenerationUnavailable(
            f"design generation dispatch failed: {exc}") from exc

    text = str((envelope or {}).get("result") or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GenerationUnavailable(
            f"design generation output not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GenerationUnavailable("design generation output not an object")

    gate_plain = str(payload.get("gate_plain") or "").strip()
    check_command = str(payload.get("check_command") or "").strip()
    gate_files = payload.get("gate_files") or {}
    tool_plan = str(payload.get("tool_plan") or "").strip()
    raw_subs = payload.get("sub_tasks") or []
    if not (gate_plain and check_command and tool_plan
            and isinstance(gate_files, dict) and gate_files
            and isinstance(raw_subs, list) and raw_subs):
        raise GenerationUnavailable(
            "design generation produced an unusable design (empty gate, "
            "no verification files, or no build plan) — refusing to "
            "freeze a half-generated gate")
    if "{gate_dir}" not in check_command:
        raise GenerationUnavailable(
            "generated check_command does not target the gate dir — "
            "an unanchored gate cannot be frozen honestly")

    criteria = []
    for raw in payload.get("gate_criteria") or []:
        if isinstance(raw, dict) and str(raw.get("criterion", "")).strip():
            criteria.append(GateCriterion(
                criterion=str(raw["criterion"]).strip(),
                traceable_to=str(raw.get("traceable_to", "") or "").strip(),
            ))
    known_ids = {n.norm_id for n in (grounding.norms if grounding else [])}
    # Claim-or-cite on traceability: a cited norm id must exist in the
    # record; a fabricated citation is a refusal, not a footnote.
    for c in criteria:
        if c.traceable_to and c.traceable_to not in known_ids:
            raise GenerationUnavailable(
                f"gate criterion cites norm {c.traceable_to!r} that is "
                f"not in the grounding record — fabricated traceability")
    if grounding is not None and grounding.grounded:
        if not any(c.traceable_to for c in criteria):
            raise GenerationUnavailable(
                "a grounding record exists but no gate criterion is "
                "traceable to a practitioner norm (AC.DGR.2)")

    sub_tasks = []
    for raw in raw_subs:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip()
        brief = str(raw.get("brief") or "").strip()
        tighter = str(raw.get("tighter_acceptance") or "").strip()
        if not (name and brief and tighter):
            continue
        # Frozen-unseen by construction: a brief that quotes the gate
        # text or names a gate file is rejected at generation time
        # (assert_unseen_by re-checks at dispatch — belt and braces).
        if gate_plain in brief or any(p in brief for p in gate_files):
            raise GenerationUnavailable(
                f"sub-task {name!r} brief leaks the gate — refusing")
        sub_tasks.append({"name": name, "brief": brief,
                          "tighter_acceptance": tighter})
    if not sub_tasks:
        raise GenerationUnavailable("no usable sub-task briefs generated")

    flags = list(grounding.expert_gate_flags) if (
        grounding is not None and grounding.grounded) else []
    return GeneratedDesign(
        objective=intent.objective,
        tool_plan=tool_plan,
        data_shape=str(payload.get("data_shape") or "").strip(),
        gate_plain=gate_plain,
        gate_criteria=criteria,
        gate_files={str(k): str(v) for k, v in gate_files.items()},
        check_command=check_command,
        held_out_command=str(payload.get("held_out_command") or "").strip(),
        sub_tasks=sub_tasks,
        judge_scope=str(payload.get("judge_scope") or "").strip(),
        expert_gate_flags=flags,
    )


def write_gate_files(design: GeneratedDesign, *, gate_dir: Path) -> list[str]:
    """Materialise the generated gate artifacts OUTSIDE the work dir.

    Returns the written paths.  The pipeline calls this before the
    freeze; builders work in a separate work dir and their briefs
    never carry these paths (AC.GEN.1 / frozen-unseen)."""
    gate_dir = Path(gate_dir)
    written = []
    for rel, content in design.gate_files.items():
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise GenerationUnavailable(
                f"generated gate file path escapes the gate dir: {rel!r}")
        dest = gate_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written.append(str(dest))
    return written


def resolve_command(template: str, *, gate_dir: Path, work_dir: Path) -> str:
    """Substitute the {gate_dir}/{work_dir} placeholders at freeze time."""
    return (template
            .replace("{gate_dir}", str(gate_dir))
            .replace("{work_dir}", str(work_dir)))


def render_verdict(
    design: GeneratedDesign, *, reached_done: bool,
    stop_reason: str, evidence_tail: str = "",
) -> str:
    """The plain-language verdict with judge-scope honesty (AC.GEN.3).

    States the result either polarity, then exactly what the gate did
    and did not verify — never a bare "it works"."""
    if reached_done:
        head = "Done — the tool passed its acceptance check."
    else:
        head = ("Not done — the build stopped honestly "
                f"({stop_reason}). This is reported straight, not "
                "retried until it looks green.")
    scope = design.judge_scope.strip() or (
        "The check ran the tool on prepared sample data and held-out "
        "data; it did not verify behavior on other inputs.")
    parts = [head, f"What was checked, honestly: {scope}"]
    if design.expert_gate_flags:
        parts.append(
            "Points that still need a human expert's judgment: "
            + " ".join(design.expert_gate_flags))
    if evidence_tail.strip():
        parts.append(f"Check output (last lines): {evidence_tail.strip()}")
    return "\n\n".join(parts)
