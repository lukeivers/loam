# Measurement: drain + symlink-swap timing

Captured on the test machine (macOS, APFS, Python 3.13.12) at build
time. Test: `tests/test_orchestrator_control.py::test_symlink_swap_timing_measurement`.

## Symlink swap

400 samples (`atomic_symlink_swap` alternating between two release
dirs under `tmp_path`):

| metric | value |
|--------|-------|
| p50    | **0.168 ms** |
| p99    | **0.414 ms** |

The primitive is `os.symlink` + `os.replace` — both are single
filesystem operations on POSIX. APFS's `rename(2)` guarantees
atomicity. The p99 is dominated by filesystem cache pressure, not by
the swap itself.

## Bounded drain

`wait_for_drain` with 50 ms poll interval and a drain-true counter
reaching 5: took 223 ms wall-clock (4 polls × 50 ms + the last
check's return).

## What these mean for the overall upgrade

The framework's total duration is dominated by:

1. Pre-upgrade snapshot (substrate byte-copies) — scales with DB
   size; Kuzu memory at 1 GB projects to 5–20 s on SSD per research.
2. Pre-upgrade probe — seconds at realistic probe counts.
3. Drain window — bounded, default 30 s.
4. SIGTERM + orchestrator exit — seconds.
5. Symlink swap — negligible (< 1 ms).
6. launchctl kickstart + boot — 5–15 s per the orchestrator's
   measurement doc.
7. Post-upgrade probe + clause verify — seconds.

So the swap itself is not the bottleneck — the bottlenecks are the
snapshot (substrate size) and the orchestrator boot cycle. Both are
bounded by the component layer; the framework does not add
measurable overhead to either.
