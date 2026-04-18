"""D9 demo — upgrade-fidelity harness against a single memory instance.

Rather than actually upgrading graphiti-core (we've pinned 0.28.2),
this demo exercises the harness surface:

  1. Ingest episodes (pre-upgrade state).
  2. Snapshot the Kuzu DB via `upgrade.snapshot()`.
  3. Run the probe set pre-upgrade (`pre_results`).
  4. Simulate the upgrade as a no-op (same DB state).
  5. Run the probe set post-upgrade (`post_results`).
  6. Compare — a no-op upgrade should produce zero verdict flips.

This verifies the harness machinery itself. A real framework upgrade
will plug into the same machinery: snapshot pre-upgrade, run the pOS
upgrade commands, open post-upgrade memory, run probes, compare.

Acceptance per brief D9:
- Pass/fail drift report against declared threshold.
- Snapshot captured pre-upgrade for physical reversibility.
- Harness pin'd to the Luke-approved probe set (test_set.json).

Writes: data/runs/upgrade_harness_<ts>.json
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti, prepare_graphiti  # noqa: E402
from src.memory import MemoryAPI  # noqa: E402
from src.observability import Emitter, reset_default_emitter  # noqa: E402
from src.scope import MockScopeSource  # noqa: E402
from src import upgrade  # noqa: E402


REPO = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO / "data" / "runs"
EPISODES_FILE = REPO / "data" / "episodes.json"
TEST_SET_FILE = REPO / "data" / "test_set.json"


def _wipe_db(db_path: Path) -> None:
    for sib in db_path.parent.glob(db_path.name + "*"):
        try:
            if sib.is_file(): sib.unlink()
            elif sib.is_dir(): shutil.rmtree(sib, ignore_errors=True)
        except OSError:
            pass


async def build_memory(db_path: Path, scope_registry: Path, emitter: Emitter) -> tuple:
    scope_source = MockScopeSource(registry_path=scope_registry)
    g = await make_graphiti(db_path=str(db_path))
    await prepare_graphiti(g)
    memory = MemoryAPI(g, scope_source=scope_source, emitter=emitter)
    return g, memory


async def main() -> int:
    load_env()

    obs_dir = REPO / "data" / "observability_upgrade"
    obs_dir.mkdir(parents=True, exist_ok=True)
    for f in obs_dir.glob("*.jsonl"):
        f.unlink()
    emitter = Emitter(sink_dir=obs_dir)
    reset_default_emitter(emitter)

    db_path = REPO / "data" / "kuzu_db_upgrade"
    registry_path = REPO / "data" / "scope_registry_upgrade.json"
    if registry_path.exists():
        registry_path.unlink()

    # First run: ingest a limited seed to keep demo fast (first 8 episodes).
    # The harness is independent of the probe set size or ingest volume.
    _wipe_db(db_path)
    g, memory = await build_memory(db_path, registry_path, emitter)

    episodes = json.loads(EPISODES_FILE.read_text())[:8]
    probe_set = json.loads(TEST_SET_FILE.read_text())

    print(f"ingesting {len(episodes)} episodes...")
    for ep in episodes:
        scope_id = f"aldermere_{ep['engagement']}"
        ref = datetime.fromisoformat(ep["reference_time"])
        await memory.ingest(
            body=ep["body"],
            name=ep["name"],
            source_description=f"synthetic episode {ep['id']}",
            reference_time=ref,
            scope_id=scope_id,
            retention_class="normal",
        )

    print("running pre-upgrade probe set...")
    pre_results = await upgrade.run_probe_set(memory, probe_set=probe_set)
    print(f"  pre: {sum(1 for r in pre_results if r.passed)}/{len(pre_results)} pass")

    # Pre-upgrade snapshot.
    await g.close()
    # Small sleep to let Kuzu finalise (checkpoint) before we copy files.
    await asyncio.sleep(0.2)
    snap_dir = upgrade.snapshot(str(db_path), tag="pre-upgrade-demo")
    print(f"snapshot captured at {snap_dir}")

    # "Upgrade" is simulated as a no-op: we re-open the same DB.
    # In a real upgrade, this is where `pip install --upgrade graphiti-core`
    # and any schema migrations would run.

    # Spawn a new subprocess to run post-upgrade probe, because Kuzu's
    # close() is a no-op and a second in-process open fails on the lock.
    post_runner = REPO / "scripts" / "_upgrade_probe_runner.py"
    post_runner.write_text(_POST_RUNNER)
    import subprocess
    args = {
        "db_path": str(db_path),
        "scope_registry": str(registry_path),
        "obs_dir": str(obs_dir),
        "test_set_path": str(TEST_SET_FILE),
    }
    proc = subprocess.run(
        [sys.executable, str(post_runner), json.dumps(args)],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        print("post-upgrade runner FAILED:")
        print(proc.stdout[-2000:])
        print(proc.stderr[-2000:])
        return 1
    post_payload = json.loads(proc.stdout.strip().splitlines()[-1])
    post_results_dicts = post_payload["results"]
    # Rehydrate into ProbeResult shape.
    post_results = [
        upgrade.ProbeResult(**r) for r in post_results_dicts
    ]
    print(f"  post: {sum(1 for r in post_results if r.passed)}/{len(post_results)} pass")

    # Compare.
    report = upgrade.compare(pre_results, post_results)
    print(f"\ndrift verdict: {'PASS' if report.passed else 'FAIL'}")
    print(f"  verdict_flip_fraction={report.verdict_flip_fraction}")
    print(f"  over_tolerance_fraction={report.over_tolerance_fraction}")
    print(f"  mean_recall_delta={report.mean_recall_delta}")
    print(f"  mean_precision_delta={report.mean_precision_delta}")

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"upgrade_harness_{int(time.time())}.json"
    out_path.write_text(json.dumps(upgrade.drift_report_to_dict(report), indent=2, default=str))
    print(f"\n-> wrote {out_path}")
    print(f"-> snapshot at {snap_dir}")

    return 0 if report.passed else 1


_POST_RUNNER = """
import asyncio, json, sys
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.factory import load_env, make_graphiti
from src.memory import MemoryAPI
from src.observability import Emitter, reset_default_emitter
from src.scope import MockScopeSource
from src import upgrade

async def main(args):
    load_env()
    emitter = Emitter(sink_dir=args['obs_dir'])
    reset_default_emitter(emitter)
    scope_source = MockScopeSource(registry_path=args['scope_registry'])
    g = await make_graphiti(db_path=args['db_path'])
    memory = MemoryAPI(g, scope_source=scope_source, emitter=emitter)
    probe_set = json.loads(Path(args['test_set_path']).read_text())
    results = await upgrade.run_probe_set(memory, probe_set=probe_set)
    out = {'results': [asdict(r) for r in results]}
    print(json.dumps(out))

if __name__ == '__main__':
    asyncio.run(main(json.loads(sys.argv[1])))
"""


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
