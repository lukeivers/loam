"""The `/goal`-under-`-p` drive/stop leg (Lens-1 composition).

Maps to AC.A.4(i) ("reached frozen done without human loop-driving").

Grounded strictly in the verified primitive surface
(`claude-code-primitive-surface-2026-05-16.md`, binary 2.1.143):

  * `/goal <condition>` is REAL — added v2.1.139, present in 2.1.143.
    "Claude keeps working across turns until the condition is met";
    after each turn a small fast model (Haiku default) checks the
    condition.  Works non-interactively under `-p`.  Condition max
    4,000 characters.

  * The evaluator "does not call tools, so it can only judge what
    Claude has already surfaced in the conversation."  Therefore the
    condition is phrased so it is provable from the transcript ONLY
    via the surfaced exit code of loam's own tool-executing
    independent check (verify.py) — NOT from the sub-agent's prose.

The hard boundary (contract §7, enforced here): `/goal` is the
drive/stop leg ONLY.  loam's independent check decides; `/goal`'s
Haiku evaluator merely keys off the surfaced exit-code line that the
in-turn check prints.  This module builds the argv + the condition
string; it never lets `/goal` be the artefact judge and never
re-implements turn-after-turn drive (that would be the Lens-1
violation the contract forbids).

NO Anthropic API key: argv targets the real `claude` binary, default
Sonnet.  `--bare` is deliberately NOT used (the verified surface
flags `--bare` as incompatible with loam's subscription-only / OAuth
path).
"""

from __future__ import annotations

from dataclasses import dataclass, field

GOAL_CONDITION_MAX = 4000  # live-sourced cap (binary 2.1.143)

# The surfaced sentinel the in-turn independent check prints.  The
# /goal Haiku evaluator can ONLY see transcript text, so the loop's
# completion is keyed off this exact line appearing in the surfaced
# output — which the tool-executing verify step (not the sub-agent)
# emits.  This is the "loam decides, /goal drives" seam.
DONE_SENTINEL = "HANDSOFF_INDEPENDENT_CHECK: DONE exit=0"
NOT_DONE_SENTINEL = "HANDSOFF_INDEPENDENT_CHECK: NOT_DONE"


@dataclass(frozen=True)
class GoalDriveSpec:
    """A `/goal`-driven `claude -p` invocation for one sub-task.

    `directive` is the scoped sub-task brief (never contains the
    frozen acceptance — that isolation is enforced upstream in
    orchestrator.py / verify.assert_unseen_by).  `check_command` is
    the loam tool-executing independent check the sub-agent must run
    and surface the result of every turn.
    """

    directive: str
    check_command: str
    model: str = "sonnet"
    max_turns_hint: int = 8

    def goal_condition(self) -> str:
        """Build the ≤4,000-char condition string.

        The condition is provable from the transcript ONLY by the
        surfaced exit-code line of `check_command` — never by the
        sub-agent claiming success.  This is the structural
        enforcement of "loam's independent check decides".
        """
        cond = (
            f"The sub-task is done ONLY when the command "
            f"`{self.check_command}` has been run in this turn and the "
            f"line `{DONE_SENTINEL}` is present verbatim in the surfaced "
            f"output. The sub-agent's own claim of success does NOT "
            f"satisfy this condition — only the surfaced exit-code line "
            f"does. If the check has not yet surfaced "
            f"`{DONE_SENTINEL}`, keep working: implement, then re-run "
            f"`{self.check_command}` and surface its full output "
            f"including the `{DONE_SENTINEL}` / `{NOT_DONE_SENTINEL}` "
            f"line."
        )
        if len(cond) > GOAL_CONDITION_MAX:
            raise ValueError(
                f"/goal condition {len(cond)} > {GOAL_CONDITION_MAX} "
                f"char cap (binary 2.1.143). Shorten check_command."
            )
        return cond

    def prompt(self) -> str:
        """The `-p` prompt: directive + the /goal directive line.

        `/goal <condition>` set inside the prompt starts the loop;
        Claude keeps taking turns until the surfaced-exit-code
        condition holds, with no human driving the loop.
        """
        return (
            f"{self.directive}\n\n"
            f"After each implementation step, run `{self.check_command}` "
            f"and surface its FULL output verbatim (it prints either "
            f"`{DONE_SENTINEL}` or `{NOT_DONE_SENTINEL}`).\n\n"
            f"/goal {self.goal_condition()}"
        )


def build_goal_drive_argv(
    spec: GoalDriveSpec,
    *,
    cost_json: bool = True,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Build the real `claude -p` argv for a /goal-driven sub-agent.

    `cost_json=True` adds `--output-format json` so cost is MEASURED
    (D-COST-BAND closes the probe's instrumentation gap), not
    estimated.  `--bare` is intentionally never added.
    """
    argv = [
        "claude",
        "-p",
        spec.prompt(),
        "--model",
        spec.model,
        "--permission-mode",
        "bypassPermissions",
    ]
    if cost_json:
        argv += ["--output-format", "json"]
    if extra_args:
        argv += list(extra_args)
    return argv
