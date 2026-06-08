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

"""SubagentStop out-of-band frame-consistency judge (loam-realignment 1b,
AC.SSFC.*).

The OUT-side guarantee that pairs with 1a's IN-handoff. When a
CONSEQUENTIAL dispatched subagent FINISHES (it wrote a deliverable /
mutated state — a STRUCTURAL cue read off its transcript), this module
evaluates the subagent's result OUT-OF-BAND: a fresh evaluation seeded
with ONLY the microkernel (``kernel/loam-microkernel.md``) + the
subagent's stated objective + its result — explicitly NOT the polluted
parent conversation — judging frame-consistency. The judge runs as an
ISOLATED subscription ``claude -p`` via the SEALED
``spawn_isolated_claude`` entry-point (no Anthropic API key; spawn
-isolation MANDATORY). Off-frame -> a non-blocking flag SURFACES to the
dispatcher; on-frame -> a silent no-op. Every path is FAIL-SOFT: a judge
error never aborts, never blocks a subagent's return.

This is component J from the integrated design instantiated at the
persona->subagent FINISH boundary. The hook (``subagent_stop_frame_check
.py``) stays thin (envelope read -> delegate -> emit); this module
carries the logic — mirrors 1a's hook/``bundle.py`` split.

Per ODD §2.5 every branch below traces to a named AC:

  * the structural-cue trigger predicate (:func:`is_consequential`) ->
    AC.SSFC.1;
  * the fresh-context seed assembly (:func:`assemble_seed`) ->
    AC.SSFC.2 (microkernel + objective + result ONLY; parent
    conversation EXCLUDED);
  * the isolated-``claude -p`` judge call (:func:`run_judge` via
    ``spawn_isolated_claude``) -> AC.SSFC.3;
  * the off-frame surface render (:func:`render_surface`) -> AC.SSFC.4
    (off-frame surfaces, on-frame silent);
  * every ``except`` / degraded return -> AC.SSFC.5 (fail-soft, never
    aborts/blocks).

Reuses 1a's ``bundle._read_microkernel`` microkernel-render path read
-only (D-SSFC.5 / Lens 1) — the same TCB the SubagentStart hook injects,
license boilerplate stripped. Composes on the SEALED
``loam_spawn_isolation.spawn_isolated_claude`` entry-point — never a
hand-rolled ``subprocess.run(["claude",...])`` (the PROVEN Telegram-drop
kill vector; ``feedback_spawned_claude_must_isolate_telegram_plugin``).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Reuse 1a's microkernel-render path read-only (D-SSFC.5 / Lens 1): the
# SAME TCB the SubagentStart hook injects, with the license/comment
# boilerplate stripped. We do NOT re-author the read.
from loam.frame_kernel.bundle import (
    MICROKERNEL_PRIME_MARKER,
    MISSING_KERNEL_MARKER,
    _read_microkernel,
)


# ---------------------------------------------------------------------
# Markers + verdict tokens
# ---------------------------------------------------------------------

# The seed delimiters. The judge prompt is assembled FRESH from exactly
# these three blocks (AC.SSFC.2): microkernel + stated objective +
# result. The parent conversation is NEVER a block here — that is the
# load-bearing fresh-context guarantee (D-SSFC.5).
SEED_OBJECTIVE_MARKER = "=== subagent stated objective ==="
SEED_RESULT_MARKER = "=== subagent result ==="

# The verdict tokens the judge is instructed to emit (last line of its
# output). Parsed leniently (AC.SSFC.5: a malformed verdict fails soft).
VERDICT_ON_FRAME = "ON_FRAME"
VERDICT_OFF_FRAME = "OFF_FRAME"

# The non-blocking surface marker (AC.SSFC.4). Off-frame emits this in a
# ``systemMessage`` to the dispatcher; on-frame emits nothing.
OFF_FRAME_SURFACE_MARKER = "[frame-check] OFF-FRAME subagent result flagged"

# Fail-soft seed/objective markers (AC.SSFC.5 named degraded modes).
SEED_OBJECTIVE_MISSING_MARKER = "[no recoverable stated objective]"
SEED_RESULT_MISSING_MARKER = "[no recoverable subagent result]"

SUBAGENT_STOP_EVENT = "SubagentStop"

# The structural cues that mark a CONSEQUENTIAL subagent (D-SSFC.3 /
# AC.SSFC.1): tool uses that WROTE a deliverable or MUTATED state. The
# SHAPE is pinned (wrote-deliverable / mutated-state); the exact list is
# the build-time-empirical knob (plan §6-Q1 / RF-5) — tunable without
# re-opening the AC, which asserts the GATE BEHAVIOR not the list.
_WRITE_TOOL_NAMES = frozenset(
    {"Write", "Edit", "MultiEdit", "NotebookEdit"}
)
# Bash is consequential only when it mutates; a read-only Bash (ls/cat/
# grep) is NOT a cue. We treat any Bash tool use as a potential mutation
# cue unless its command is recognizably read-only — erring toward NOT
# firing keeps the judge cheap (RF-5: too-broad gets disabled).
_BASH_TOOL_NAMES = frozenset({"Bash"})
_READ_ONLY_BASH_RE = re.compile(
    r"^\s*(ls|cat|head|tail|grep|rg|find|pwd|echo|git\s+(status|log|diff|show|"
    r"branch|rev-parse)|wc|sort|uniq|which|file|stat|du|df)\b"
)


# ---------------------------------------------------------------------
# Transcript parsing (D-SSFC.5 seed sources; AC.SSFC.1 cue)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SubagentResult:
    """What the judge path reads off a finished subagent's transcript.

    ``objective`` is the subagent's STATED objective (its dispatch task
    text, recovered from the transcript head / the SubagentStop
    envelope). ``result`` is its final output (recovered from the
    transcript tail). ``consequential`` is the structural-cue verdict
    (AC.SSFC.1). ``workspace_root`` seeds the kernel-path resolution.
    Any field may be empty/degraded — the caller degrades each path
    independently (AC.SSFC.5).
    """

    objective: str
    result: str
    consequential: bool
    workspace_root: Path | None


def _block_text(content: Any) -> str:
    """Flatten a message ``content`` (str or list-of-blocks) to text.

    Reads the documented transcript message shapes: a plain-string
    content, or a list of typed blocks where ``{"type":"text"}`` blocks
    carry the prose. Tool-use blocks contribute nothing to the prose
    extraction (they are the AC.SSFC.1 cue source, handled separately).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def _iter_tool_uses(content: Any) -> list[dict[str, Any]]:
    """Return the ``tool_use`` blocks in a message ``content`` list."""
    if not isinstance(content, list):
        return []
    return [
        b
        for b in content
        if isinstance(b, dict) and b.get("type") == "tool_use"
    ]


def _bash_is_mutation(tool_input: Any) -> bool:
    """A Bash tool use is a mutation cue unless it is recognizably
    read-only (AC.SSFC.1 — wrote-deliverable / mutated-state SHAPE).

    Conservative: an UN-recognized command is treated as a potential
    mutation (it could be ``rm`` / ``mv`` / ``loam amend`` / a build).
    A recognized read-only prefix (ls/cat/grep/git-status/...) is NOT a
    cue. Tuning the recognizer is the build-time knob (RF-5).
    """
    if not isinstance(tool_input, dict):
        return True
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return True
    return _READ_ONLY_BASH_RE.match(command) is None


def _is_consequential_tool_use(block: dict[str, Any]) -> bool:
    """Does a single ``tool_use`` block mark a consequential action?"""
    name = block.get("name")
    if not isinstance(name, str):
        return False
    if name in _WRITE_TOOL_NAMES:
        return True
    if name in _BASH_TOOL_NAMES:
        return _bash_is_mutation(block.get("input"))
    return False


def _load_transcript_records(transcript_path: Path | None) -> list[Any]:
    """Load a JSONL transcript into a list of records, fail-soft.

    The SubagentStop ``transcript_path`` common-input field points at the
    finished subagent's transcript (official hook-development SKILL).
    Reads the documented JSONL shape (one JSON object per line); a
    missing / unreadable / non-JSONL file yields ``[]`` so the caller
    degrades rather than raises (AC.SSFC.5 / plan §8 trigger #1's
    readable-result residual).
    """
    if transcript_path is None or not transcript_path.exists():
        return []
    try:
        raw = transcript_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    records: list[Any] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _record_message(record: Any) -> tuple[str, Any]:
    """Return ``(role, content)`` for a transcript record, else ("", None).

    Tolerant of the real transcript shape ``{"type": "user"/"assistant",
    "message": {"role": ..., "content": ...}}`` AND a flatter
    ``{"role": ..., "content": ...}`` shape, so the parser does not rest
    on one exact flavor (the SubagentStop transcript flavor in the
    running version is the AC.SSFC.S residual).
    """
    if not isinstance(record, dict):
        return "", None
    message = record.get("message")
    if isinstance(message, dict) and "content" in message:
        role = message.get("role") or record.get("type") or ""
        return (role if isinstance(role, str) else ""), message.get("content")
    if "content" in record:
        role = record.get("role") or record.get("type") or ""
        return (role if isinstance(role, str) else ""), record.get("content")
    return "", None


def is_consequential(records: list[Any]) -> bool:
    """AC.SSFC.1 — did the subagent do something CONSEQUENTIAL?

    Scans the transcript for a structural cue: a Write/Edit/MultiEdit/
    NotebookEdit tool use, or a mutating Bash tool use. Returns False
    for a trivial read-only finish (no cue) -> the judge is NOT spawned
    (the gate keeps the check cheap + bounded — D-SSFC.3 / RF-5). The
    predicate is deterministic (read off the transcript), never a
    semantic judgment by the possibly-drifted pass (integrated-design
    §2-J: structural cues, not semantic).
    """
    for record in records:
        _role, content = _record_message(record)
        for block in _iter_tool_uses(content):
            if _is_consequential_tool_use(block):
                return True
    return False


def _extract_objective(records: list[Any], envelope_objective: str) -> str:
    """The subagent's STATED objective (AC.SSFC.2 seed source).

    Prefers an explicit objective from the SubagentStop envelope (the
    dispatch text, when the running version carries it); else recovers
    it from the transcript HEAD — the first real user message's text
    (the dispatch brief). Skips the local-command-caveat preamble Claude
    Code injects. Returns the missing-marker when neither carries it
    (plan §8 trigger #4's named degraded mode — do NOT invent an
    objective).
    """
    if envelope_objective.strip():
        return envelope_objective.strip()
    for record in records:
        role, content = _record_message(record)
        if role != "user":
            continue
        text = _block_text(content).strip()
        if not text:
            continue
        # Skip the local-command caveat preamble Claude Code injects as
        # a synthetic user message — it is not the dispatch objective.
        if text.startswith("<local-command") or "Caveat:" in text[:80]:
            continue
        return text
    return SEED_OBJECTIVE_MISSING_MARKER


def _extract_result(records: list[Any], envelope_result: str) -> str:
    """The subagent's RESULT (AC.SSFC.2 seed source).

    Prefers an explicit result from the SubagentStop envelope (when the
    running version carries one); else recovers it from the transcript
    TAIL — the last assistant message's text (the subagent's final
    output). Returns the missing-marker when neither carries it
    (AC.SSFC.5 degraded mode).
    """
    if envelope_result.strip():
        return envelope_result.strip()
    for record in reversed(records):
        role, content = _record_message(record)
        if role != "assistant":
            continue
        text = _block_text(content).strip()
        if text:
            return text
    return SEED_RESULT_MISSING_MARKER


# ---------------------------------------------------------------------
# Envelope parsing (the SubagentStop input contract)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class StopContext:
    """The fields read off a SubagentStop envelope.

    ``transcript_path`` is the common-input field pointing at the
    finished subagent's transcript (official hook contract).
    ``workspace_root`` seeds the kernel-path resolution.
    ``envelope_objective`` / ``envelope_result`` capture an objective/
    result the envelope itself carries (some versions may), preferred
    over transcript recovery. ``subagent_id`` names the subagent in the
    surface (AC.SSFC.4). Any field may be empty (AC.SSFC.5).
    """

    transcript_path: Path | None
    workspace_root: Path | None
    envelope_objective: str
    envelope_result: str
    subagent_id: str


def parse_stop_envelope(envelope: Any) -> StopContext:
    """Extract the SubagentStop context, fail-soft (AC.SSFC.5).

    A malformed / empty / non-dict envelope yields an all-empty
    :class:`StopContext` rather than raising.
    """
    if not isinstance(envelope, dict):
        return StopContext(
            transcript_path=None,
            workspace_root=None,
            envelope_objective="",
            envelope_result="",
            subagent_id="",
        )

    transcript_path: Path | None = None
    tp = envelope.get("transcript_path")
    if isinstance(tp, str) and tp.strip():
        transcript_path = Path(tp)

    workspace_root: Path | None = None
    workspace = envelope.get("workspace")
    if isinstance(workspace, dict):
        root_str = workspace.get("project_dir")
        if isinstance(root_str, str) and root_str.strip():
            workspace_root = Path(root_str)
    if workspace_root is None:
        # The common-input ``cwd`` field is the fallback workspace root.
        cwd = envelope.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            workspace_root = Path(cwd)

    # Some versions may carry the objective/result on the envelope. Read
    # the documented + plausible fields; absence falls back to the
    # transcript recovery (never invented).
    envelope_objective = ""
    for key in ("objective", "prompt", "task", "description"):
        value = envelope.get(key)
        if isinstance(value, str) and value.strip():
            envelope_objective = value.strip()
            break
    envelope_result = ""
    for key in ("result", "output", "last_assistant_message"):
        value = envelope.get(key)
        if isinstance(value, str) and value.strip():
            envelope_result = value.strip()
            break

    subagent_id = ""
    for key in ("subagent_id", "agent_id", "session_id"):
        value = envelope.get(key)
        if isinstance(value, str) and value.strip():
            subagent_id = value.strip()
            break

    return StopContext(
        transcript_path=transcript_path,
        workspace_root=workspace_root,
        envelope_objective=envelope_objective,
        envelope_result=envelope_result,
        subagent_id=subagent_id,
    )


def read_subagent_result(ctx: StopContext) -> SubagentResult:
    """Read the finished subagent's objective + result + cue (AC.SSFC.1/2).

    Loads the transcript, computes the structural-cue verdict, and
    recovers the stated objective + result. Fail-soft throughout: an
    unreadable/absent transcript yields ``consequential=False`` + missing
    -markers, so a degenerate SubagentStop payload degrades rather than
    aborts (AC.SSFC.5 / plan §8 trigger #1).
    """
    records = _load_transcript_records(ctx.transcript_path)
    return SubagentResult(
        objective=_extract_objective(records, ctx.envelope_objective),
        result=_extract_result(records, ctx.envelope_result),
        consequential=is_consequential(records),
        workspace_root=ctx.workspace_root,
    )


# ---------------------------------------------------------------------
# Fresh-context seed assembly (AC.SSFC.2 / D-SSFC.5)
# ---------------------------------------------------------------------


def assemble_seed(result: SubagentResult) -> str:
    """Assemble the FRESH judge seed: microkernel + objective + result
    ONLY (AC.SSFC.2 / D-SSFC.5).

    The seed contains exactly three blocks — the verbatim microkernel
    (reusing 1a's ``_read_microkernel`` render path; the SAME TCB),
    the subagent's stated objective, and its result. The parent
    conversation is NEVER assembled here: that is the load-bearing
    fresh-context guarantee (integrated-design §1 — the check must run
    in a frame the polluted conversation cannot reach). The judge
    COMPARES the result against the core; it does not ask the doer "did
    you consider the core?" (integrated-design §8).
    """
    microkernel = _read_microkernel(result.workspace_root)
    blocks = [
        MICROKERNEL_PRIME_MARKER,
        "",
        microkernel,
        "",
        SEED_OBJECTIVE_MARKER,
        "",
        result.objective or SEED_OBJECTIVE_MISSING_MARKER,
        "",
        SEED_RESULT_MARKER,
        "",
        result.result or SEED_RESULT_MISSING_MARKER,
    ]
    return "\n".join(blocks)


def build_judge_prompt(seed: str) -> str:
    """Wrap the fresh seed in the judge instruction.

    The judge is asked to compare the RESULT against the microkernel +
    the stated objective (NOT to ask the doer anything), and to emit a
    final-line verdict token (:data:`VERDICT_ON_FRAME` /
    :data:`VERDICT_OFF_FRAME`) + a one-line reason. The instruction is
    appended to the fresh seed; no parent-conversation content is added.
    """
    return (
        "You are an out-of-band frame-consistency judge. Below is the loam "
        "microkernel (the core), a subagent's STATED OBJECTIVE, and the "
        "subagent's RESULT. You do NOT see the conversation that produced "
        "the result. Judge ONLY whether the RESULT is consistent with the "
        "core AND addresses the stated objective that was actually "
        "requested. Do not ask whether the author considered the core — "
        "judge the result itself.\n\n"
        f"{seed}\n\n"
        "Respond with a one-line reason, then a FINAL line that is exactly "
        f"one of: {VERDICT_ON_FRAME} or {VERDICT_OFF_FRAME}."
    )


# ---------------------------------------------------------------------
# Isolated judge spawn (AC.SSFC.3 / D-SSFC.2) — via the SEALED surface
# ---------------------------------------------------------------------

# Resolve the SEALED spawn-isolation surface (Lens 1: compose, never
# hand-roll). The package is a sibling tool tree; put its src on path
# the same one-line way the surface's own docstring documents for an
# out-of-tree caller. The import is wrapped at the call site so a
# packaging gap degrades fail-soft (AC.SSFC.5) rather than aborting.
_SPAWN_ISOLATION_SRC = (
    Path(__file__).resolve().parents[5]
    / "framework"
    / "tools"
    / "loam-spawn-isolation"
    / "src"
)
if _SPAWN_ISOLATION_SRC.is_dir() and str(_SPAWN_ISOLATION_SRC) not in sys.path:
    sys.path.insert(0, str(_SPAWN_ISOLATION_SRC))


# Default judge model is Sonnet (no model-rationale line needed per Lens
# 5). Short timeout keeps the check bounded (D-SSFC.3).
_JUDGE_MODEL = "sonnet"
_JUDGE_TIMEOUT_S = 90


def build_judge_argv(prompt: str, *, model: str = _JUDGE_MODEL) -> list[str]:
    """The base ``claude -p`` argv the judge runs (PRE-isolation).

    This is the caller's own ``-p``/json shape; the SEALED
    ``spawn_isolated_claude`` injects the empty-strict-MCP isolation +
    scrubbed env around it (AC.SSFC.3). NEVER spawned bare — see
    :func:`run_judge`.
    """
    return [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
    ]


def run_judge(
    prompt: str,
    *,
    model: str = _JUDGE_MODEL,
    timeout: int = _JUDGE_TIMEOUT_S,
) -> str | None:
    """Run the judge as an ISOLATED subscription ``claude -p`` (AC.SSFC.3
    / D-SSFC.2).

    Goes through the SEALED ``spawn_isolated_claude`` entry-point — which
    injects ``--strict-mcp-config`` + an empty ``--mcp-config`` (no
    plugin load -> no Telegram-bot-slot theft), scrubs the bot-token +
    ``ANTHROPIC_API_KEY`` (subscription-only; ``feedback_no_anthropic_
    api_key``), and sets ``CLAUDE_PERSONA`` belt-and-braces. NEVER a
    hand-rolled ``subprocess.run(["claude",...])`` (the PROVEN
    Telegram-drop kill vector).

    Fail-soft (AC.SSFC.5): a missing spawn surface, a spawn failure, a
    timeout, or a non-zero exit returns ``None`` (the caller treats a
    ``None`` verdict as on-frame-degraded — never blocks the return).
    Returns the raw judge stdout on success.
    """
    try:
        from loam_spawn_isolation import spawn_isolated_claude
    except Exception:  # noqa: BLE001 — packaging gap is fail-soft (AC.SSFC.5)
        return None

    argv = build_judge_argv(prompt, model=model)
    try:
        proc = spawn_isolated_claude(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception:  # noqa: BLE001 — spawn/timeout is fail-soft (AC.SSFC.5)
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    stdout = getattr(proc, "stdout", None)
    if not isinstance(stdout, str) or not stdout.strip():
        return None
    return stdout


# ---------------------------------------------------------------------
# Verdict parse + surface render (AC.SSFC.4 / AC.SSFC.5)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """A parsed judge verdict. ``off_frame`` is the surface trigger
    (AC.SSFC.4); ``reason`` is the judge's one-line reason; ``parsed``
    is False when the raw output could not be parsed (AC.SSFC.5 — a
    malformed verdict fails soft to NOT off-frame, never a false block)."""

    off_frame: bool
    reason: str
    parsed: bool


def parse_verdict(raw: str | None) -> Verdict:
    """Parse the judge's raw output into a :class:`Verdict` (AC.SSFC.5).

    ``claude -p --output-format json`` wraps the model text in a JSON
    envelope; we read the ``result`` field if present, else treat the
    whole string as the text. The verdict token is the last recognizable
    ``ON_FRAME``/``OFF_FRAME`` in the text. A ``None`` / empty /
    unparseable output yields ``off_frame=False, parsed=False`` — fail
    -soft to NOT-off-frame so a judge malfunction never manufactures a
    false off-frame surface (AC.SSFC.5).
    """
    if not raw or not raw.strip():
        return Verdict(off_frame=False, reason="", parsed=False)

    text = raw.strip()
    # Unwrap the claude -p JSON envelope when present.
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            inner = payload.get("result")
            if isinstance(inner, str) and inner.strip():
                text = inner.strip()
    except json.JSONDecodeError:
        pass

    has_off = VERDICT_OFF_FRAME in text
    has_on = VERDICT_ON_FRAME in text
    if not has_off and not has_on:
        # No recognizable verdict token — fail soft to NOT off-frame.
        return Verdict(off_frame=False, reason=_first_reason_line(text), parsed=False)

    # If both appear (e.g. the instruction echoed), the LAST occurrence
    # wins — that is the judge's final-line verdict.
    off_at = text.rfind(VERDICT_OFF_FRAME)
    on_at = text.rfind(VERDICT_ON_FRAME)
    off_frame = off_at > on_at
    return Verdict(
        off_frame=off_frame,
        reason=_first_reason_line(text),
        parsed=True,
    )


def _first_reason_line(text: str) -> str:
    """The first non-empty, non-verdict-token line — the judge's reason."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line in (VERDICT_ON_FRAME, VERDICT_OFF_FRAME):
            continue
        return line
    return ""


def render_surface(verdict: Verdict, ctx: StopContext) -> dict[str, Any] | None:
    """Render the dispatcher surface for an off-frame verdict (AC.SSFC.4).

    Off-frame -> a NON-BLOCKING ``systemMessage`` naming the subagent +
    the inconsistency + the judge's reason (D-SSFC.4: surface, never
    silently pass; never a hard block for v1). On-frame (or an
    unparsed/degraded verdict) -> ``None`` (a silent no-op). The shape is
    a ``hookSpecificOutput`` envelope with a ``systemMessage`` — the
    documented non-blocking surface, NOT a ``decision: block``.
    """
    if not verdict.off_frame:
        return None
    subagent = ctx.subagent_id or "(unidentified subagent)"
    reason = verdict.reason or "(no reason given)"
    message = (
        f"{OFF_FRAME_SURFACE_MARKER}: subagent {subagent} returned an "
        f"off-frame result. Judge reason: {reason}. This is a non-blocking "
        f"flag — the subagent's return is NOT blocked; re-aim if warranted."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": SUBAGENT_STOP_EVENT,
            "systemMessage": message,
        }
    }


# ---------------------------------------------------------------------
# Top-level evaluation (the hook's single delegate; AC.SSFC.1..5)
# ---------------------------------------------------------------------


def evaluate(
    envelope: Any,
    *,
    _run_judge: Any = None,
) -> dict[str, Any] | None:
    """Evaluate a finished subagent OUT-OF-BAND; return a non-blocking
    surface dict for an off-frame result, else ``None`` (AC.SSFC.1..5).

    The single entry the thin hook delegates to. Steps:

      1. parse the SubagentStop envelope (fail-soft);
      2. read the subagent's objective + result + structural cue;
      3. GATE on the cue — a trivial (read-only) finish returns ``None``
         WITHOUT spawning the judge (AC.SSFC.1 / D-SSFC.3);
      4. assemble the FRESH seed (microkernel + objective + result
         ONLY — AC.SSFC.2);
      5. run the ISOLATED judge (AC.SSFC.3);
      6. parse the verdict; off-frame -> a non-blocking surface, on
         -frame/degraded -> ``None`` (AC.SSFC.4).

    Every path is fail-soft (AC.SSFC.5): any internal error returns
    ``None`` (no surface, no block) so the subagent's return is never
    aborted. ``_run_judge`` is injectable for the test surface (the
    AC.SSFC.S probe exercises the REAL seed + REAL argv construction and
    may stub only the model-verdict leg at this boundary — the 1a
    AC.SACH.S posture).
    """
    # Resolve the judge at CALL time (not bound as a default) so a
    # monkeypatch of ``run_judge`` reaches the real entry-point; tests
    # inject ``_run_judge`` directly (the AC.SSFC.S stub-at-spawn-boundary
    # posture).
    judge = _run_judge if _run_judge is not None else run_judge
    try:
        ctx = parse_stop_envelope(envelope)
        result = read_subagent_result(ctx)

        # AC.SSFC.1 — the structural-cue gate. A trivial read-only finish
        # has no cue: do NOT spawn the judge.
        if not result.consequential:
            return None

        seed = assemble_seed(result)
        prompt = build_judge_prompt(seed)
        raw = judge(prompt)
        verdict = parse_verdict(raw)
        return render_surface(verdict, ctx)
    except Exception:  # noqa: BLE001 — fail-soft per AC.SSFC.5
        return None
