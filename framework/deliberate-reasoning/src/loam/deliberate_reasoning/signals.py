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

"""The situation-signal substrate (slice 3 — plan D-SIT.1, D-SIT.2, D-SIT.3).

This module is the v1 STRUCTURAL signal floor that replaces the slice-1
conversation-keyword triggers (``_HEDGE_RE`` over ``draft_text``,
``_STAKES_RE`` over ``prompt_text``). Every detector here classifies the
**pending action's structure** and **recent tool-RESULT history** — never the
natural-language content of the user's prompt or the model's draft (the
D-SIT.3 bright line). It is LLM-free by construction (re / dataclasses /
enum only — no print-client, no anthropic).

The admissible-source contract (D-SIT.3 / AC.TRIG.3) — a detector may read
ONLY:

  1. the pending action's **tool name** (Bash, Write, Edit, a search tool, a
     network/process tool);
  2. the **structure of the tool's arguments** — the regex/quantifier shape,
     the recursion/breadth flags, the presence/absence of a result bound, the
     target path, the target's size/type;
  3. the **recent tool-RESULT history** — action metadata (tool name,
     argument-shape hash, exit/result class) of the last N calls.

It may NOT read:

  - the natural-language content of the user's prompt;
  - the natural-language content of the model's draft answer.

The v1 situation set (plan §3.2 / D-SIT.2), all calibrated to fire on the
2026-06-24 runaway-regex incident:

- ``UNBOUNDED_OP``       — about to run an unbounded / expensive operation.
- ``REPEAT_FAILED``      — repeating an approach that just failed this turn.
- ``MACHINE_IRREVERSIBLE`` — about to act irreversibly on the user's machine.
- ``HIGH_BLAST_RADIUS``  — about to take a high-blast-radius action.

ACs:

- AC.TRIG.1 — escalation driven by situation signals (this module), not by
  conversation keywords.
- AC.TRIG.2 — each v1 signal fires on its positive fixture / declines its
  negative, LLM-free.
- AC.TRIG.3 — the detectors read admissible sources only (the
  :class:`PendingAction` + :class:`ToolResultRing` carry no NL prompt/draft).
- AC.TRIG.4 — the incident shape (unbounded quantifier over a large target +
  a repeated failing call) fires ``UNBOUNDED_OP`` + ``REPEAT_FAILED``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class SituationSignal(str, Enum):
    """The v1 STRUCTURAL signal set (plan §3.2 / D-SIT.2).

    Each member classifies the pending action / behavioral history, never
    the conversation. These are the members the gate's ``Trigger`` enum
    gains in slice 3.
    """

    UNBOUNDED_OP = "unbounded_op"
    REPEAT_FAILED = "repeat_failed"
    MACHINE_IRREVERSIBLE = "machine_irreversible"
    HIGH_BLAST_RADIUS = "high_blast_radius"


# --------------------------------------------------------------------------
# The structural inputs — the pending action + the recent-result ring.
# By construction these carry NO natural-language prompt/draft field; the
# admissible-source contract (D-SIT.3 / AC.TRIG.3) is enforced by the shape
# of these dataclasses, not by a runtime check on free text.
# --------------------------------------------------------------------------


# The exit/result classes a recent tool call can carry (action metadata,
# never conversation). The ring stores only these, never the result text.
class ResultClass(str, Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    FAILURE = "failure"
    TIMEOUT = "timeout"


_FAILED_RESULT_CLASSES = frozenset(
    {ResultClass.FAILURE, ResultClass.EMPTY, ResultClass.TIMEOUT}
)


@dataclass(frozen=True)
class PendingAction:
    """The structural description of the tool call about to run.

    This is the PreToolUse envelope's already-available structural view (the
    same ``tool_name`` + ``tool_input`` the existing guards read). It carries
    the tool name, the argument string(s) whose STRUCTURE the detectors read,
    and the target-path / target-size metadata — and **no** prompt or draft
    natural-language field (D-SIT.3 / AC.TRIG.3).
    """

    # The pending tool's name (Bash, Write, Edit, Grep, a search/network tool).
    tool_name: str = ""
    # The command / pattern string the tool will run (e.g. the Bash command,
    # the search regex). Read for its STRUCTURE (quantifier shape, presence of
    # a bound), never as conversation text.
    command: str = ""
    # The search/match pattern when the tool is a dedicated search tool whose
    # pattern is a distinct argument (e.g. Grep). Read for its quantifier
    # structure. Empty when not a pattern-bearing tool.
    pattern: str = ""
    # The target path the action reads/writes/searches, when present.
    target_path: str = ""
    # The target's size in bytes when known (e.g. a known-large or minified
    # file). 0 / unknown when the harness cannot cheaply size it.
    target_size_bytes: int = 0

    def arg_shape_key(self) -> str:
        """A stable structural key for the action (tool + normalized args).

        Used by REPEAT_FAILED to detect a structurally near-identical retry.
        Whitespace-collapsed so trivial reformatting does not dodge the match;
        carries NO conversation text — only the action's own arguments.
        """

        norm_cmd = re.sub(r"\s+", " ", self.command).strip()
        norm_pat = re.sub(r"\s+", " ", self.pattern).strip()
        return f"{self.tool_name}\x1f{norm_cmd}\x1f{norm_pat}\x1f{self.target_path}"


@dataclass(frozen=True)
class ToolCallRecord:
    """One entry in the recent-tool-result ring — action metadata only."""

    arg_shape_key: str
    result_class: ResultClass


@dataclass(frozen=True)
class ToolResultRing:
    """The recent-tool-RESULT history (the SIT.REPEAT_FAILED substrate).

    A small ordered record of the last N tool calls' action metadata (the
    ``arg_shape_key`` + the ``result_class``). It stores NO conversation text
    and NO result body — only the structural fingerprint + the exit class,
    which is action metadata, never conversation (D-SIT.3).
    """

    records: tuple[ToolCallRecord, ...] = ()

    def last_failed_keys(self) -> frozenset[str]:
        """The arg-shape keys of recent calls that returned a failed class."""
        return frozenset(
            r.arg_shape_key
            for r in self.records
            if r.result_class in _FAILED_RESULT_CLASSES
        )


# --------------------------------------------------------------------------
# The structural detectors. Each reads ONLY the PendingAction / ToolResultRing
# — the admissible sources (D-SIT.3). None reads a prompt or draft.
# --------------------------------------------------------------------------

# An unbounded / backtracking-prone quantifier shape in a search/command
# argument: an open-ended ``.*`` / ``.+`` over an arbitrary span, an explicit
# wide bounded span ``.{0,N}`` / ``.{N,}``, or a nested-quantifier shape. This
# is a pattern over the pending ACTION'S argument (what the command will DO),
# NOT over the conversation (D-SIT.3 / RF-5; owner-confirmed admissible).
_UNBOUNDED_QUANTIFIER_RE = re.compile(
    r"""
    \.\*               # .* — open-ended any-run
  | \.\+               # .+ — open-ended any-run (>=1)
  | \.\{\d*,\}         # .{N,} — open upper bound
  | \.\{\d+,\d+\}      # .{M,N} — wide bounded span
  | (?:[+*]\s*){2,}    # stacked quantifiers (catastrophic-backtracking shape)
    """,
    re.VERBOSE,
)

# Result-bounding tokens that, when present in a command, cap the work and
# REMOVE the unbounded shape (head/limit/timeout/first-N). Their ABSENCE is
# part of the unbounded signal (a command with no bound over a large target).
_RESULT_BOUND_RE = re.compile(
    r"""
    \|\s*head\b        # piped to head
  | \bhead\s+-         # head -N
  | \|\s*sed\s+-n\b    # sed -n line range
  | \btimeout\s+\d     # timeout N
  | \b--max-count\b    # grep --max-count
  | \b-m\s+\d          # grep -m N
  | \bhead_limit\b     # tool-arg head_limit
    """,
    re.VERBOSE,
)

# A "large target" threshold (bytes). A search/command over a target at or
# above this size with an unbounded quantifier and no result bound is the
# UNBOUNDED_OP shape (the 2026-06-24 incident: a 2.1MB single-line minified
# blob). Sizing is structural metadata, never conversation.
_LARGE_TARGET_BYTES = 512 * 1024

# Mutating / external tool names whose effect is non-trivially reversible:
# writes, deletes, moves, network sends, process spawns. Detection is over the
# tool TYPE + target PATH (D-SIT.3), mirroring wd_discipline_guard.
_MUTATING_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})

# Bash sub-commands that mutate / spawn irreversibly. Read from the command's
# leading verb structure, not from conversation.
_BASH_MUTATING_RE = re.compile(
    r"""
    \b(?:rm|mv|cp|dd|mkfs|chmod|chown|truncate|shred)\b
  | \b(?:curl|wget|scp|rsync|ssh)\b      # network send
  | (?:^|[\s;&|])(?:nohup|&\s*$)         # background process spawn
  | \bkill(?:all)?\b
    """,
    re.VERBOSE | re.MULTILINE,
)

# The safe scratch / tmp target set — actions whose target is confined here
# are NOT machine-irreversible (mirrors the existing guards' exempt set).
_SAFE_TARGET_PREFIXES = (
    "/tmp/",
    "/var/tmp/",
    ".scratch/",
    "/private/tmp/",
)

# Bulk / recursive breadth structure — a wide blast radius. Recursive
# delete/find-exec, recursive flags, glob-everything. Over the command's
# recursion structure, not conversation.
_HIGH_BLAST_RE = re.compile(
    r"""
    \brm\s+-[a-z]*r[a-z]*f?\b    # rm -rf / -fr / -r
  | \brm\s+-[a-z]*f[a-z]*r\b     # rm -fr permutation
  | \bfind\b[^\n]*\s-exec\b      # find ... -exec (bulk apply)
  | \bgit\s+clean\s+-[a-z]*f     # git clean -fd
  | --recursive\b
  | \s-R\b                       # -R recursive flag
  | /\*\s*$                      # trailing /* glob over a dir
    """,
    re.VERBOSE,
)

# Sealed / load-bearing path fragments — an action against these is
# high-blast-radius regardless of breadth (target sensitivity, D-SIT.2).
_SENSITIVE_PATH_FRAGMENTS = (
    "/seals/",
    "SEAL_COMMIT",
    "test_no_sealed_amendments",
    ".claude/settings.json",
    "/.git/",
)


def _has_unbounded_quantifier(action: PendingAction) -> bool:
    blob = f"{action.command}\n{action.pattern}"
    return _UNBOUNDED_QUANTIFIER_RE.search(blob) is not None


def _has_result_bound(action: PendingAction) -> bool:
    return _RESULT_BOUND_RE.search(action.command) is not None


def detect_unbounded_op(action: PendingAction) -> bool:
    """SIT.UNBOUNDED_OP — the pending action's STRUCTURE is unbounded.

    Fires when the pending command/search carries an unbounded/backtracking
    quantifier AND lacks a result bound, OR runs an unbounded quantifier over
    a known-large target. Reads only the pending action's argument structure
    and target size (D-SIT.3). Calibrated to fire on the 2026-06-24 incident:
    an unbounded quantifier over a 2.1MB single-line file (AC.TRIG.4).
    """

    if not _has_unbounded_quantifier(action):
        return False
    if _has_result_bound(action):
        # A bounded command (piped to head, timeout, --max-count) is capped.
        return False
    over_large_target = action.target_size_bytes >= _LARGE_TARGET_BYTES
    # Unbounded quantifier with no bound is the signal; a large target makes
    # it unambiguous, but an unbounded backtracking shape with no bound at all
    # is itself the structural risk (catastrophic backtracking is size-
    # independent for adversarial input). Both fire.
    return True or over_large_target  # noqa: SIM103 — explicit for the reader


def detect_repeat_failed(action: PendingAction, ring: ToolResultRing) -> bool:
    """SIT.REPEAT_FAILED — the pending action repeats a just-failed approach.

    Fires when the pending action's structural key matches a recent call in
    the ring that returned a failure/empty/timeout class. Reads only the
    action's arg-shape key + the ring's result metadata (D-SIT.3) — never the
    conversation. Calibrated to fire on the incident's repeated failing
    search (AC.TRIG.4).
    """

    return action.arg_shape_key() in ring.last_failed_keys()


def _target_is_safe(target_path: str) -> bool:
    if not target_path:
        return False
    return any(
        target_path.startswith(p) or f"/{p}" in target_path
        for p in _SAFE_TARGET_PREFIXES
    )


def detect_machine_irreversible(action: PendingAction) -> bool:
    """SIT.MACHINE_IRREVERSIBLE — about to act irreversibly on the machine.

    Fires when the pending action is a mutating/external/process-spawning
    action whose target is OUTSIDE the safe scratch/tmp set. Reads the tool
    TYPE + target PATH + the command's mutating-verb structure (D-SIT.3) —
    the same classification wd_discipline_guard / in_thread_work_budget_guard
    already perform.
    """

    if action.tool_name in _MUTATING_TOOLS:
        return not _target_is_safe(action.target_path)
    if action.tool_name == "Bash" and _BASH_MUTATING_RE.search(action.command):
        return not _target_is_safe(action.target_path)
    return False


def detect_high_blast_radius(action: PendingAction) -> bool:
    """SIT.HIGH_BLAST_RADIUS — about to take a high-blast-radius action.

    Fires when the pending action's STRUCTURE implies wide effect: a
    bulk/recursive mutation (rm -rf, recursive find-exec, recursive flags) OR
    an action against a sealed/load-bearing path. Reads the command's
    recursion/breadth structure + the target sensitivity (D-SIT.3).
    """

    if _HIGH_BLAST_RE.search(action.command):
        return True
    haystack = f"{action.command} {action.target_path}"
    return any(frag in haystack for frag in _SENSITIVE_PATH_FRAGMENTS)


# The detector table — order fixes the reported signal order so the recorded
# signal list is deterministic (mirrors gate.py's _DETECTORS pattern).
_SITUATION_DETECTORS: Sequence[
    tuple[SituationSignal, "callable"]
] = (
    (SituationSignal.UNBOUNDED_OP, lambda a, r: detect_unbounded_op(a)),
    (SituationSignal.REPEAT_FAILED, lambda a, r: detect_repeat_failed(a, r)),
    (SituationSignal.MACHINE_IRREVERSIBLE, lambda a, r: detect_machine_irreversible(a)),
    (SituationSignal.HIGH_BLAST_RADIUS, lambda a, r: detect_high_blast_radius(a)),
)


def detect_situation_signals(
    action: PendingAction | None,
    ring: ToolResultRing | None = None,
) -> tuple[SituationSignal, ...]:
    """Run every v1 structural detector; return the fired signals in order.

    LLM-free, deterministic, instant. A turn with no pending action (or a
    structurally-safe one) yields the empty tuple — the zero-collateral floor
    (AC.WIRE.2 / AC.TRIG.1). Reads only the admissible structural inputs; no
    detector receives a prompt or draft (AC.TRIG.3).
    """

    if action is None:
        return ()
    r = ring or ToolResultRing()
    return tuple(
        sig for sig, detect in _SITUATION_DETECTORS if detect(action, r)
    )
