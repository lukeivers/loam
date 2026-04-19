# IPC p95 Latency Measurement (D4 addendum)

Two measurements were captured in-test and verified against the
brief's acceptance criteria:

## D3: ping/pong round-trip (<10 ms target)

**Test:** `test_d3_ipc.py::test_p95_latency_under_10ms`

- Warm-up: 10 calls
- Sample size: 200 calls
- Transport: Unix-domain socket on local loopback (`/tmp/pos-*.sock`)
- Method: `ping` (minimal handler; no Phase 1 integration)
- Assertion: p95 < 10.0 ms

On the reference machine (Apple M-series, Python 3.13.12), p95
consistently lands under 1 ms. The assertion holds with generous
headroom.

## D4: awareness pull (<100 ms target)

**Test:** `test_d4_monitor_awareness.py::test_awareness_p95_under_100ms`

- Warm-up: none
- Sample size: 100 calls
- Workload: 10 active scopes (representative of the brief's
  "representative workload")
- Transport: Unix-domain socket + BackgroundWorkMonitor snapshot
  on worker thread
- Method: `awareness` (full Phase 1 integration — monitor pulls
  from scope-of-work's authoritative projection)
- Assertion: p95 < 100.0 ms

On the reference machine, p95 is well below 10 ms — a full order of
magnitude under the brief's ceiling. The 100 ms figure exists as a
*ceiling*, not a target; the ceiling is important because the
cache-fallback code path must be exercisable in production if a
slow day happens.

## Cache-fallback behaviour (cache-fallback ceiling test)

**Test:** `test_d4_monitor_awareness.py::test_awareness_cache_fallback_on_timeout`

The cache path is verified by forcing the monitor to sleep 50 ms
with a configured ceiling of 1 ms. The result is `stale: true` with
a numeric `cache_age_ms` — this is the cache fallback Luke approved
as the hard-ceiling policy.

## Reproducing

```bash
source .venv/bin/activate
cd orchestrator
pytest tests/test_d3_ipc.py::test_p95_latency_under_10ms -v
pytest tests/test_d4_monitor_awareness.py::test_awareness_p95_under_100ms -v
```

Raw sample files from the most recent test run are written to
`$tmp_path/ipc_latency_samples.txt` and
`$tmp_path/awareness_latency_samples.txt` (test-scoped temp dirs).
