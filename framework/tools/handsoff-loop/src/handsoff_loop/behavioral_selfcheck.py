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
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""The loop's OWN self-constructed BEHAVIORAL self-check (AC.BRC.1 /
AC.BRC.4 / AC.BRC.6).

The hands-off loop's terminal "done" was, from source
(orchestrator.py:203-244 @ 48418ff), a SINGLE structural-presence
verify — and the realpb in-loop ``check_command`` was literally
``"true"`` (arms.py:200), so the loop's keep-going condition was
satisfied by a no-op.  This module constructs the loop's OWN
behavioural self-check: a self-constructed *functional* check, derived
from the task's plain-language objective, that EXERCISES the produced
artefact's observable behaviour rather than merely asserting a
``compile.sh`` + a source file exist.

WHY THIS MODULE IS STRUCTURALLY SEPARATE (AC.BRC.4 — the load-bearing
isolation, provable by construction):

  * It imports NEITHER ``verify`` (the frozen graded independent +
    anti-overfit authority — the EXTERNAL scoring authority the loop
    must not have been steered to) NOR any benchmark scorer / the
    independent held-out judge / the intake faithfulness judge
    (``intake._judge_faithful``).  An AST/import test
    (test_AC_BRC_4_*) asserts this module's import set is clean — the
    isolation is provable, not asserted in prose.
  * The behavioural self-check is the loop's OWN check the SUB-AGENT
    runs+surfaces each turn via the EXISTING ``/goal`` ``check_command``
    seam (goal_drive.py:67-107).  It never consumes the frozen graded
    acceptance; the ``FrozenAcceptance.assert_unseen_by`` freeze-
    isolation spine (verify.py:60-82) is preserved by construction —
    this module produces a shell COMMAND STRING, never reads the
    frozen spec, never the held-out inputs.

WHAT "BEHAVIOURAL" MEANS HERE (AC.BRC.1):

  A check that passes on structural presence alone (a ``compile.sh`` +
  a source file exist) or that is satisfied by running ``true`` / any
  no-op does NOT satisfy AC.BRC.1.  The constructed command (a) runs /
  exercises the produced artefact, (b) asserts an observable effect
  the plain-language objective describes, (c) prints the existing
  ``DONE_SENTINEL`` / ``NOT_DONE_SENTINEL`` line so the established
  ``/goal``-decides-via-surfaced-exit-code seam is reused unchanged
  (Lens 1 — compose the present Claude-native primitive, do not
  re-implement turn drive).

GENERIC, NOT REALPB-SPECIFIC (AC.BRC.6): the same construct serves any
task driven through the loop.  ``reject_no_op`` makes a ``"true"`` /
no-op / structural-only ``check_command`` a hard error at the seam, so
the realpb ``"true"`` literal is replaced by routing the in-loop check
through THIS generic construct — not a realpb-specific hack and not
another no-op.

NO Anthropic API key, NO spawn here: this module only BUILDS a command
string.  It spawns nothing — the sub-agent runs the command under the
already-isolated ``/goal``-driven ``claude -p`` the orchestrator owns
(framework/tools/handsoff-loop/_isolation.py); there is no ``claude``
invocation in this module to isolate.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass

from .goal_drive import DONE_SENTINEL, NOT_DONE_SENTINEL

# Commands that are NOT a behavioural check — a no-op / structural-
# presence-only signal.  Routing the loop's in-loop check through one
# of these is the exact defect AC.BRC.1/.6 forbid (arms.py:200's
# literal "true").  The match is conservative: the bare no-op
# utilities and the structural-floor presence pattern.
_NO_OP_COMMANDS = frozenset({
    "true", "/bin/true", ":", "/usr/bin/true",
    "exit 0", "echo", "false", "/bin/false",
})


class NotABehavioralCheck(ValueError):
    """Raised when an in-loop check_command is a no-op / structural-

    only signal rather than a behavioural self-check (AC.BRC.1 /
    AC.BRC.6).  Refusing is honest; silently accepting a ``"true"``
    keep-going condition is the exact gap this cycle closes."""


def reject_no_op(check_command: str) -> str:
    """Refuse a no-op / structural-only in-loop ``check_command``.

    AC.BRC.6 — the realpb ``"true"`` literal (arms.py:200) and any
    other no-op / structural-presence-only command are NOT a
    behavioural self-check.  Returns the command unchanged when it is
    not a recognised no-op; raises ``NotABehavioralCheck`` otherwise.
    Callers route the in-loop check through
    :func:`build_behavioral_check_command` instead of a no-op.
    """
    norm = (check_command or "").strip()
    if not norm:
        raise NotABehavioralCheck(
            "empty check_command is not a behavioural self-check "
            "(AC.BRC.1) — derive one from the plain-language objective"
        )
    head = shlex.split(norm)[0] if norm else ""
    if norm in _NO_OP_COMMANDS or head in _NO_OP_COMMANDS:
        raise NotABehavioralCheck(
            f"in-loop check_command {check_command!r} is a no-op / "
            f"structural-only signal — not a behavioural self-check "
            f"(AC.BRC.1/.6). Route through "
            f"build_behavioral_check_command(objective=...) so the "
            f"loop's 'done' is gated on observable behaviour, not a "
            f"no-op or structural presence."
        )
    return norm


@dataclass(frozen=True)
class BehavioralCheckSpec:
    """A self-constructed behavioural self-check for one objective.

    ``objective`` is the task's plain-language intent (the orchestrator
    already carries it).  ``reference_artifact`` is an OPTIONAL
    runnable reference the check MAY probe/diff against where a task
    supplies one (D-BRC-5 — permitted, not mandated); where none is
    supplied the check is synthesised from the plain-language intent
    alone.  The spec NEVER carries the frozen graded acceptance / the
    held-out inputs (AC.BRC.4 — provable: this dataclass has no field
    for them and this module imports no scorer/judge).
    """

    objective: str
    work_dir: str
    reference_artifact: str | None = None

    def directive(self) -> str:
        """A plain-language behavioural-evidence directive for the

        sub-agent brief: the artefact must be EXERCISED and OBSERVED
        to behave as the objective describes — structural presence
        (a file exists / it compiles) is explicitly NOT enough."""
        ref = (
            f"\nA runnable reference artefact is available at "
            f"{self.reference_artifact!r}; you MAY diff/compare the "
            f"produced artefact's OBSERVABLE BEHAVIOUR against it."
            if self.reference_artifact else ""
        )
        return (
            "Behavioural-evidence requirement (the loop's OWN self-"
            "check, NOT the external grader): the produced artefact "
            "must be RUN / EXERCISED and OBSERVED to actually behave "
            f"as this plain-language objective describes: "
            f"{self.objective!r}. A submission that is structurally "
            "present (a file exists / it compiles) but does NOT "
            "behave as described is NOT done. Implement, then run the "
            "behavioural self-check and surface its full output."
            + ref
        )

    def command(self) -> str:
        """The runnable behavioural self-check command string.

        The sub-agent runs THIS each turn via the existing ``/goal``
        ``check_command`` seam (goal_drive.py:67-107); it prints the
        established ``DONE_SENTINEL`` / ``NOT_DONE_SENTINEL`` line so
        ``/goal``'s evaluator keys off the SURFACED exit-code line
        exactly as before (Lens 1 — the drive/stop seam is reused
        unchanged; only WHAT the in-loop check asserts changes from
        structural presence / a no-op to observable behaviour).

        The command runs the loop-emitted behavioural probe
        ``loam_behavioral_selfcheck.sh`` in the work dir — a probe the
        SUB-AGENT authors+keeps-current from the plain-language
        objective (it exercises the artefact and asserts the observed
        effect).  The command refuses to report done on a missing /
        empty / no-op probe: a probe that is absent, empty, or a bare
        ``true``/``:`` prints ``NOT_DONE`` (structural presence is
        explicitly insufficient — AC.BRC.1).  This is generic across
        tasks (AC.BRC.6): the construct, not a per-task string.
        """
        probe = "loam_behavioral_selfcheck.sh"
        # The runner is a `python3 -c` one-liner: Python is already a
        # hard loop dependency, and a single `-c` argument quotes
        # deterministically (it survives BOTH direct argv execution
        # and being re-wrapped as `sh -c "<this command>"` by the
        # /goal seam — no fragile nested-shell quoting).  The runner:
        #   1. NOT_DONE if the probe is absent / empty (structural
        #      presence is explicitly insufficient — AC.BRC.1);
        #   2. NOT_DONE if the probe's non-whitespace body is a bare
        #      no-op (`true`/`:`/`exit 0`, with or without a shebang)
        #      — a no-op probe is not behavioural evidence
        #      (AC.BRC.1/.6);
        #   3. otherwise EXECUTE the probe and let its exit code
        #      decide; print the established DONE/NOT_DONE sentinel so
        #      the existing /goal evaluator keys off the surfaced
        #      exit-code line unchanged (Lens 1).
        py = (
            "import os,subprocess,sys\n"
            f"P={probe!r}\n"
            f"DONE={DONE_SENTINEL!r}\n"
            f"ND={NOT_DONE_SENTINEL!r}\n"
            "def nd(m):\n"
            " print(ND); print(m); sys.exit(1)\n"
            "if not os.path.isfile(P) or os.path.getsize(P)==0:\n"
            " nd('behavioural self-check probe '+P+' absent or "
            "empty - structural presence is NOT behavioural "
            "evidence (AC.BRC.1)')\n"
            "raw=open(P).read()\n"
            "body=''.join(raw.split())\n"
            "noops={'true',':','exit0','/bin/true','false',"
            "'/bin/false'}\n"
            "lines=[l.strip() for l in raw.splitlines() "
            "if l.strip() and not l.strip().startswith('#')]\n"
            "if body in noops or (len(lines)==1 and lines[0] in "
            "{'true',':','exit 0','/bin/true','false'}) or not "
            "lines:\n"
            " nd('behavioural self-check probe is a no-op - not "
            "behavioural evidence (AC.BRC.1/.6)')\n"
            "r=subprocess.run(['sh',P])\n"
            "if r.returncode==0:\n"
            " print(DONE); sys.exit(0)\n"
            "nd('behavioural self-check FAILED - the artefact does "
            "not yet behave as the objective describes')\n"
        )
        return f"python3 -c {shlex.quote(py)}"


def build_behavioral_check_command(
    *,
    objective: str,
    work_dir: str,
    reference_artifact: str | None = None,
) -> BehavioralCheckSpec:
    """Construct the loop's OWN behavioural self-check from the plain-

    language objective (AC.BRC.1 / AC.BRC.4 / AC.BRC.6).

    Returns a :class:`BehavioralCheckSpec`; the caller uses
    ``.command()`` as the ``/goal`` ``check_command`` (replacing a
    structural-presence / ``"true"`` signal generically) and
    ``.directive()`` as the behavioural-evidence line carried into the
    sub-task brief / a refine re-dispatch.

    The construct imports no scorer/judge (AC.BRC.4 — provable by the
    import test); it produces only a command string + a directive, so
    it cannot have been steered to the frozen graded acceptance.
    """
    if not (objective or "").strip():
        raise NotABehavioralCheck(
            "cannot derive a behavioural self-check from an empty "
            "objective (AC.BRC.1)"
        )
    return BehavioralCheckSpec(
        objective=objective.strip(),
        work_dir=work_dir,
        reference_artifact=reference_artifact,
    )
