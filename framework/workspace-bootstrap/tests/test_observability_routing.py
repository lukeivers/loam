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

"""B21 — bootstrap's `loam.bootstrap.*` spans flow through the
observability aggregator's registered TracerProvider.

We verify:

  1. The aggregator spool file receives span output after bootstrap
     completes.
  2. Bootstrap emits the expected span events:
     contribution_started, contribution_completed, phase_complete.

The OpenTelemetry global TracerProvider is process-wide and cannot
be overridden once set. To avoid cross-test contamination (the first
test in the process "wins" the provider), this test runs in a
subprocess so it gets a fresh global.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml


_PY = sys.executable


def test_B21_bootstrap_spans_land_in_aggregator(tmp_path: Path) -> None:
    spool = tmp_path / "data" / "aggregator" / "spans.jsonl"

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "observability.yaml").write_text(
        yaml.safe_dump({"spool_path": str(spool), "service_name": "pos-test"})
    )

    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": ["observability_aggregator"],
    }
    (tmp_path / "bootstrap.yaml").write_text(yaml.safe_dump(manifest))

    manifest_path = tmp_path / "bootstrap.yaml"
    script = textwrap.dedent(
        f"""
        import asyncio
        from loam.workspace_bootstrap import Bootstrapper, load_manifest

        async def main():
            bs = Bootstrapper(load_manifest({str(manifest_path)!r}))
            try:
                await bs.start()
            finally:
                await bs.shutdown()

        asyncio.run(main())
        """
    )

    result = subprocess.run(
        [_PY, "-c", script],
        capture_output=True,
        timeout=30,
        text=True,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )

    # Spool should now have span JSON lines.
    assert spool.exists(), f"aggregator spool not created at {spool}"
    lines = [
        json.loads(ln) for ln in spool.read_text().splitlines() if ln.strip()
    ]
    assert len(lines) > 0, "no spans landed in aggregator spool"

    all_event_names: list[str] = []
    for record in lines:
        events = record.get("events") or []
        for ev in events:
            name = ev.get("name")
            if name:
                all_event_names.append(name)

    expected = {
        "loam.bootstrap.contribution_started",
        "loam.bootstrap.contribution_completed",
        "loam.bootstrap.phase_complete",
    }
    missing = expected - set(all_event_names)
    assert not missing, (
        f"missing bootstrap span events: {missing}; "
        f"observed: {sorted(set(all_event_names))}"
    )
