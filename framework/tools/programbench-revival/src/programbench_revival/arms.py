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

"""AC.PBR.1 — the two arms, isolated and identically tasked under a
CLOSED (no-answer) user channel (zero-interaction parity, D-PBR-6).

  * Baseline arm (no-harness floor): ONE bare ``claude -p`` given the
    task's plain-language statement and nothing else — no decompose,
    no independent verify, no refinement, no persistence. Spawned
    through the MANDATED ``spawn_isolated_claude`` surface (NEVER a
    hand-rolled subprocess.run(["claude",...]) — the Telegram-death
    #5 hard error).

  * Loam arm: the REAL sealed v0.11.0 hands-off loop driven through
    its ACTUAL persona-invocable entry surface (``handsoff-loop
    run``), no mock, no pre-loop machinery. Driven with ``--frozen``
    so NO live question is ever posed (the AC.PBR.1 satisfiability
    path for realising the closed channel) — the loop's interactive
    intake/approval machinery degrades to internal best-effort under
    the closed channel; the loop decides done by EXECUTING the frozen
    check via verify.py. The cooperative-user simulation is NOT used
    (D-PBR-6 — removed as the loam-arm model).

Both arms run per-task ENVIRONMENT-ISOLATED (fresh work dir, the task
setup files written fresh, no residual state across tasks/arms) and
ISOLATED FROM the ground-truth check (neither arm's agent ever sees
the floor/held-out check command or its path — input parity is total;
the only difference under measurement is the loop's INTERNAL
machinery operating on the SAME single prompt).

NO Anthropic API key — real ``claude`` binary, default Sonnet.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

_ISO_SRC = (
    Path(__file__).resolve().parents[3]
    / "loam-spawn-isolation" / "src"
)
if str(_ISO_SRC) not in sys.path:
    sys.path.insert(0, str(_ISO_SRC))

from loam_spawn_isolation import spawn_isolated_claude  # noqa: E402

_HANDSOFF_SRC = (
    Path(__file__).resolve().parents[3]
    / "handsoff-loop" / "src"
)

# The single plain-language directive an arm receives. It carries
# ONLY the user's sentence + the work-dir contract — NO frozen check,
# NO ground-truth, NO held-out input (input parity; ground-truth
# isolation, AC.PBR.1).
#
# The SUBMISSION-BUILD DEPENDENCY CONVENTION (AC.PBD.1 / AC.PBD.2 /
# AC.PBD.3) is appended HERE — in the single prompt template BOTH
# arms construct their prompt from (run_baseline_arm and run_loam_arm
# both call `_ARM_DIRECTIVE.format(statement=...)`). This is the only
# parity-and-hash-safe seam:
#   * INPUT PARITY (AC.PBD.3 / AC.RPB.1): the convention reaches both
#     arms BYTE-IDENTICALLY through the same single prompt both arms
#     already receive; the harness NEVER post-edits, patches, or
#     inspects an arm's PRODUCED `compile.sh`/work dir to enforce
#     determinism — that would silently break the binding
#     zero-interaction parity invariant. This block shapes the prompt
#     the agent authors its `compile.sh` FROM; it never touches the
#     produced artefact, and the closed no-answer channel is
#     unchanged.
#   * FROZEN TASK-SET CONTENT HASH UNTOUCHED (AC.PBD.6): the
#     convention is NOT written into the per-task `statement` bytes in
#     `tasks/tasks.json` (those bytes are content-hash-pinned —
#     `load_frozen_realpb_set` sha256s the exact file; the frozen
#     task-set content hash is a FROZEN measurement-semantics surface).
#     Living in the directive template keeps the frozen task content
#     and its pinned hash byte-unchanged.
# Determinism + fail-loud only; no new outcome semantics — a failed
# dependency install is a non-pass BY CONSTRUCTION via the EXISTING
# upstream `compile_failed => 0` contract (NOT a new outcome class,
# NOT an interactive prompt, NOT a retry-to-green — the zero-
# interaction one-shot contract AC.RPB.1 / honest-negative-first-class
# AC.RPB.7 are unchanged).
_SUBMISSION_BUILD_DEP_CONVENTION = """\

Submission-build dependency rule (applies when your build needs \
third-party packages — produce a build that is reproducible, not one \
that depends on install luck):
- If `compile.sh` (or any build step) installs dependencies, pin \
every dependency to an EXACT version (e.g. `pip3 install \
pyyaml==6.0.2 tomli==2.0.1`), so the same submission resolves to the \
same dependency set every time it is built.
- The dependency-install step MUST fail loud: if a required \
dependency cannot be installed, the build MUST exit non-zero and \
stop. Do NOT suppress install errors and continue — never \
`2>/dev/null`, never `|| true`, never `|| :`, never any construct \
that lets the build proceed as if the dependency were present when \
the install actually failed. A build that cannot get its \
dependencies is a failed build and must report itself as one.
- Prefer the language/runtime standard library when it can do the \
job, so the build needs no third-party dependency at all.
There is no one to ask and no retry: a clean reproducible build that \
fails loudly when a dependency is missing is correct; a build that \
silently swallows a failed install is not.
"""

_ARM_DIRECTIVE = """\
You are given ONE task from a non-technical user, stated in plain \
language. There is NO channel to ask them anything — you cannot ask a \
clarifying question and you will get no answer. Produce the real \
result they asked for, in the current working directory, working \
ENTIRELY from this single sentence and the files already in this \
directory. Do the actual task — produce the real artefact / make the \
real change — do not merely describe what you would do.

The user's request:
{statement}
""" + _SUBMISSION_BUILD_DEP_CONVENTION


def _write_setup(work_dir: Path, setup_files: dict[str, str]) -> None:
    for rel, content in setup_files.items():
        p = work_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def run_baseline_arm(
    *,
    statement: str,
    setup_files: dict[str, str],
    work_dir: Path,
    timeout: int = 900,
) -> tuple[str, float, float | None]:
    """ONE bare ``claude -p`` (the documented no-harness floor).

    Given ONLY the plain-language statement (the closed-channel
    single prompt) under a fresh isolated work dir. Spawned through
    the MANDATED isolation surface. Returns (transcript, wall_s,
    cost_usd|None) — cost MEASURED from --output-format json
    (D-COST-BAND, never estimated).
    """
    work_dir = Path(work_dir)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    _write_setup(work_dir, setup_files)

    prompt = _ARM_DIRECTIVE.format(statement=statement)
    t0 = time.monotonic()
    proc = spawn_isolated_claude(
        ["claude", "-p", prompt, "--model", "sonnet",
         "--output-format", "json", "--permission-mode",
         "bypassPermissions"],
        cwd=str(work_dir),
        capture_output=True, text=True, timeout=timeout,
    )
    dt = time.monotonic() - t0
    out = proc.stdout or ""
    cost: float | None = None
    transcript = out
    try:
        env = json.loads(out)
        if isinstance(env, dict):
            cost = env.get("total_cost_usd")
            transcript = str(env.get("result") or out)
    except json.JSONDecodeError:
        pass
    return transcript + "\n" + (proc.stderr or ""), dt, cost


def run_loam_arm(
    *,
    task_id: str,
    statement: str,
    setup_files: dict[str, str],
    floor_check_argv: list[str],
    held_out_argv: list[str],
    work_dir: Path,
    artifact_dir: Path,
    timeout: int = 1800,
    behavioral_done: bool = True,
    reference_artifact: str | None = None,
    max_refine_attempts: int = 2,
    cost_ceiling_usd: float | None = None,
    wall_ceiling_s: float | None = None,
) -> tuple[str, float, float | None]:
    """The REAL sealed v0.11.0 hands-off loop via its ACTUAL CLI.

    ``handsoff-loop run --objective <the user sentence> --frozen
    <spec.json> --work-dir <dir> --artifact-dir <dir>``. The frozen
    spec's check_argv/held_out_argv are the task's floor + held-out
    checks (the loop EXECUTES them via verify.py to decide done — the
    sub-agents' self-reports are never trusted). ``sub_tasks`` is ONE
    internal scoped sub-task whose brief carries ONLY the user's
    plain-language statement (input parity with the baseline; the
    frozen acceptance is kept UNSEEN by the brief —
    FrozenAcceptance.assert_unseen_by, AC.A.2). Driven with --frozen
    so NO live question is posed (closed channel, D-PBR-6). No mock,
    no pre-loop machinery, no cooperative-user simulation.
    """
    work_dir = Path(work_dir)
    artifact_dir = Path(artifact_dir)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_setup(work_dir, setup_files)

    # The frozen spec. `content` is the acceptance text (kept UNSEEN
    # by the sub-task brief). check_argv/held_out_argv are the task's
    # real floor + held-out checks the loop executes. The single
    # sub-task brief carries ONLY the user's sentence — identical to
    # the baseline's single prompt (input parity, AC.PBR.1). The
    # acceptance text deliberately does NOT echo the user statement so
    # assert_unseen_by(brief) cannot trip on the shared sentence.
    spec = {
        "acceptance_id": f"pbr_{task_id}",
        "content": (
            f"FROZEN-ACCEPTANCE pbr_{task_id}: the positive-real-"
            f"outcome floor check exits 0 (the real outcome was "
            f"actually delivered into the named target) AND the "
            f"held-out anti-overfit check exits 0. Independent + "
            f"anti-overfit; unseen by any sub-agent brief or judge."
        ),
        "check_argv": floor_check_argv,
        "held_out_argv": held_out_argv,
        "sub_tasks": [
            {
                "name": f"deliver_{task_id}",
                "brief": _ARM_DIRECTIVE.format(statement=statement),
                "tighter_acceptance": (
                    "The real result the user asked for is actually "
                    "present in the working directory (the real "
                    "artefact exists / the real change was made), "
                    "not merely described."
                ),
                # AC.BRC.6 — the in-loop check_command is NO LONGER
                # the hand-authored `"true"` literal (the concrete
                # defect: a no-op satisfied the keep-going condition).
                # It is replaced GENERICALLY: `--behavioral-done`
                # (below) routes the in-loop check through the loop's
                # OWN behavioural self-check construct
                # (handsoff_loop.behavioral_selfcheck), derived from
                # the plain-language objective and run against the
                # produced artefact.  This placeholder is a
                # SELF-DESCRIBING marker (NOT another no-op — the
                # construct's reject_no_op would refuse a `"true"`/`:`
                # here); the orchestrator's _behavioralize() overrides
                # it with the generic behavioural command.  The fix is
                # the generic construct, NOT a realpb-specific hack.
                "check_command": (
                    "BEHAVIORAL-SELF-CHECK-PLACEHOLDER "
                    "(replaced generically by "
                    "handsoff_loop.behavioral_selfcheck via "
                    "--behavioral-done; arms.py never hand-authors a "
                    "no-op in-loop check_command — AC.BRC.6)"
                ),
            }
        ],
    }
    spec_path = artifact_dir / f"frozen_{task_id}.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    argv = [
        sys.executable, "-m", "handsoff_loop.cli", "run",
        "--objective", statement,
        "--frozen", str(spec_path),
        "--work-dir", str(work_dir),
        "--artifact-dir", str(artifact_dir),
    ]
    # AC.BRC.1/.2/.6 — drive the loop's terminal "done" through its
    # OWN generic behavioural self-check (replacing the removed
    # arms.py:200 `"true"` literal generically) and re-drive a
    # BOUNDED number of refine attempts carrying the behavioural-
    # failure context, under the EXISTING cost/wall ceiling.  These
    # are the generic CLI flags — the construct is the loop's, not a
    # realpb-specific hack; the realpb arm is just one consumer.
    if behavioral_done:
        argv.append("--behavioral-done")
    if reference_artifact:
        argv += ["--reference-artifact", str(reference_artifact)]
    if max_refine_attempts:
        argv += ["--max-refine-attempts", str(max_refine_attempts)]
    if cost_ceiling_usd is not None:
        argv += ["--cost-ceiling-usd", str(cost_ceiling_usd)]
    if wall_ceiling_s is not None:
        argv += ["--wall-ceiling-s", str(wall_ceiling_s)]
    # The handsoff-loop CLI subprocess MUST inherit the FULL real
    # environment (so the loop's internal `claude -p` sub-agents
    # resolve the keychain-stored SUBSCRIPTION credential — there is
    # NO Anthropic API key, feedback_no_anthropic_api_key). The loop
    # then applies its OWN sealed telegram-poller isolation INTERNALLY
    # via handsoff_loop._isolation.isolated_env() (which itself starts
    # from os.environ and scrubs only the bot-token/API-key spellings,
    # air_gapped_config=False). Hand-stripping the env BEFORE the loop
    # starts breaks subscription auth ("Not logged in") and is the
    # exact defect this build's first run surfaced. We only ADD the
    # package PYTHONPATH on top of the inherited environment.
    import os

    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_HANDSOFF_SRC}{os.pathsep}{existing_pp}"
        if existing_pp else str(_HANDSOFF_SRC)
    )
    t0 = time.monotonic()
    loop_stdout = ""
    timed_out = False
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            env=env,
        )
        loop_stdout = proc.stdout or ""
        out = loop_stdout + "\n" + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        out = f"LOAM-ARM TIMEOUT after {timeout}s: {exc}"
    dt = time.monotonic() - t0

    # Loop cost is MEASURED (the orchestrator sums sub-agent
    # total_cost_usd from the --output-format json envelope; the CLI
    # emits it as the top-level `cost_usd` key of a PRETTY-PRINTED
    # multi-line `json.dumps({...}, indent=2)` result envelope on
    # stdout — handsoff_loop/cli.py).
    #
    # AC.PBD.4 / AC.PBD.5 — robust structured read (D-PBD-3). The
    # prior single-line scan (`for line in reversed(...): if
    # line.startswith("{") and "cost_usd" in line`) STRUCTURALLY
    # cannot match an `indent=2` object: the `{` opening line carries
    # no `cost_usd`, and the `"cost_usd": ...` line does not start
    # with `{` — so a MEASURED cost was silently lost to `null` on
    # every loam disposition. We instead scan stdout for the LAST
    # balanced top-level JSON object and parse the whole document.
    # Three outcomes are kept DISTINCT (never conflated):
    #   * envelope parsed, `cost_usd` present + non-null  -> the
    #     measured cost reaches the disposition (AC.PBD.4);
    #   * envelope parsed, `cost_usd` present but null     -> the loop
    #     genuinely did not measure a cost: HONEST-ABSENT (AC.PBD.5);
    #   * loop produced output but NO parseable result envelope with a
    #     `cost_usd` key (and it did not time out) -> a CONSUMER-SIDE
    #     parse MISS: a visible diagnostic is folded into the evidence
    #     `out` (the independent judge + run evidence see it); cost is
    #     left `None` but it is NOT a SILENT loss (AC.PBD.5).
    def _last_json_object(text: str) -> dict | None:
        """Return the last balanced, parseable top-level JSON object
        in ``text`` (the loop CLI's pretty-printed result envelope is
        the final such object printed before the CLI returns), or
        ``None`` if there is no parseable top-level object."""
        result: dict | None = None
        depth = 0
        start = -1
        in_str = False
        esc = False
        for i, ch in enumerate(text):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start >= 0:
                        try:
                            obj = json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            obj = None
                        if isinstance(obj, dict):
                            result = obj
                        start = -1
        return result

    cost: float | None = None
    envelope = _last_json_object(loop_stdout)
    if envelope is not None and "cost_usd" in envelope:
        # Honest value the loop reported: a real measured cost, or an
        # honest null when the loop genuinely measured none.
        cost = envelope.get("cost_usd")
    elif not timed_out and loop_stdout.strip():
        # The loop produced output but no result envelope carrying a
        # cost_usd key was parseable — a consumer-side parse miss, NOT
        # an honest-absent. Make it VISIBLE in the evidence rather
        # than silently recording null.
        out += (
            "\n\n[arms.run_loam_arm] cost-capture parse MISS: the "
            "loop produced stdout but no parseable result envelope "
            "with a `cost_usd` key was found; loam cost recorded as "
            "absent due to a consumer-side parse miss, NOT because "
            "the loop did not measure a cost (AC.PBD.5).\n"
        )
    # Fold in the artefact dir's final_verify + transcript tails so
    # the independent judge sees the real machine evidence.
    fv = artifact_dir / "final_verify.json"
    if fv.exists():
        out += "\n\n[final_verify.json]\n" + fv.read_text()
    return out, dt, cost
