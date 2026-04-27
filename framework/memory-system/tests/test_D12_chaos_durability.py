"""D12 — Kuzu chaos-durability split pytest (amendment #16).

D12 is a named acceptance criterion in ``docs/rebuild/components/
memory-system/brief-full-build.md`` (lines ~110-119):

  - Kill-mid-ingest scenarios produce clean-rollback or recoverable-WAL
    state; never corrupted.
  - Kill-mid-query scenarios produce no state change (reads are
    idempotent).
  - WAL-recovery scenarios confirm state is restored to the last
    successful commit on restart.

The runner at ``memory-system/scripts/chaos_durability.py`` exercises
all three scenarios end-to-end with real subprocesses + SIGKILL. Its
2026-04-18 baseline run (``memory-system/docs/chaos-durability-report.
md``) shows all three passing. But per ODD §8.2 rule 9 a standalone
runner script is not a regression surface — the test suite must be
able to re-prove the AC.

This module splits D12 into two buckets per prior Luke ruling
("option c — split"):

  (A) Fast bucket — default-on, in-process assertions that protect
      the durability-adjacent config surface against silent
      regression. Every ``pytest memory-system/`` run executes these.

  (B) Slow bucket — marked ``@pytest.mark.slow`` (registered in
      ``memory-system/tests/conftest.py``). Invokes the full chaos
      runner and asserts ``overall_passed is True`` plus per-scenario
      verdicts by parsing the runner's JSON report. Skipped by
      default; runs under ``pytest -m slow``. Runtime ~65s.

Cadence for the slow bucket is documented in
``docs/rebuild/plans/d12-chaos-durability-split-pytest.md`` §6: run
manually before any pos-v2 release cut, AND on any PR whose diff
touches ``memory-system/src/factory.py``,
``memory-system/src/retention.py``, or kuzu-adjacent surfaces in
``memory-system/src/``. Runbook:
``cd memory-system && .venv/bin/pytest -m slow tests/
test_D12_chaos_durability.py -v``.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
import tempfile
from pathlib import Path

import pytest


MEMORY_SYSTEM = Path(__file__).resolve().parent.parent
# The runner lives under ``scripts/`` which is not an importable
# package by default. ``chaos_durability.py`` itself does the same
# ``sys.path.insert`` trick at module top; mirror it here so the slow
# test can ``import chaos_durability`` without subprocess.
_SCRIPTS_DIR = MEMORY_SYSTEM / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

RUNS_DIR = MEMORY_SYSTEM / "data" / "runs"


# =====================================================================
# Fast bucket (default-on) — durability-config regression guards
# =====================================================================


def test_D12_kuzu_driver_factory_initialises_database_attribute() -> None:
    """``make_kuzu_driver`` initialises ``_database`` to the empty
    string, matching ``get_default_group_id(KUZU)``.

    Ties to all three D12 sub-behaviours: ``_database`` is the
    workaround that prevents ``Graphiti.add_episode`` from cloning the
    driver per-group_id (graphiti-core 0.28.2 bug #1). A cloned driver
    points at a separate Kuzu handle, which breaks the single-writer
    invariant the durability posture rests on — with two writers, the
    WAL-replay and kill-mid-ingest guarantees no longer hold.

    This is the necessary-and-sufficient precondition for D12's
    ``kuzu_db_chaos`` single-writer scenarios.
    """
    from src import factory

    driver = factory.make_kuzu_driver(db_path=":memory:")

    assert hasattr(driver, "_database")
    assert driver._database == ""


@pytest.mark.asyncio
async def test_D12_kuzu_driver_factory_wires_build_indices_override() -> None:
    """``make_kuzu_driver`` replaces ``build_indices_and_constraints``
    with an idempotent closure that routes through ``_graph_ops`` and
    swallows "already exists" errors from re-runs.

    Ties to D12's kill-mid-query and WAL-recovery scenarios. The
    scenarios run real search queries after reopening the DB post-
    kill; without the FTS-index override, graphiti-core's upstream
    ``pass`` no-op would leave the query worker Binder-exception-ing
    before the SIGKILL, invalidating the "reads idempotent" assertion.
    Idempotency matters because reopen-after-WAL-replay retriggers
    index build; a non-idempotent wiring would fail the second open
    and break the WAL-recovery scenario's reopen step.
    """
    from src import factory

    driver = factory.make_kuzu_driver(db_path=":memory:")

    # The override is a closure (has __closure__); the upstream ``pass``
    # no-op would be a plain coroutine function with no closure.
    assert driver.build_indices_and_constraints.__closure__ is not None

    # Source must reference the FTS-index wiring the durability
    # scenarios depend on.
    src = inspect.getsource(driver.build_indices_and_constraints)
    assert "get_fulltext_indices" in src
    assert "already exists" in src  # the idempotent-swallow branch

    # Idempotency proof: two sequential calls both succeed on the
    # same driver. On the second call, Kuzu raises "index already
    # exists" Binder exceptions; the override swallows them.
    await driver.build_indices_and_constraints()
    await driver.build_indices_and_constraints()


@pytest.mark.asyncio
async def test_D12_prepare_graphiti_wires_retention_column_hook() -> None:
    """``prepare_graphiti`` imports and awaits ``ensure_retention_
    column`` — the hook that adds the D10 ``retention_class`` column
    to the Episodic table.

    Ties to D12's kill-mid-ingest scenario. The scenario reopens the
    chaos DB after SIGKILL and runs ``MATCH (e:Episodic) RETURN ...``
    via the count worker; if the retention-column hook were missing
    from ``prepare_graphiti``, an ingest-mid-kill on a fresh DB could
    leave the Episodic table without the ``retention_class`` column,
    and subsequent opens that try to write via ``MemoryAPI.ingest``
    (which tags episodes with their retention class) would fail. The
    hook being wired AND idempotent is the necessary-and-sufficient
    precondition for D12's reopen-counts-episodes verification.
    """
    from src import factory
    from src.retention import ensure_retention_column

    # Static wiring proof: the function's source body names the hook.
    src = inspect.getsource(factory.prepare_graphiti)
    assert "ensure_retention_column" in src

    # Runtime idempotency proof: two sequential calls on the same
    # driver both succeed. Uses a tempdir-backed Kuzu DB because
    # ALTER TABLE on ``:memory:`` has edge-case persistence behaviour
    # across Kuzu versions; the realistic durability posture operates
    # on a file-backed DB.
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "kuzu_d12_test"
        driver = factory.make_kuzu_driver(db_path=str(db_path))
        await driver.build_indices_and_constraints()
        await ensure_retention_column(driver)
        await ensure_retention_column(driver)  # idempotent


# =====================================================================
# Slow bucket (marked) — full chaos-runner invocation
# =====================================================================


def _claude_oauth_available() -> bool:
    """Environment precondition for the full runner: the ``claude``
    CLI must be installed AND OAuth-authenticated.

    The runner's worker subprocesses call ``make_graphiti`` which
    constructs a ``ClaudePrintLLMClient`` and probes OAuth state at
    construction (``ClaudeUnauthenticatedError`` otherwise). This is
    a runner-precondition, not a D12 sub-behaviour; absence of auth
    yields a test skip with a clear reason rather than a false
    failure. On Luke's authenticated workstation the probe passes and
    the scenarios run to completion.
    """
    try:
        from src.factory import make_claude_print_client

        asyncio.run(make_claude_print_client())
        return True
    except Exception:
        return False


@pytest.mark.slow
def test_D12_chaos_durability_runner_reports_all_scenarios_pass() -> None:
    """Invoke the full chaos-durability runner and assert all three
    scenarios pass + the runner's JSON report shape matches D12's AC.

    This test re-proves D12's full AC end-to-end:
      - kill-mid-ingest: clean-rollback or recoverable-WAL, never
        corrupted (runner verifies via reopen-and-count).
      - kill-mid-query: reads idempotent across SIGKILL-mid-query
        (runner verifies pre/post counts match).
      - wal-recovery: reopen after dirty exit replays committed state
        (runner verifies via reopen-and-count after os._exit(0)).

    Runtime ~65s on 2026-04-18 reference hardware. Excluded from
    default pytest run via ``@pytest.mark.slow``; invoke via
    ``pytest -m slow``.

    Invocation shape: imports the runner as a module (no subprocess;
    module-level side effects are limited to the runner's own
    ``sys.path.insert`` + factory imports — verified at amendment-
    plan time) and calls ``chaos_durability.main()`` directly. The
    runner writes a JSON report to ``data/runs/chaos_durability_<ts>.
    json``; we locate the newest report (mtime-sorted) and parse it.

    Precondition: ``claude`` CLI + OAuth (required by the runner's
    worker subprocesses which construct a full Graphiti with the
    subscription-routed LLM client). If auth is absent, the test
    skips — the auth-precondition is not a D12 sub-behaviour.
    """
    if not _claude_oauth_available():
        pytest.skip(
            "claude CLI OAuth not available in this environment; the "
            "runner's worker subprocesses require authentication. Run "
            "this test on Luke's authenticated workstation. D12's AC "
            "covers Kuzu durability, not LLM auth."
        )

    import chaos_durability  # noqa: E402 — sys.path prep above

    exit_code = asyncio.run(chaos_durability.main())
    assert exit_code == 0, "runner's main() exit-code convention: 0 == overall pass"

    # Locate the newest report. Ties broken by mtime (the runner uses
    # ``int(time.time())`` as the filename suffix, so lexical sort is
    # temporal at second granularity; mtime is the tiebreaker).
    reports = sorted(
        RUNS_DIR.glob("chaos_durability_*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    assert reports, f"runner produced no report under {RUNS_DIR}"
    latest = reports[-1]
    payload = json.loads(latest.read_text())

    # Shape assertions tie the report 1:1 to D12's three named
    # sub-behaviours — no more, no less (ODD §8.2 rule 9).
    assert payload["overall_passed"] is True, (
        f"overall verdict FAIL in {latest.name}: {payload}"
    )
    scenario_names = {s["name"] for s in payload["scenarios"]}
    assert scenario_names == {"kill_mid_ingest", "kill_mid_query", "wal_recovery"}, (
        f"unexpected scenario set: {scenario_names}"
    )
    for s in payload["scenarios"]:
        assert s["passed"] is True, (
            f"scenario {s['name']} FAILED: {s.get('observations')}"
        )
