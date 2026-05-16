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

"""AC.RPB.2 / AC.RPB.6 — the REAL upstream ``programbench eval``
invoker + the real ``*.eval.json`` parser (the deterministic
positive-real-outcome FLOOR signal).

REUSE, NOT re-derivation (D-RPB-7 / Lens 1): the invocation form, the
``<run_dir>/<instance_id>/submission.tar.gz`` packaging shape, the
instance-id binding, the HF-blob resolution, and the proven
amd64-emulation runnability are the EXISTING pos3
``programbench-derivative`` real-PB plumbing — established Tier-0 by
the builder's live recheck of
``pos3/.../harness/eval_submission.sh`` +
``programbench-eval/src/programbench/cli/main.py`` +
``.../eval/eval.py`` (``score = n_resolved / len(test_results)``;
``is_resolved iff status=='passed'``; ``compile_failed`` => error_code
set + ``not_run`` injected => score 0.0). This module DRIVES that
existing upstream CLI; it does NOT re-implement the eval.

The real upstream eval leg is WALL-CLOCK-HEAVY under amd64 emulation
(F2 §10.3 — ~8-33 min/task on prior real runs); the caller records
the eval-emulation wall-clock DISTINCTLY from the agent wall-clock
(AC.RPB.6 / D-RPB-4).
"""

from __future__ import annotations

import json
import subprocess
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path

# The existing real-PB upstream eval clone (read-only reuse, D-RPB-7).
# Resolved from the well-known pos3 experiment path the builder
# live-verified (HEAD 4e8456b, real eval.py, `uv run programbench
# eval --help` exit 0). Overridable for portability.
DEFAULT_UPSTREAM_EVAL_DIR = Path(
    "/Users/lukeivers/pos3/workspace/experiments/"
    "programbench-derivative/programbench-eval"
)


@dataclass
class UpstreamEvalResult:
    """The parsed REAL upstream ``*.eval.json`` graded signal
    (AC.RPB.2 floor / AC.RPB.6 evidence)."""

    instance_id: str
    score: float            # n_resolved / len(test_results); 0.0 on
    #                         compile_failed (per upstream eval.py)
    n_resolved: int
    n_tests: int
    error_code: str | None
    eval_json_path: str
    eval_emulation_wall_clock_s: float
    raw_stdout_tail: str
    produced_submission: bool


def package_submission(work_dir: Path, dest_tar: Path) -> bool:
    """Package an arm's produced work dir into the upstream
    ``submission.tar.gz`` shape (D-RPB-7 reuse of the existing
    packaging contract). Returns True iff a non-empty submission was
    produced (the arm actually wrote files — the
    did-not-produce-output signal)."""
    work_dir = Path(work_dir)
    dest_tar = Path(dest_tar)
    dest_tar.parent.mkdir(parents=True, exist_ok=True)
    files = [
        p for p in work_dir.rglob("*")
        if p.is_file() and ".git" not in p.parts
    ] if work_dir.exists() else []
    produced = len(files) > 0
    with tarfile.open(dest_tar, "w:gz") as tf:
        for p in files:
            tf.add(p, arcname=str(p.relative_to(work_dir)))
    return produced


def run_upstream_eval(
    *,
    instance_id: str,
    filter_regex: str,
    submission_tar: Path,
    run_dir: Path,
    upstream_eval_dir: Path | None = None,
    docker_cpus: int = 4,
    timeout: int = 5400,
) -> UpstreamEvalResult:
    """Invoke the REAL upstream ``programbench eval`` against one
    instance's submission under amd64 Docker emulation, in the EXACT
    invocation form the existing harness proved (D-RPB-7):

      ``uv run programbench eval <run_dir> --workers 1
      --branch-workers 1 --docker-cpus N --filter '^<inst>$'
      --image-tag task --force``

    from the upstream clone dir. The result lands at
    ``<run_dir>/<instance_id>/<instance_id>.eval.json``; this parses
    the real graded ``score = n_resolved / len(test_results)`` (0.0 on
    ``compile_failed`` per the upstream contract). The agent NEVER
    sees this command or the test suite (ground-truth isolation,
    AC.RPB.1) — this runs AFTER the arm has produced its work dir.
    """
    ued = Path(upstream_eval_dir or DEFAULT_UPSTREAM_EVAL_DIR)
    run_dir = Path(run_dir)
    inst_dir = run_dir / instance_id
    inst_dir.mkdir(parents=True, exist_ok=True)
    sub_dest = inst_dir / "submission.tar.gz"
    if Path(submission_tar).resolve() != sub_dest.resolve():
        sub_dest.write_bytes(Path(submission_tar).read_bytes())

    argv = [
        "uv", "run", "programbench", "eval", str(run_dir),
        "--workers", "1",
        "--branch-workers", "1",
        "--docker-cpus", str(docker_cpus),
        "--filter", filter_regex,
        "--image-tag", "task",
        "--force",
    ]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            argv, cwd=str(ued), capture_output=True, text=True,
            timeout=timeout,
        )
        stdout_tail = ((proc.stdout or "") + "\n"
                       + (proc.stderr or ""))[-3000:]
    except subprocess.TimeoutExpired as exc:
        stdout_tail = (
            f"UPSTREAM-EVAL TIMEOUT after {timeout}s "
            f"(amd64 emulation is wall-clock-heavy — F2 §10.3): {exc}"
        )
    eval_wall = time.monotonic() - t0

    eval_json = inst_dir / f"{instance_id}.eval.json"
    score = 0.0
    n_resolved = 0
    n_tests = 0
    error_code: str | None = "eval_json_absent"
    if eval_json.exists():
        try:
            doc = json.loads(eval_json.read_text())
            results = doc.get("test_results", []) or []
            n_tests = len(results)
            n_resolved = sum(
                1 for r in results if r.get("status") == "passed"
            )
            score = (n_resolved / n_tests) if n_tests else 0.0
            error_code = doc.get("error_code")
        except (json.JSONDecodeError, OSError) as exc:
            error_code = f"eval_json_unparseable: {exc}"
            score = 0.0

    return UpstreamEvalResult(
        instance_id=instance_id,
        score=round(score, 6),
        n_resolved=n_resolved,
        n_tests=n_tests,
        error_code=error_code,
        eval_json_path=str(eval_json),
        eval_emulation_wall_clock_s=round(eval_wall, 2),
        raw_stdout_tail=stdout_tail,
        produced_submission=True,
    )
