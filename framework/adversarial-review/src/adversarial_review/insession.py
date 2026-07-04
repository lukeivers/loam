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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""In-session backend — run the review with the CALLER's fresh-context legs.

Why this exists (the failure this fixes): the default critic leg is a
nested ``claude -p`` subprocess (spawn.py). Empirically that subprocess
RETURNS FINE when the review is driven from a background/dispatched agent
(the calibration ran it twice — 158s, 197s), but HANGS when driven from
inside an INTERACTIVE Claude Code session — the single most common way
the ``/adversarial-review`` skill invokes it. The hang is an
interactive-session contention (single-flight / interactive-slot), NOT a
stdin bug and NOT universal: a nested ``claude -p <prompt>`` was probed
returning rc=0 with inherited stdin, an open-pipe stdin, and DEVNULL
stdin. So the robust fix ROUTES AROUND the nested subprocess for the
in-session path rather than trying to make an unreproducible contention
reliable.

The mechanism is the ``model_fn`` seam that already threads end-to-end
(run_standard_review -> run_critic -> ``call = model_fn or
run_isolated_critic``). This module supplies a model leg backed by
responses the CALLER captured from FRESH ISOLATED CONTEXTS (loam Task
subagents), NOT the caller's own context.

THE LOAD-BEARING ISOLATION CONSTRAINT (do not weaken): the caller — an
in-session agent — has ALREADY read the artifact to invoke the review.
Using that single polluted context as the critic would make the DERIVE
phase NOT artifact-blind and silently defeat AC.AR.2/AC.AR.3. So every
model leg MUST be a FRESH context: the agent dispatches a NEW subagent
per phase. The DERIVE prompt this module emits is structurally
artifact-blind (it is the same ``derive_prompt`` the pipeline builds —
objective + methodology + protocol only, artifact ABSENT); the DIFF
prompt reveals the artifact only AFTER the derivation is fixed. The
stepwise handshake below is what enforces "fresh context per phase" at
the orchestration boundary.

The stepwise handshake (STANDARD tier — the floor / common in-session
case), driven by the ``/adversarial-review`` SKILL:

  1. ``insession derive`` -> emits the artifact-blind DERIVE prompt.
     The agent dispatches a FRESH subagent with it -> captures the
     derived correct-artifact spec.
  2. ``insession diff``   -> emits the DIFF prompt (derivation +
     artifact). The agent dispatches ANOTHER FRESH subagent -> captures
     the raw findings.
  3. ``insession finalize`` -> replays the two captured responses through
     the REAL pipeline (parse -> generic-lint -> ground-truth validation
     -> verdict -> render). NO nested subprocess is touched.

Per ODD §2.5: :func:`replay_model_fn` -> the injected-leg backend (the
route-around); :func:`run_insession_standard` -> a real review from
caller-supplied legs (AC.AR.1 via the injected seam, AC.AR.3 preserved).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .critic import derive_prompt, diff_prompt
from .manual import render_report, review_text
from .pipeline import DEFAULT_PROTOCOL, ReviewResult, build_inputs
from .seed import ReviewInputs


class ReplayExhausted(RuntimeError):
    """Raised when the pipeline requests more model legs than were supplied.

    A STANDARD review makes exactly two model calls (derive, then diff).
    If the pipeline asks for a third the caller under-supplied responses —
    this raises loudly rather than returning ``None`` (which the pipeline
    would read as "model unavailable" -> a false REVIEW-INCONCLUSIVE that
    hides the real caller error).
    """


def replay_model_fn(responses: Sequence[Optional[str]]):
    """A ``model_fn`` that returns caller-captured responses in call order.

    THE in-session backend: the caller (an in-session agent) captures each
    critic phase's output from a FRESH isolated subagent and hands the
    ordered list here. The returned callable feeds them to the pipeline in
    the exact order the pipeline makes its model calls — derive first,
    then diff (then, for DEEP, each axis's derive/diff pair in sequence).

    A ``None`` element models a genuinely-unavailable leg (the pipeline
    renders REVIEW-INCONCLUSIVE for that pass, never a false clean bill).
    Requesting MORE legs than supplied raises :class:`ReplayExhausted`.
    """
    remaining = list(responses)

    def _leg(_prompt: str) -> Optional[str]:
        if not remaining:
            raise ReplayExhausted(
                "the review requested more model legs than the caller "
                "supplied — capture one fresh-subagent response per critic "
                "phase (STANDARD = 2: derive, diff)."
            )
        return remaining.pop(0)

    return _leg


def _inputs(
    artifact: str,
    objective: str,
    *,
    domain: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> ReviewInputs:
    inputs, _domain, _stale = build_inputs(
        artifact, objective, domain=domain, protocol=protocol
    )
    return inputs


def emit_derive_prompt(
    objective: str,
    *,
    domain: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
    """Emit the artifact-BLIND DERIVE prompt for a fresh subagent (AC.AR.3).

    The artifact is NEVER an input here — the derive phase constructs the
    correct-artifact spec from objective + methodology alone, so the fresh
    subagent that runs it cannot have seen the artifact. This is the
    structural guarantee that the in-session derive leg is artifact-blind
    even though the CALLER has read the artifact.
    """
    # Pass an empty artifact: derive_prompt/derive_seed never concatenate
    # the artifact, but keeping it empty makes the blindness unmissable.
    inputs = _inputs("", objective, domain=domain, protocol=protocol)
    return derive_prompt(inputs)


def emit_diff_prompt(
    artifact: str,
    objective: str,
    derived_spec: str,
    *,
    domain: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
) -> str:
    """Emit the DIFF prompt (derivation + artifact) for a fresh subagent.

    Given the artifact-blind derivation captured in step 1, emit the diff
    prompt that reveals the artifact and tasks the fresh diff subagent to
    diff reality against that derivation (AC.AR.3, DIFF phase).
    """
    inputs = _inputs(artifact, objective, domain=domain, protocol=protocol)
    return diff_prompt(inputs, derived_spec)


def run_insession_standard(
    artifact: str,
    objective: str,
    *,
    derived_spec: str,
    diff_raw: str,
    domain: Optional[str] = None,
) -> ReviewResult:
    """Run a STANDARD review from the caller's two captured legs (AC.AR.1).

    ``derived_spec`` is the fresh DERIVE subagent's output; ``diff_raw`` is
    the fresh DIFF subagent's output. Both are replayed through the REAL
    pipeline (seed already consumed to build the prompts; here the parse ->
    generic-lint -> ground-truth validation -> verdict path runs exactly as
    it does for the subprocess backend). NO nested ``claude -p`` runs.

    The two-phase falsification isolation is preserved by CONSTRUCTION: the
    caller obtained ``derived_spec`` from a fresh subagent given the
    artifact-blind derive prompt (:func:`emit_derive_prompt`), and
    ``diff_raw`` from a SEPARATE fresh subagent — not from its own
    artifact-polluted context.
    """
    return review_text(
        artifact,
        objective,
        tier="STANDARD",
        domain=domain,
        model_fn=replay_model_fn([derived_spec, diff_raw]),
    )


# --------------------------------------------------------------------------
# Stepwise CLI — the SKILL drives this in-session, dispatching a FRESH
# subagent between `derive` and `diff`. Each subcommand is one short call
# that never spawns a nested `claude -p`; the model legs are the agent's
# own Task subagents.
# --------------------------------------------------------------------------


def _resolve_objective(args: argparse.Namespace) -> str:
    if getattr(args, "objective_file", None):
        return Path(args.objective_file).read_text(encoding="utf-8")
    return args.objective


def _build_insession_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adversarial-review insession",
        description="In-session adversarial review — the caller (an "
        "in-session agent) supplies each critic phase from a FRESH "
        "subagent, so no nested `claude -p` subprocess is spawned. Run "
        "`derive`, dispatch a fresh subagent, `diff`, dispatch a fresh "
        "subagent, then `finalize`.",
    )
    sub = p.add_subparsers(dest="phase", required=True)

    def _obj(sp: argparse.ArgumentParser) -> None:
        g = sp.add_mutually_exclusive_group(required=True)
        g.add_argument("--objective", help="the artifact's stated objective")
        g.add_argument("--objective-file", help="path to a file with the objective")
        sp.add_argument("--domain", default=None, help="domain for methodology lookup")

    d = sub.add_parser(
        "derive",
        help="emit the artifact-BLIND derive prompt (feed to a fresh subagent)",
    )
    _obj(d)

    f = sub.add_parser(
        "diff",
        help="emit the diff prompt given the captured derivation (fresh subagent)",
    )
    _obj(f)
    f.add_argument("--artifact", required=True, help="path to the artifact file")
    f.add_argument(
        "--derived-file",
        required=True,
        help="path to the file holding the DERIVE subagent's output",
    )

    z = sub.add_parser(
        "finalize",
        help="replay both captured legs through the real pipeline; print the review",
    )
    _obj(z)
    z.add_argument("--artifact", required=True, help="path to the artifact file")
    z.add_argument(
        "--derived-file",
        required=True,
        help="path to the file holding the DERIVE subagent's output",
    )
    z.add_argument(
        "--diff-raw-file",
        required=True,
        help="path to the file holding the DIFF subagent's output",
    )
    return p


def insession_main(argv: Optional[list[str]] = None) -> int:
    """CLI for the in-session handshake (AC.AR.1 via the injected leg).

    ``derive`` / ``diff`` print a prompt to stdout for the agent to hand to
    a fresh subagent; ``finalize`` prints the rendered review. Exit 0 (this
    is a review, never a gate).
    """
    args = _build_insession_parser().parse_args(argv)
    objective = _resolve_objective(args)

    if args.phase == "derive":
        print(emit_derive_prompt(objective, domain=args.domain))
        return 0

    if args.phase == "diff":
        artifact = Path(args.artifact).read_text(encoding="utf-8")
        derived = Path(args.derived_file).read_text(encoding="utf-8")
        print(emit_diff_prompt(artifact, objective, derived, domain=args.domain))
        return 0

    # finalize
    artifact = Path(args.artifact).read_text(encoding="utf-8")
    derived = Path(args.derived_file).read_text(encoding="utf-8")
    diff_raw = Path(args.diff_raw_file).read_text(encoding="utf-8")
    result = run_insession_standard(
        artifact,
        objective,
        derived_spec=derived,
        diff_raw=diff_raw,
        domain=args.domain,
    )
    print(render_report(result, args.artifact))
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.exit(insession_main())
