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
"""


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
                "check_command": "true",
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
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            env=env,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = f"LOAM-ARM TIMEOUT after {timeout}s: {exc}"
    dt = time.monotonic() - t0

    # Loop cost is MEASURED (orchestrator sums sub-agent
    # total_cost_usd from the --output-format json envelope). Parse
    # the loop's own JSON result line for cost_usd.
    cost: float | None = None
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line.startswith("{") and "cost_usd" in line:
            try:
                cost = json.loads(line).get("cost_usd")
            except json.JSONDecodeError:
                pass
            break
    # Fold in the artefact dir's final_verify + transcript tails so
    # the independent judge sees the real machine evidence.
    fv = artifact_dir / "final_verify.json"
    if fv.exists():
        out += "\n\n[final_verify.json]\n" + fv.read_text()
    return out, dt, cost
