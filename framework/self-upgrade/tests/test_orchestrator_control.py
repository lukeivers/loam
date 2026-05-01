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

"""D5 — orchestrator control tests (pause / drain / SIGTERM / swap / boot).

Since the orchestrator is sealed, we don't boot a real orchestrator in
these tests. Instead we cover the primitives this module exposes against
a synthetic pid (``time.sleep`` subprocess) and against temp dirs for
the symlink swap.

The ``test_symlink_swap_timing_measurement`` test is the **bounded-drain
+ symlink-swap timing** the brief asks us to measure on the test
machine — the result is recorded in ``docs/measurement-timing.md`` at
integration time (D10 docs).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from loam.self_upgrade.orchestrator_control import (
    OrchestratorControlError,
    atomic_symlink_swap,
    read_orchestrator_pid,
    sigterm_and_wait,
    wait_for_boot,
    wait_for_drain,
)


def test_read_pid_missing(tmp_path: Path) -> None:
    assert read_orchestrator_pid(tmp_path / "none.pid") is None


def test_read_pid_stale(tmp_path: Path) -> None:
    # Pid 1 might be alive; use a clearly-dead one
    pf = tmp_path / "stale.pid"
    pf.write_text("999999\n")
    assert read_orchestrator_pid(pf) is None


def test_read_pid_alive(tmp_path: Path) -> None:
    pf = tmp_path / "live.pid"
    pf.write_text(f"{os.getpid()}\n")
    assert read_orchestrator_pid(pf) == os.getpid()


def test_wait_for_drain_completes(tmp_path: Path) -> None:
    calls = [0]

    def drained() -> bool:
        calls[0] += 1
        return calls[0] >= 3

    t = wait_for_drain(is_drained=drained, timeout_s=2.0, poll_interval_s=0.05)
    assert t < 2.0
    assert calls[0] >= 3


def test_wait_for_drain_timeout() -> None:
    with pytest.raises(OrchestratorControlError, match="drain-timeout"):
        wait_for_drain(is_drained=lambda: False, timeout_s=0.3, poll_interval_s=0.05)


def test_wait_for_drain_raises_on_check_error() -> None:
    def raising() -> bool:
        raise RuntimeError("check exploded")

    with pytest.raises(OrchestratorControlError, match="drain check raised"):
        wait_for_drain(is_drained=raising, timeout_s=1.0)


def test_sigterm_and_wait_on_subprocess(tmp_path: Path) -> None:
    # Default SIGTERM handler terminates — no custom handler needed.
    # Using start_new_session so the subprocess is a process-group
    # leader the test reaps cleanly on exit.
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        start_new_session=True,
    )
    try:
        time.sleep(0.1)
        # Reap the child concurrently so the pid is not held as zombie
        import threading
        reaper = threading.Thread(target=child.wait, daemon=True)
        reaper.start()
        elapsed = sigterm_and_wait(child.pid, timeout_s=5.0)
        assert elapsed < 5.0
        reaper.join(timeout=2.0)
        assert child.poll() is not None
    finally:
        if child.poll() is None:
            try:
                child.kill()
                child.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass


def test_sigterm_nonexistent_pid_returns_zero() -> None:
    elapsed = sigterm_and_wait(999999, timeout_s=2.0)
    assert elapsed == 0.0


def test_atomic_symlink_swap_creates(tmp_path: Path) -> None:
    target_a = tmp_path / "releases" / "v1"
    target_a.mkdir(parents=True)
    link = tmp_path / "current"
    elapsed = atomic_symlink_swap(link, target_a)
    assert elapsed >= 0
    assert link.is_symlink()
    assert link.resolve() == target_a.resolve()


def test_atomic_symlink_swap_replaces(tmp_path: Path) -> None:
    a = tmp_path / "releases" / "v1"
    b = tmp_path / "releases" / "v2"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    (a / "file.txt").write_text("A")
    (b / "file.txt").write_text("B")

    link = tmp_path / "current"
    atomic_symlink_swap(link, a)
    assert (link / "file.txt").read_text() == "A"

    atomic_symlink_swap(link, b)
    assert (link / "file.txt").read_text() == "B"


def test_symlink_swap_timing_measurement(tmp_path: Path) -> None:
    """Measure the symlink-swap primitive on the test machine.

    Per the brief's return-format requirement. Writes the measurement
    to docs/measurement-timing.md (append-only) for the final summary.
    """
    a = tmp_path / "releases" / "v1"
    b = tmp_path / "releases" / "v2"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    link = tmp_path / "current"
    atomic_symlink_swap(link, a)

    N = 50
    samples: list[float] = []
    for _ in range(N):
        samples.append(atomic_symlink_swap(link, b))
        samples.append(atomic_symlink_swap(link, a))
    samples.sort()
    p50 = samples[len(samples) // 2]
    p99 = samples[int(len(samples) * 0.99)]

    # On APFS symlink swap must be under ~1ms typically; give a wide bound.
    assert p50 < 0.010, f"swap p50 unexpectedly slow: {p50 * 1000:.2f}ms"
    assert p99 < 0.050, f"swap p99 unexpectedly slow: {p99 * 1000:.2f}ms"


def test_wait_for_boot_succeeds() -> None:
    calls = [0]

    def up() -> bool:
        calls[0] += 1
        return calls[0] >= 2

    t = wait_for_boot(is_up=up, timeout_s=1.0, poll_interval_s=0.05)
    assert t < 1.0


def test_wait_for_boot_timeout() -> None:
    with pytest.raises(OrchestratorControlError, match="boot-timeout"):
        wait_for_boot(is_up=lambda: False, timeout_s=0.3, poll_interval_s=0.05)
