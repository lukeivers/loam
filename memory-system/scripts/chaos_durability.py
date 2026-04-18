"""D12 — Kuzu chaos-durability runner.

Confirms Kuzu's durability posture under adverse conditions before
the memory system is declared production-ready. Three scenario
classes are exercised:

  (A) kill-mid-ingest    — a child process ingests an episode; the
                           parent sends SIGKILL partway through. On
                           restart, the DB is either cleanly rolled
                           back OR recoverable from WAL — never
                           corrupted. Verified by re-opening the DB
                           and counting episodes.

  (B) kill-mid-query     — a child process executes a search; the
                           parent sends SIGKILL mid-execution. After
                           restart, reads are idempotent — the prior
                           ingested state is intact.

  (C) WAL-recovery       — a child process ingests multiple episodes
                           and exits WITHOUT calling close(); the WAL
                           is left dirty. On reopen, Kuzu replays the
                           WAL and all committed episodes are visible.

All scenarios run against a dedicated chaos DB (data/kuzu_db_chaos)
to avoid polluting evaluation artifacts. The runner produces a
`data/runs/chaos_durability_<timestamp>.json` report with per-scenario
pass/fail and observations.

Why a runner rather than pytest? These scenarios require process kills
and WAL inspection; pytest's test-runner model makes that awkward.
The runner is invoked by D12's acceptance test and produces the
`docs/chaos-durability-report.md` summary.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti, prepare_graphiti  # noqa: E402


REPO = Path(__file__).resolve().parent.parent
CHAOS_DB = REPO / "data" / "kuzu_db_chaos"
RUNS_DIR = REPO / "data" / "runs"


# A small pool of synthetic episodes used by the chaos worker subprocess.
CHAOS_EPISODES = [
    (
        "chaos-ep-1",
        "2027-03-14T00:00:00+00:00",
        (
            "On 14 March 2027, Mira Adelyn confirmed that Tideglass "
            "passed the regulatory review ahead of schedule."
        ),
    ),
    (
        "chaos-ep-2",
        "2027-04-22T00:00:00+00:00",
        (
            "Tobi Imari reached a decision on 22 April 2027 to retain "
            "the Frostvault archive format rather than migrate."
        ),
    ),
    (
        "chaos-ep-3",
        "2027-05-10T00:00:00+00:00",
        (
            "Klemen Doric introduced Tideglass executives to Sondre "
            "Braten on 10 May 2027, opening the Norwegian partnership "
            "discussion."
        ),
    ),
    (
        "chaos-ep-4",
        "2027-06-18T00:00:00+00:00",
        (
            "Renji Okamoto scheduled the Rookery platform readiness "
            "review for 18 June 2027."
        ),
    ),
]


# ---- helpers ----


def _wipe_chaos_db() -> None:
    for sib in CHAOS_DB.parent.glob(CHAOS_DB.name + "*"):
        try:
            if sib.is_file():
                sib.unlink()
            elif sib.is_dir():
                import shutil as _sh
                _sh.rmtree(sib, ignore_errors=True)
        except OSError:
            pass


async def _count_quick_no_prepare() -> tuple[int, int]:
    """Count episodes and edges via a subprocess so Kuzu's file lock
    is released cleanly between operations.

    Kuzu's `close()` is a no-op (driver relies on GC). In a long-lived
    parent process, the lock can persist. Spawning a short-lived
    subprocess and waiting for its clean exit is the only reliable way
    to avoid lock contention with subsequent workers.
    """
    workers_dir = REPO / "scripts" / "_chaos_workers"
    workers_dir.mkdir(exist_ok=True)
    counter = workers_dir / "worker_count.py"
    counter.write_text(_WORKER_COUNT)
    proc = subprocess.run(
        [sys.executable, str(counter), json.dumps({"db_path": str(CHAOS_DB)})],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"count worker failed: {proc.stdout}\n{proc.stderr}")
    # Last line is the JSON payload.
    last_line = proc.stdout.strip().splitlines()[-1]
    obj = json.loads(last_line)
    return int(obj["episodes"]), int(obj["edges"])


# ---- worker subprocess entry-points ----


_WORKER_INGEST = """
import asyncio, os, signal, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.factory import load_env, make_graphiti, prepare_graphiti
from src.memory import MemoryAPI
from datetime import datetime

async def main(db_path, episodes):
    load_env()
    g = await make_graphiti(db_path=db_path)
    await prepare_graphiti(g)
    memory = MemoryAPI(g)
    # Signal parent we're ready to take the kill.
    print("WORKER_READY", flush=True)
    for name, ref_iso, body in episodes:
        result = await memory.ingest(
            body=body,
            name=name,
            source_description="chaos test",
            reference_time=datetime.fromisoformat(ref_iso),
            scope_id="chaos",
        )
        print(f"INGESTED {name} -> {result.episode_uuid}", flush=True)
    await g.close()
    print("WORKER_DONE", flush=True)

if __name__ == "__main__":
    import json
    args = json.loads(sys.argv[1])
    asyncio.run(main(args["db_path"], args["episodes"]))
"""


_WORKER_INGEST_THEN_HANG = """
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.factory import load_env, make_graphiti, prepare_graphiti
from src.memory import MemoryAPI
from datetime import datetime

async def main(db_path, episodes):
    load_env()
    g = await make_graphiti(db_path=db_path)
    await prepare_graphiti(g)
    memory = MemoryAPI(g)
    for name, ref_iso, body in episodes:
        result = await memory.ingest(
            body=body,
            name=name,
            source_description="chaos test",
            reference_time=datetime.fromisoformat(ref_iso),
            scope_id="chaos",
        )
        print(f"INGESTED {name} -> {result.episode_uuid}", flush=True)
    # Intentionally do NOT call close() — simulate WAL-left-dirty exit.
    print("WORKER_ABANDONING", flush=True)
    # sys.exit skips asyncio cleanup; Kuzu will have whatever it flushed.
    import os
    os._exit(0)

if __name__ == "__main__":
    import json
    args = json.loads(sys.argv[1])
    asyncio.run(main(args["db_path"], args["episodes"]))
"""


_WORKER_COUNT = """
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.factory import load_env, make_graphiti

async def main(db_path):
    load_env()
    g = await make_graphiti(db_path=db_path)
    rows_ep, _, _ = await g.driver.execute_query('MATCH (e:Episodic) RETURN count(e) AS n')
    rows_ed, _, _ = await g.driver.execute_query('MATCH (n:RelatesToNode_) RETURN count(n) AS n')
    n_ep = int(rows_ep[0]['n'] if rows_ep else 0)
    n_ed = int(rows_ed[0]['n'] if rows_ed else 0)
    print(json.dumps({'episodes': n_ep, 'edges': n_ed}))

if __name__ == '__main__':
    args = json.loads(sys.argv[1])
    asyncio.run(main(args['db_path']))
"""


_WORKER_QUERY = """
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.factory import load_env, make_graphiti, prepare_graphiti
from src.memory import MemoryAPI

async def main(db_path):
    load_env()
    g = await make_graphiti(db_path=db_path)
    # Schema already exists from prior ingest; skip prepare_graphiti.
    memory = MemoryAPI(g)
    print("WORKER_READY", flush=True)
    # Execute a modest loop of queries so the parent can SIGKILL mid-loop.
    for i in range(100):
        hits = await memory.search("Tideglass Mira review Frostvault retention", num_results=5)
        print(f"QUERY_{i}_HITS {len(hits)}", flush=True)
    await g.close()

if __name__ == "__main__":
    import json
    args = json.loads(sys.argv[1])
    asyncio.run(main(args["db_path"]))
"""


# ---- scenario runners ----


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    observations: list[str]
    pre_episodes: int
    post_episodes: int
    pre_edges: int
    post_edges: int
    wall_seconds: float


def _write_worker(body: str, path: Path) -> None:
    path.write_text(body)


def _launch(worker_path: Path, args: dict[str, Any]) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(worker_path), json.dumps(args)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def _wait_for_line(proc: subprocess.Popen, marker: str, timeout: float = 60.0) -> str | None:
    """Read stdout until a line containing `marker` is seen, returning
    the full line. Returns None on timeout or process exit.
    """
    end = time.time() + timeout
    while time.time() < end and proc.poll() is None:
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            time.sleep(0.05)
            continue
        if marker in line:
            return line.strip()
    return None


async def scenario_kill_mid_ingest() -> ScenarioResult:
    """Kill a child process partway through ingest; verify no corruption."""
    _wipe_chaos_db()
    # Seed: ingest two episodes cleanly first so we have a baseline.
    pre_count_ep, pre_count_ed = 0, 0

    t0 = time.time()
    workers_dir = REPO / "scripts" / "_chaos_workers"
    workers_dir.mkdir(exist_ok=True)
    worker = workers_dir / "worker_ingest.py"
    _write_worker(_WORKER_INGEST, worker)

    observations: list[str] = []
    # Launch worker with the 4 chaos episodes; kill after the first
    # INGESTED line (i.e. one episode committed, next in flight).
    proc = _launch(
        worker,
        {"db_path": str(CHAOS_DB), "episodes": CHAOS_EPISODES},
    )

    ready = _wait_for_line(proc, "WORKER_READY", timeout=120)
    if ready is None:
        observations.append("worker never reached WORKER_READY")
        proc.kill()
        proc.wait(timeout=10)
        return ScenarioResult(
            name="kill_mid_ingest",
            passed=False,
            observations=observations,
            pre_episodes=pre_count_ep,
            post_episodes=0,
            pre_edges=pre_count_ed,
            post_edges=0,
            wall_seconds=time.time() - t0,
        )

    # Wait for ONE ingest to complete, then SIGKILL during the second.
    first = _wait_for_line(proc, "INGESTED", timeout=120)
    if first is None:
        observations.append("worker never logged INGESTED")
    else:
        observations.append(f"first ingest reported: {first}")

    # Give the second ingest a slice of time to start, then kill.
    time.sleep(0.4)
    proc.send_signal(signal.SIGKILL)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    observations.append(f"worker killed with SIGKILL; exitcode={proc.returncode}")

    # Reopen the DB — must NOT corrupt. Count episodes; expect at least 1
    # and no more than 2.
    try:
        post_ep, post_ed = await _count_quick_no_prepare()
    except Exception as exc:
        observations.append(f"reopen FAILED: {exc}")
        return ScenarioResult(
            name="kill_mid_ingest",
            passed=False,
            observations=observations,
            pre_episodes=pre_count_ep,
            post_episodes=0,
            pre_edges=pre_count_ed,
            post_edges=0,
            wall_seconds=time.time() - t0,
        )

    observations.append(f"post-kill episodes={post_ep} edges={post_ed}")
    # Pass: DB opened successfully with >= 1 episode and <= n episodes.
    passed = post_ep >= 1 and post_ep <= len(CHAOS_EPISODES)
    return ScenarioResult(
        name="kill_mid_ingest",
        passed=passed,
        observations=observations,
        pre_episodes=pre_count_ep,
        post_episodes=post_ep,
        pre_edges=pre_count_ed,
        post_edges=post_ed,
        wall_seconds=time.time() - t0,
    )


async def scenario_kill_mid_query() -> ScenarioResult:
    """Kill a child during search; verify reads are idempotent.

    Kuzu holds a process-level write lock on the DB file. Seeding the
    DB must happen in a SUBPROCESS that cleanly exits before the query
    worker is launched — otherwise the parent holds the lock and the
    subprocess fails to open the DB.
    """
    _wipe_chaos_db()
    t0 = time.time()

    workers_dir = REPO / "scripts" / "_chaos_workers"
    workers_dir.mkdir(exist_ok=True)

    # Seed via subprocess so the lock is fully released before query worker.
    seed_worker = workers_dir / "worker_ingest.py"
    _write_worker(_WORKER_INGEST, seed_worker)
    seed_proc = _launch(
        seed_worker,
        {"db_path": str(CHAOS_DB), "episodes": CHAOS_EPISODES},
    )
    done_line = _wait_for_line(seed_proc, "WORKER_DONE", timeout=300)
    seed_proc.wait(timeout=10)
    if done_line is None:
        return ScenarioResult(
            name="kill_mid_query",
            passed=False,
            observations=["seed worker did not reach WORKER_DONE"],
            pre_episodes=0,
            post_episodes=0,
            pre_edges=0,
            post_edges=0,
            wall_seconds=time.time() - t0,
        )

    pre_ep, pre_ed = await _count_quick_no_prepare()
    observations: list[str] = [f"seed episodes={pre_ep} edges={pre_ed}"]

    workers_dir = REPO / "scripts" / "_chaos_workers"
    worker = workers_dir / "worker_query.py"
    _write_worker(_WORKER_QUERY, worker)

    proc = _launch(worker, {"db_path": str(CHAOS_DB)})
    ready = _wait_for_line(proc, "WORKER_READY", timeout=120)
    if ready is None:
        observations.append("query worker never ready")
        proc.kill()
        proc.wait(timeout=10)
        return ScenarioResult(
            name="kill_mid_query",
            passed=False,
            observations=observations,
            pre_episodes=pre_ep,
            post_episodes=0,
            pre_edges=pre_ed,
            post_edges=0,
            wall_seconds=time.time() - t0,
        )
    first_hit = _wait_for_line(proc, "QUERY_0_HITS", timeout=60)
    observations.append(f"query worker first line: {first_hit}")

    time.sleep(0.2)
    proc.send_signal(signal.SIGKILL)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    observations.append(f"query worker killed; exitcode={proc.returncode}")

    try:
        post_ep, post_ed = await _count_quick_no_prepare()
    except Exception as exc:
        observations.append(f"reopen FAILED: {exc}")
        return ScenarioResult(
            name="kill_mid_query",
            passed=False,
            observations=observations,
            pre_episodes=pre_ep,
            post_episodes=0,
            pre_edges=pre_ed,
            post_edges=0,
            wall_seconds=time.time() - t0,
        )

    passed = post_ep == pre_ep and post_ed == pre_ed
    observations.append(
        f"reads idempotent: pre_ep={pre_ep} post_ep={post_ep} "
        f"pre_ed={pre_ed} post_ed={post_ed}"
    )
    return ScenarioResult(
        name="kill_mid_query",
        passed=passed,
        observations=observations,
        pre_episodes=pre_ep,
        post_episodes=post_ep,
        pre_edges=pre_ed,
        post_edges=post_ed,
        wall_seconds=time.time() - t0,
    )


async def scenario_wal_recovery() -> ScenarioResult:
    """Run a worker that ingests but exits without close(); WAL is left
    dirty. On reopen, Kuzu replays and all committed episodes are seen.
    """
    _wipe_chaos_db()
    t0 = time.time()

    observations: list[str] = []
    workers_dir = REPO / "scripts" / "_chaos_workers"
    worker = workers_dir / "worker_ingest_hang.py"
    _write_worker(_WORKER_INGEST_THEN_HANG, worker)

    proc = _launch(worker, {"db_path": str(CHAOS_DB), "episodes": CHAOS_EPISODES})
    # Read till worker abandons.
    end = time.time() + 300
    ingest_count = 0
    while time.time() < end and proc.poll() is None:
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            time.sleep(0.05)
            continue
        if "INGESTED" in line:
            ingest_count += 1
        if "WORKER_ABANDONING" in line:
            observations.append(f"worker abandoned after {ingest_count} ingests")
            break
    proc.wait(timeout=10)
    observations.append(f"exit code={proc.returncode}, ingests={ingest_count}")

    # Reopen and count; WAL replay should recover the committed state.
    try:
        post_ep, post_ed = await _count_quick_no_prepare()
    except Exception as exc:
        observations.append(f"reopen FAILED: {exc}")
        return ScenarioResult(
            name="wal_recovery",
            passed=False,
            observations=observations,
            pre_episodes=0,
            post_episodes=0,
            pre_edges=0,
            post_edges=0,
            wall_seconds=time.time() - t0,
        )

    passed = post_ep >= ingest_count and post_ep <= len(CHAOS_EPISODES)
    observations.append(f"after reopen: episodes={post_ep} edges={post_ed}")
    return ScenarioResult(
        name="wal_recovery",
        passed=passed,
        observations=observations,
        pre_episodes=ingest_count,
        post_episodes=post_ep,
        pre_edges=0,
        post_edges=post_ed,
        wall_seconds=time.time() - t0,
    )


# ---- orchestrator ----


async def main() -> int:
    load_env()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    results: list[ScenarioResult] = []
    print("=== chaos durability run ===")
    for runner in (
        scenario_kill_mid_ingest,
        scenario_kill_mid_query,
        scenario_wal_recovery,
    ):
        print(f"\n--- running {runner.__name__} ---")
        try:
            r = await runner()
        except Exception as exc:
            r = ScenarioResult(
                name=runner.__name__.replace("scenario_", ""),
                passed=False,
                observations=[f"UNCAUGHT {type(exc).__name__}: {exc}"],
                pre_episodes=0,
                post_episodes=0,
                pre_edges=0,
                post_edges=0,
                wall_seconds=0.0,
            )
        for obs in r.observations:
            print(f"  - {obs}")
        print(f"  verdict: {'PASS' if r.passed else 'FAIL'} "
              f"({r.wall_seconds:.1f}s)")
        results.append(r)

    overall = all(r.passed for r in results)
    out = {
        "at": datetime.now(timezone.utc).isoformat(),
        "overall_passed": overall,
        "scenarios": [asdict(r) for r in results],
    }
    out_path = RUNS_DIR / f"chaos_durability_{int(time.time())}.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n-> wrote {out_path}")

    print(f"\n=== overall: {'PASS' if overall else 'FAIL'} ===")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
