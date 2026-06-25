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


@dataclass(frozen=True)
class CandidateDesign:
    """One reviewable candidate design (AC.DF.1).

    A LIGHTWEIGHT review artifact — what the user looks at to pick a
    direction, NOT the full buildable design.  The expensive buildable
    artifact (the verification scripts + held-out fixtures + sub-task
    briefs the freeze consumes) is generated for the ONE chosen
    direction only, via the existing single-design ``generate_design``
    — generating N full buildable gates in one dispatch overruns the
    generation budget (empirically: a single N=3 dispatch carrying full
    gate_files times out at the 900s ceiling; the lightweight N=3
    dispatch returns in ~170s).  This split is the §14 D-build.1 /
    D-build.2 method call: candidate review is cheap, the buildable
    gate is generated once on the settled direction (Lens 5 — each
    stage's scope is tighter than producing all N full designs at
    once).

    Fields:

      * ``form_factor`` — a short label naming the design DIRECTION
        (e.g. "one-shot CLI", "interactive review-queue app",
        "scheduled background normalizer"). Distinctness across
        candidates is asserted on this, so the N candidates are
        materially different directions, not three phrasings of one
        design (AC.DF.1 / SAL-DF-3).
      * ``tool_plan`` / ``data_shape`` / ``gate_plain`` — the plain-
        language review surface (what the tool is, what it reads/
        writes, what "done" looks like).
      * ``sample_output`` — a representative SAMPLE OUTPUT the tool
        would PRODUCE, structured at the demo-grade quality bar (named
        sections, a populated tabular result, a plain-language summary,
        a review-queue-equivalent surface). This is the centerpiece the
        user reviews — they see what the thing will produce, not how it
        is coded (D-2, implementation-agnostic). AC.DF.5's rubric checks
        this rendering. The rubric is purely STRUCTURAL (section count /
        table / summary / review surface) — domain-blind, no vertical
        branch (AC.GEN.2).
      * ``launch_mechanism`` — a short label naming HOW the user starts
        the tool (e.g. "web app opened by URL", "double-click app",
        "scheduled email report"). For a non-technical user this MUST be
        a launcher they can personally operate — a browser URL/link, a
        double-click packaged app, or email/file delivery — never a
        terminal/script/dev-env launch (AC.DF.7).
      * ``user_workflow`` — the ORDERED, literal end-to-end steps the
        target user personally takes to LAUNCH and USE the tool (e.g.
        "Open your web browser", "Go to <address>", "Drag your two files
        onto the page", "Click Run", "Review the flagged rows").
        This is what makes "visible output" sufficient: a design whose
        output is a GUI but whose only way in is "run the script" leaks a
        developer task back to the user (AC.DF.7).

    ``sample_output`` is a structured dict (the rendering substrate);
    a caller may lay it out as plain text or HTML — the rendering
    POLISH is a presentation concern, the structured content is the
    build target the rubric scores."""

    form_factor: str
    tool_plan: str
    data_shape: str
    gate_plain: str
    sample_output: dict
    launch_mechanism: str = ""
    user_workflow: tuple[str, ...] = ()

    def as_evidence(self) -> dict:
        return {
            "form_factor": self.form_factor,
            "tool_plan": self.tool_plan,
            "data_shape": self.data_shape,
            "gate_plain": self.gate_plain,
            "sample_output_sections": sorted(self.sample_output.keys()),
            "launch_mechanism": self.launch_mechanism,
            "user_workflow": list(self.user_workflow),
        }

    def as_direction_brief(self) -> str:
        """A plain-language statement of THIS candidate's direction the
        buildable-design generation conditions on (so the chosen
        direction's form factor + output shape + LAUNCH mechanism survive
        into the full design).

        The launch mechanism + user workflow are carried so the buildable
        design HONORS the form-factor the user settled on — a candidate
        committed to "web app opened by URL" conditions the build toward a
        browser-openable app, NOT a bare desktop script the user would have
        to start from a terminal (AC.DF.7 build-target linkage)."""
        workflow_block = ""
        if self.user_workflow:
            steps = "\n".join(f"  {i + 1}. {s}"
                              for i, s in enumerate(self.user_workflow))
            workflow_block = (
                "\nThe user's literal end-to-end workflow (the tool MUST be "
                "launchable + usable by exactly these steps):\n" + steps)
        launch_block = ""
        if self.launch_mechanism:
            launch_block = (
                f"\nLaunch mechanism the build MUST target: "
                f"{self.launch_mechanism}. Build the tool so the target "
                "user can start it this way — do NOT deliver a form-factor "
                "the user cannot launch (e.g. a desktop script started from "
                "a terminal when the design commits to a web app opened by "
                "URL).")
        return (f"Design direction: {self.form_factor}\n"
                f"Tool plan: {self.tool_plan}\n"
                f"Data shape: {self.data_shape}\n"
                f"Done when: {self.gate_plain}"
                + launch_block + workflow_block)


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


# --- design-first front stage: N candidate designs (AC.DF.*) ---------
#
# generate_candidate_designs asks the SAME domain-blind generation
# contract for N materially-distinct candidate designs, each carrying a
# polished sample-output rendering at the demo-grade quality bar.  The
# single-design generate_design path is UNTOUCHED (it stays
# the n=1 degenerate / non-interactive default the sealed S6 proof
# uses).  One dispatch returns all N (D-build.1) — no new spawn surface
# beyond the sealed _claude_json primitive (no API key; AC.GEN.2 domain-
# blindness preserved — the prompt carries no vertical branch).

# The rubric the AC.DF.5 sample-output rendering must satisfy — a
# purely STRUCTURAL bar (no vertical branch, AC.GEN.2): a populated
# section map with >= N named sections, at least one populated tabular
# result, a plain-language summary, and a review surface naming what a
# human should look at.  The provenance of this bar (the demo whose
# output shape it generalises) is named only in the plan-doc + the
# AC.DF.5 test, NEVER in this source.  The generation prompt NEVER
# carries this rubric, so a candidate that satisfies it is checked by
# something the generator never saw (AC.DF.5).
SAMPLE_RUBRIC_MIN_SECTIONS = 3


def design_rubric_check(sample_output: dict) -> tuple[bool, str]:
    """Score a candidate's sample-output rendering against the bar.

    Returns ``(ok, reason)``.  Rubric (purely structural, domain-blind;
    NOT shown to the generator — AC.DF.5):

      1. >= SAMPLE_RUBRIC_MIN_SECTIONS named output sections;
      2. at least one POPULATED tabular result (a list of >=1 row,
         each row a dict / record);
      3. a plain-language SUMMARY (a non-empty prose string section);
      4. a REVIEW-QUEUE-equivalent (a section naming items that need a
         human's eyes, OR an empty-but-named review surface).

    A rendering that meets all four reaches the named quality bar."""
    if not isinstance(sample_output, dict) or not sample_output:
        return False, "sample_output is not a populated section map"
    sections = [k for k, v in sample_output.items()
                if v not in (None, "", [], {})]
    if len(sections) < SAMPLE_RUBRIC_MIN_SECTIONS:
        return False, (
            f"only {len(sections)} populated section(s); rubric needs "
            f">= {SAMPLE_RUBRIC_MIN_SECTIONS} named sections")

    def _is_table(v) -> bool:
        return (isinstance(v, list) and len(v) >= 1
                and all(isinstance(row, dict) for row in v))

    def _is_summary(v) -> bool:
        return isinstance(v, str) and len(v.strip()) >= 40

    def _names_review(key: str) -> bool:
        k = key.lower()
        return any(t in k for t in ("review", "queue", "flag", "needs_"))

    has_table = any(_is_table(v) for v in sample_output.values())
    has_summary = any(_is_summary(v) for v in sample_output.values())
    has_review = any(_names_review(k) for k in sample_output)
    missing = []
    if not has_table:
        missing.append("a populated tabular result (a list of >=1 row "
                       "records)")
    if not has_summary:
        missing.append("a plain-language summary section (prose, "
                       ">=40 chars)")
    if not has_review:
        missing.append("a review-queue-equivalent section (a section "
                       "naming items that need a human's eyes)")
    if missing:
        return False, "sample output is missing: " + "; ".join(missing)
    return True, (
        f"{len(sections)} sections, a populated table, a plain-language "
        "summary, and a review-queue surface")


# A LIGHTWEIGHT candidate-review timeout: the candidate dispatch is the
# cheap review-surface call (no gate_files / verification scripts — those
# are generated for the chosen design only), so it fits a much tighter
# bound than the full-design GENERATE_TIMEOUT_S.
CANDIDATES_TIMEOUT_S = 600

# The finite re-dispatch bound for the large-JSON transient (see
# generate_candidate_designs). NOT retry-until-green — a bounded best.
CANDIDATES_PARSE_ATTEMPTS = 3


# --- tech-level framing of the candidate space (AC.DF.6) -------------
#
# Candidate designs are framed for the USER'S tech level, DEFAULTING to a
# NON-TECHNICAL user (the owner ruling
# `2026-06-24-design-first-non-tech-user-visible-outputs`).  For a
# non-technical user every surfaced candidate must be something they can
# personally SEE and USE without developer skill — a visible/interactive
# experience OR a sensible automated delivery — and NO candidate may hand
# them developer machinery (a command-line tool, a daemon /
# background-watch service they must manage, a drop-folder to configure).
# This is the prime directive applied to the design stage: the user
# brings WHAT in their terms; the design they review is in their
# vocabulary (visible outcomes), never the machinery.
#
# The constraint is enforced two ways so a non-tech user is guaranteed a
# clean candidate set even if one layer slips: (1) the direction SEEDS
# the non-tech user draws from are partitioned to the see-and-use /
# sensible-delivery families (no CLI / daemon seed is offered to a
# non-tech user), and the prompt carries an explicit tech-level
# constraint; (2) a held-out STRUCTURAL classifier (is_nontech_operable)
# drops any candidate whose primary interaction still reads as a CLI /
# daemon / background-watch surface.  The classifier is the falsifiable
# AC.DF.6 check — it runs over the candidate's own fields, never sees the
# generation prompt, and is domain-blind (it keys on interaction-surface
# vocabulary, NOT on any business domain — AC.GEN.2).

# Tech-level labels.  Only "non_technical" is constrained here; "technical"
# leaves the full seed set + no surface constraint.  The DEFAULT is
# non-technical (the owner ruling + the demo case).
TECH_LEVEL_NON_TECHNICAL = "non_technical"
TECH_LEVEL_TECHNICAL = "technical"

# Interaction-surface vocabulary that DISQUALIFIES a candidate for a
# non-technical user — a CLI / daemon / background-watch primary surface
# (the rehearsal-1 failure: a "command-line tool" candidate + a
# "file-watch daemon" candidate offered to a non-technical user, who
# cannot operate either; the domain context is named in the AC.DF.6 test +
# the plan-doc, never here).  Domain-blind: these name developer-machinery
# interaction surfaces, no business domain (AC.GEN.2).  Whole-word matched
# so "report" does not
# trip on "port" and a benign "the service emails you" delivery phrasing
# is handled by the positive-affordance check below, not by a bare
# substring.
_NONTECH_DISQUALIFYING_TERMS = (
    "command-line", "command line", "commandline", "cli",
    "terminal", "shell command", "run this command",
    "daemon", "background service", "background process",
    "file-watch", "file watcher", "watch folder", "watched folder",
    "drop folder", "drop-folder", "watch a folder", "watches a folder",
    "cron job", "crontab", "config file", "configuration file",
    "edit the config", "set up a folder",
)

# Positive affordances that mark a candidate as non-tech operable — a
# visible/interactive experience the user opens, OR a sensible automated
# delivery (the finished result arrives, e.g. by email).  A candidate
# whose primary surface trips a disqualifying term is rescued ONLY if its
# direction label clearly names a delivery/visible affordance (a
# "scheduled email report" is fine even though "scheduled" is adjacent to
# the daemon family).
_NONTECH_OPERABLE_TERMS = (
    "app", "web", "website", "page", "screen", "dashboard", "portal",
    "form", "wizard", "assistant", "chat", "review queue", "review-queue",
    "email", "emails you", "emailed", "sent to you", "arrives", "inbox",
    "report you open", "document you open", "delivered", "notification",
)


def is_nontech_operable(form_factor: str, tool_plan: str = "") -> tuple[bool, str]:
    """Held-out structural check: is this candidate operable by a
    NON-TECHNICAL user with a visible / delivered output? (AC.DF.6).

    Returns ``(ok, reason)``.  Domain-blind, prompt-blind: it reads only
    the candidate's interaction-surface vocabulary (the form_factor label
    + tool_plan prose), never the generation prompt and never any
    business domain.  A candidate is DISQUALIFIED for a non-tech user when
    its primary surface reads as developer machinery — a command-line
    tool, a daemon / background-watch service, a drop-folder to configure
    — UNLESS the same text clearly names a sensible-delivery or visible
    affordance (a scheduled EMAIL report is operable; a background daemon
    the user must manage is not).

    This is the falsifiable AC.DF.6 check the generator never saw."""
    blob = f"{form_factor}\n{tool_plan}".lower()
    has_operable = any(t in blob for t in _NONTECH_OPERABLE_TERMS)
    hit = next((t for t in _NONTECH_DISQUALIFYING_TERMS if t in blob), None)
    if hit is None:
        # No developer-machinery surface named — operable by construction
        # (a plain visible/interactive or delivery candidate).
        return True, "no developer-machinery surface; non-tech operable"
    if has_operable:
        # A disqualifying term appears, but a visible/delivery affordance
        # also does (e.g. "scheduled" + "emails you the report") — the
        # primary surface the user touches is the visible/delivered one.
        return True, (
            f"names {hit!r} but also a non-tech affordance — primary "
            "surface is visible/delivered")
    return False, (
        f"primary interaction is developer machinery ({hit!r}); a "
        "non-technical user cannot operate it — disqualified for a "
        "non-tech user (AC.DF.6)")


# --- launch-workflow operability (AC.DF.7) ---------------------------
#
# AC.DF.6 guarantees the candidate's OUTPUT is visible (a wizard/app, not
# a CLI).  AC.DF.7 goes one layer deeper: a design can be visible (a GUI)
# yet still UN-LAUNCHABLE by the target user — the rehearsal-2 failure
# built a Tkinter wizard whose only way in was `python the_gui.py`
# in a terminal.  Visible output is necessary but NOT sufficient: the
# whole path to STARTING and USING the tool must be operable by the
# target user, or the design has leaked a developer task back to them
# (owner ruling 2026-06-24-design-must-carry-user-operable-launch-workflow).
#
# So every candidate carries (a) a launch_mechanism label and (b) the
# literal end-to-end user_workflow.  For a non-technical user the
# launch_mechanism MUST be one they can operate — a browser URL/link, a
# double-click packaged app, or email/file delivery — and the workflow
# must NOT contain a terminal/script/dev-env step.  The held-out
# is_launch_user_operable classifier enforces this domain-blind +
# prompt-blind, exactly like is_nontech_operable: it reads only the
# launch surface vocabulary, never the generation prompt, never a
# business domain (AC.GEN.2).

# Launch-surface vocabulary that DISQUALIFIES a non-tech launch — a
# terminal, a script run, a dev-env install (the rehearsal-2 failure:
# `python the_gui.py` in a terminal).  Whole-phrase matched so a
# benign "open the app" is not tripped.  Domain-blind: these name
# developer launch tasks, no business domain (AC.GEN.2).
_LAUNCH_DISQUALIFYING_TERMS = (
    "terminal", "command line", "command-line", "commandline",
    "command prompt", "shell", "run the script", "run a script",
    "run this script", "run the command", "run a command",
    "python ", "python3", "pip install", "npm install", "npm run",
    "node ", "./", "$ ", "execute the", "run the program from",
    "install python", "install node", "virtualenv", "venv",
    "dev environment", "development environment", "command in",
)

# Launch surfaces a non-tech user CAN operate — a browser URL/link, a
# double-click packaged app (an icon), or email/file delivery.  A launch
# that names one of these (and no disqualifying step) is operable.
_LAUNCH_OPERABLE_TERMS = (
    "browser", "url", "link", "open the page", "open the website",
    "go to ", "double-click", "double click", "click the icon",
    "app icon", "desktop icon", "tap the", "open the app",
    "email", "emailed", "sent to you", "arrives in your inbox",
    "in your inbox", "delivered to you", "open the file we send",
    "web app", "web page", "website", "bookmark",
)


def is_launch_user_operable(
    launch_mechanism: str, user_workflow=(),
) -> tuple[bool, str]:
    """Held-out structural check: can the TARGET (non-technical) user
    personally LAUNCH and USE this candidate end-to-end? (AC.DF.7).

    Returns ``(ok, reason)``.  Domain-blind, prompt-blind: it reads only
    the candidate's launch-surface vocabulary (the launch_mechanism label
    + the literal user_workflow steps), never the generation prompt and
    never a business domain.  A candidate is DISQUALIFIED for a non-tech
    user when its launch / workflow requires developer machinery to START
    it — opening a terminal, running a script (``python foo.py``),
    installing a dev environment — even if its OUTPUT is a GUI.  It is
    operable when the launch is a browser URL/link, a double-click app, or
    email/file delivery AND no workflow step requires a technical task.

    This is the falsifiable AC.DF.7 check the generator never saw — the
    layer beneath AC.DF.6 (visible output is necessary, an operable launch
    is the rest)."""
    steps = list(user_workflow or ())
    blob = (str(launch_mechanism) + "\n" + "\n".join(str(s) for s in steps)).lower()
    if not str(launch_mechanism).strip() and not steps:
        # No launch path stated at all — the design has not told the user
        # how to start it; it cannot be vouched operable.
        return False, (
            "no launch mechanism or user workflow stated; the user is not "
            "told how to START the tool (AC.DF.7)")
    hit = next((t for t in _LAUNCH_DISQUALIFYING_TERMS if t in blob), None)
    if hit is not None:
        return False, (
            f"the launch / workflow requires a developer task ({hit.strip()!r}) "
            "to START the tool; a non-technical user cannot do that — even a "
            "visible GUI is un-launchable this way (AC.DF.7)")
    has_operable = any(t in blob for t in _LAUNCH_OPERABLE_TERMS)
    if not has_operable:
        # No disqualifying step, but no recognised operable launcher
        # either — the launch path is not vouched as one a non-tech user
        # can start (a bare "open the tool" with no URL/icon/delivery).
        return False, (
            "no operable launcher named (a browser URL/link, a double-click "
            "app, or email/file delivery); the launch path is not one a "
            "non-technical user is shown how to start (AC.DF.7)")
    return True, (
        "launch is a non-tech-operable surface (browser URL / double-click "
        "app / delivery) with no developer-task step")


# Per-candidate (ONE design) prompt. Each candidate is its own bounded
# dispatch — N dispatches, not one N-object response (the §11 sanctioned
# alternative).  A single-candidate JSON is ~half the size of the
# N-object response and the model emits it reliably (measured 3/3 clean
# vs ~1/3 on the batched call, where deeply-nested trailing braces on a
# rich sample_output got mis-nested).  {direction_seed} rotates the
# direction across the N calls so the candidates come out materially
# distinct; {avoid_block} names the directions already taken so a later
# call does not collide with an earlier one.  {tech_constraint} carries
# the tech-level framing (AC.DF.6) — for a non-tech user it forbids the
# developer-machinery surfaces.
_CANDIDATE_PROMPT = """\
You are the design step of a build pipeline. Nothing about this
deliverable exists yet. Propose ONE candidate design for the ask, in
this DESIGN DIRECTION: {direction_seed}. This is a review candidate —
keep it light (no code, no verification scripts); the full buildable
plan is generated later if the person picks this one.
{tech_constraint}{avoid_block}
The confirmed intent:
\"\"\"{intent_block}\"\"\"

The build objective:
\"\"\"{objective}\"\"\"

{grounding_block}

Return ONLY a JSON object (no prose, no code fence) with EXACTLY:

  - "form_factor": a short label (<= 8 words) naming this candidate's
    design direction (in the spirit of "{direction_seed}").
  - "tool_plan": 2-5 plain sentences describing the tool and how a
    person uses it.
  - "data_shape": plain description of the input and output data
    (formats, columns/fields, where files live).
  - "gate_plain": a plain-English "done when:" statement.
  - "sample_output": a RICH, REPRESENTATIVE sample of what THIS tool
    would actually PRODUCE when run on realistic input — a JSON object
    whose keys are NAMED OUTPUT SECTIONS. Make it the thing the user
    most wants to see: it must include at least THREE named sections,
    and among them at least one POPULATED TABLE (a key whose value is
    an array of >=2 row objects with realistic field values), at least
    one PLAIN-LANGUAGE SUMMARY (a key whose value is a few sentences of
    readable prose stating the headline result in numbers a person
    cares about), and at least one REVIEW section (a key named with
    "review"/"queue"/"flag" listing the items a human should look at,
    even if that list is short). This is what the prospect sees to
    judge the design — make it polished and concrete, not a stub.
  - "launch_mechanism": a short label (<= 8 words) naming HOW the person
    STARTS the tool (e.g. "web app opened by URL", "double-click app",
    "scheduled email report").
  - "user_workflow": an ARRAY of short plain-language strings — the
    LITERAL, ordered steps the person personally takes to LAUNCH and
    USE the tool, start to finish (e.g. ["Open your web browser", "Go to
    the address we give you", "Drag your two files onto the page",
    "Click Run", "Review the flagged rows"]). These are the real
    steps a non-technical person would follow at their desk."""


# The rotating direction seeds — generic design DIRECTIONS, NOT vertical
# branches (AC.GEN.2: these name interaction/form-factor families, no
# business domain). The seed biases distinctness; the model still derives
# the actual design from the live ask.  TWO seed sets, partitioned by tech
# level (AC.DF.6): a non-technical user draws ONLY from see-and-use /
# sensible-delivery families (no CLI / daemon seed); a technical user gets
# the full set.
_DIRECTION_SEEDS_TECHNICAL = [
    "a one-shot command-line tool that does the whole job in a single run",
    "an interactive review-queue app that surfaces ambiguous items for a "
    "human to resolve",
    "a scheduled background service that runs automatically on each new "
    "batch of input",
    "a conversational assistant the person talks to step by step",
    "a single self-contained report generator that produces one rich "
    "document",
]

# Non-technical seed set (the DEFAULT — the owner ruling + the demo case).
# Every direction here is something a non-technical user can personally
# SEE and USE: a visible/interactive experience they open, OR a sensible
# automated delivery where the finished result ARRIVES (e.g. emailed on a
# schedule).  NO command-line / daemon / drop-folder direction — those are
# developer machinery a non-tech user cannot operate (AC.DF.6).  Still
# domain-blind: these name interaction/form-factor families, no business
# domain (AC.GEN.2).
_DIRECTION_SEEDS_NON_TECHNICAL = [
    "a simple web page or app the person opens in their browser, reviews "
    "the result on screen, and approves with a click",
    "an interactive review-queue screen that shows the items needing a "
    "person's eyes and lets them fix each one in place",
    "a sensible automated delivery: the finished, ready-to-read result is "
    "emailed to the person on a schedule, no setup for them to manage",
    "a step-by-step assistant the person talks to in plain language and "
    "that shows them the result as they go",
    "a single polished report the person opens and reads — one rich "
    "document laid out for a non-technical reader",
]

# Back-compat alias: the historical _DIRECTION_SEEDS name = the full
# technical set (the pre-AC.DF.6 behaviour for a technical user).
_DIRECTION_SEEDS = _DIRECTION_SEEDS_TECHNICAL


# The tech-level constraint injected into the per-candidate prompt
# (AC.DF.6).  For a non-technical user it forbids the developer-machinery
# surfaces and demands a see-and-use / sensible-delivery candidate stating
# what the user PERSONALLY does + what the OUTPUT looks like.
_NONTECH_PROMPT_CONSTRAINT = """\

The person you are designing for is NON-TECHNICAL. The candidate MUST be
something they can personally SEE and USE without any developer skill:
either (a) a visible/interactive experience they open — a web page, an
app, a screen, a form, a report they read — or (b) a sensible automated
delivery where the finished result ARRIVES for them (for example, it is
emailed to them on a schedule). State plainly WHAT THE PERSON PERSONALLY
DOES (and it must be doable by a non-technical person) and WHAT THE OUTPUT
LOOKS LIKE (a visible result). Do NOT propose a command-line tool, a
script they run in a terminal, a daemon or background service they have to
manage, a folder they must set up for files to be dropped into, or
anything that assumes they can operate developer machinery — those are
forbidden for this person.

CRITICAL — HOW THEY START IT: the person must be able to personally LAUNCH
the tool with NO technical task. The launch_mechanism MUST be one of: (a) a
WEB APP they open in their browser by typing/clicking a URL or link, (b) a
DOUBLE-CLICK packaged app (an icon they click), or (c) EMAIL/FILE DELIVERY
where the finished result simply arrives. The user_workflow steps MUST
start with one of those launches. NEVER write a step that requires opening
a terminal, running a script (for example "python something.py"),
installing Python or a development environment, or any command-line task —
a design whose only way in is "run the script" is FORBIDDEN even if its
output is a nice screen.
"""

_TECHNICAL_PROMPT_CONSTRAINT = ""


def _seeds_for(user_tech_level: str) -> list[str]:
    """The direction-seed set for the user's tech level (AC.DF.6).

    Non-technical (the default) → the see-and-use / sensible-delivery
    seeds only; technical → the full set."""
    if user_tech_level == TECH_LEVEL_TECHNICAL:
        return _DIRECTION_SEEDS_TECHNICAL
    return _DIRECTION_SEEDS_NON_TECHNICAL


def _tech_constraint_for(user_tech_level: str) -> str:
    """The prompt constraint string for the user's tech level (AC.DF.6)."""
    if user_tech_level == TECH_LEVEL_TECHNICAL:
        return _TECHNICAL_PROMPT_CONSTRAINT
    return _NONTECH_PROMPT_CONSTRAINT


def _candidate_from_payload(raw: dict) -> CandidateDesign:
    """Validate ONE lightweight candidate payload into a CandidateDesign.

    The review surface only — a usable candidate needs a form_factor
    direction, a tool plan, a plain done-when, and a populated sample-
    output rendering (the buildable gate is generated for the chosen
    direction later, by generate_design)."""
    form_factor = str(raw.get("form_factor") or "").strip()
    tool_plan = str(raw.get("tool_plan") or "").strip()
    gate_plain = str(raw.get("gate_plain") or "").strip()
    sample_output = raw.get("sample_output") or {}
    if not form_factor:
        raise GenerationUnavailable(
            "candidate is missing a form_factor direction label")
    if not (tool_plan and gate_plain):
        raise GenerationUnavailable(
            "candidate produced an unusable review surface (no tool plan "
            "or no done-when)")
    if not isinstance(sample_output, dict) or not sample_output:
        raise GenerationUnavailable(
            "candidate is missing a populated sample_output rendering")
    launch_mechanism = str(raw.get("launch_mechanism") or "").strip()
    raw_workflow = raw.get("user_workflow") or []
    if isinstance(raw_workflow, str):
        raw_workflow = [raw_workflow]
    user_workflow = tuple(
        str(s).strip() for s in raw_workflow if str(s).strip())
    return CandidateDesign(
        form_factor=form_factor,
        tool_plan=tool_plan,
        data_shape=str(raw.get("data_shape") or "").strip(),
        gate_plain=gate_plain,
        sample_output={str(k): v for k, v in sample_output.items()},
        launch_mechanism=launch_mechanism,
        user_workflow=user_workflow,
    )


def generate_candidate_designs(
    intent: RequestIntent,
    grounding: GroundingOutcome | None,
    *,
    n: int = 3,
    user_tech_level: str = TECH_LEVEL_NON_TECHNICAL,
    answers: dict[str, str] | None = None,
    model: str = "sonnet",
    llm_json_fn=None,
    timeout: int = CANDIDATES_TIMEOUT_S,
) -> list[CandidateDesign]:
    """Generate N materially-distinct candidate designs (AC.DF.1, AC.DF.6,
    AC.DF.7).

    N bounded dispatches — one per candidate (the §11-sanctioned "N
    dispatches" alternative; D-build.1).  Each call asks for ONE design
    in a rotating direction seed, so a per-candidate JSON is ~half the
    size of the batched N-object response and the model emits it
    reliably (measured 3/3 clean per-candidate vs ~1/3 clean on the
    batched call, where deeply-nested trailing braces on a rich
    sample_output got mis-nested — a model-side structural fragility, NOT
    a recoverable escaping issue).  Each carries a form_factor direction
    label + a polished sample-output rendering (D-2 / SAL-DF-1); the
    heavy buildable gate is generated for the CHOSEN direction only (via
    generate_design) — generating N full gates in one dispatch overruns
    the generation budget (a single N=3 full-gate dispatch timed out at
    the 900s ceiling).  Distinctness across candidates (different
    form_factor) is enforced so AC.DF.1's "materially-distinct" bar is
    not met by N phrasings of one design (SAL-DF-3).  Fewer than 2
    usable, materially-distinct candidates raises
    :class:`GenerationUnavailable` (the design-first stage cannot
    surface a real choice from one design).

    The candidate space is framed for the user's tech level
    (``user_tech_level``), DEFAULTING to a NON-TECHNICAL user (the owner
    ruling + the demo case; AC.DF.6).  For a non-tech user the direction
    seeds are partitioned to see-and-use / sensible-delivery families (no
    CLI / daemon seed), the prompt forbids developer-machinery surfaces,
    AND a held-out structural classifier (``is_nontech_operable``) drops
    any candidate whose primary interaction still reads as a CLI / daemon /
    background-watch surface — so a non-tech user is NEVER surfaced a
    candidate they cannot operate, even if the model ignores the prompt
    constraint.

    Each candidate ALSO carries a ``launch_mechanism`` + a literal
    ``user_workflow`` (AC.DF.7): the concrete steps the target user takes
    to LAUNCH and USE the tool.  For a non-tech user a second held-out
    classifier (``is_launch_user_operable``) drops any candidate whose
    launch requires a terminal / a script run / a dev-env install — so a
    visible GUI whose only way in is "run the script" is rejected (the
    rehearsal-2 failure).  The chosen candidate's launch mechanism +
    workflow are carried into the buildable-design generation (via
    ``as_direction_brief``) so the build TARGETS the form-factor the
    design committed to.

    Each per-candidate dispatch carries a finite parse-retry bound
    (CANDIDATES_PARSE_ATTEMPTS) for the occasional malformed-JSON
    transient — the honest-bound discipline (a bounded best, not
    retry-until-green)."""
    if n < 1:
        raise GenerationUnavailable("n must be >= 1")
    intent_block = intent.inferred_intent
    if answers:
        qa = "; ".join(f"{q} -> {a}" for q, a in answers.items()
                       if str(a).strip())
        if qa:
            intent_block += f"\nClarifications from the user: {qa}"
    g_block, trace_rule = _grounding_block(grounding)
    dispatch = llm_json_fn if llm_json_fn is not None else _claude_json
    seeds = _seeds_for(user_tech_level)
    tech_constraint = _tech_constraint_for(user_tech_level)
    enforce_nontech = user_tech_level != TECH_LEVEL_TECHNICAL

    def _one(direction_seed: str, taken: list[str]) -> CandidateDesign | None:
        avoid_block = ""
        if taken:
            avoid_block = (
                "\nDirections already proposed (make yours materially "
                "DIFFERENT from these): " + "; ".join(taken) + "\n")
        prompt = _CANDIDATE_PROMPT.format(
            direction_seed=direction_seed, avoid_block=avoid_block,
            tech_constraint=tech_constraint,
            intent_block=intent_block, objective=intent.objective,
            grounding_block=g_block)
        last_exc: Exception | None = None
        for _attempt in range(CANDIDATES_PARSE_ATTEMPTS):
            try:
                envelope = dispatch(prompt, model=model, timeout=timeout)
            except Exception as exc:  # noqa: BLE001
                raise GenerationUnavailable(
                    f"candidate-design dispatch failed: {exc}") from exc
            text = str((envelope or {}).get("result") or "").strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:]
                text = text.strip()
            try:
                payload = json.loads(text)
            except (json.JSONDecodeError, ValueError) as exc:
                last_exc = exc
                continue  # bounded re-dispatch on a malformed-JSON transient
            if isinstance(payload, dict):
                return _candidate_from_payload(payload)
            last_exc = ValueError("candidate output not an object")
        # A single candidate's parse never settled within the bound — the
        # caller decides whether the surviving candidates are enough.
        return None

    candidates: list[CandidateDesign] = []
    taken: list[str] = []
    for i in range(n):
        seed = seeds[i % len(seeds)]
        cand = _one(seed, taken)
        if cand is None:
            continue
        # AC.DF.6 — for a non-technical user, drop any candidate whose
        # primary interaction is developer machinery (CLI / daemon /
        # background-watch) even though the prompt forbade it. The
        # held-out classifier is the guarantee the user is NEVER surfaced
        # a candidate they cannot operate; it never saw the generation
        # prompt and is domain-blind.
        if enforce_nontech:
            ok, _why = is_nontech_operable(cand.form_factor, cand.tool_plan)
            if not ok:
                continue
            # AC.DF.7 — for a non-technical user, ALSO drop any candidate
            # whose LAUNCH path requires developer machinery to start
            # (a terminal, a script run, a dev-env install) even though
            # its output is visible. Visible output is necessary but not
            # sufficient; the user must be able to personally launch +
            # use it end-to-end. Held-out, domain-blind, prompt-blind.
            ok_launch, _why_launch = is_launch_user_operable(
                cand.launch_mechanism, cand.user_workflow)
            if not ok_launch:
                continue
        # Skip a candidate that collided with an earlier direction — the
        # distinctness bar is enforced as candidates accrue (SAL-DF-3).
        if cand.form_factor.strip().lower() in {
                c.form_factor.strip().lower() for c in candidates}:
            continue
        candidates.append(cand)
        taken.append(cand.form_factor)

    if n >= 2 and len(candidates) < 2:
        raise GenerationUnavailable(
            "fewer than 2 usable, materially-distinct candidate designs — "
            "the design-first stage needs a real choice, not one design")
    return candidates


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
