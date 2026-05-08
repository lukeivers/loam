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

"""D8 — `pos obs` CLI."""
from __future__ import annotations

import io
import json
import time
from contextlib import redirect_stdout
from datetime import datetime, timezone

import pytest

from loam.observability_aggregator import open_store
from loam.observability_aggregator.cli import main as cli_main
from loam.observability_aggregator.config import AggregatorConfig
from loam.observability_aggregator.schema import (
    AuditRecord,
    SpanRecord,
    TokenRecord,
)


def _populate(cfg: AggregatorConfig):
    store = open_store(cfg)
    try:
        now_ns = int(time.time() * 1e9)
        store.insert_span(SpanRecord(
            trace_id="t" * 32, span_id="a" * 16, name="cli_probe_op",
            tracer_name="loam.scope_of_work", component="scope_of_work",
            start_time_unix_nano=now_ns, end_time_unix_nano=now_ns + 1000,
            attributes={"loam.scope.id": "cli_scope"},
        ))
        store.insert_audit(AuditRecord(
            at_time=datetime.now(timezone.utc), operation="cli_op",
            actor="memory_system", scope_id="cli_scope", rationale="cli rationale",
        ))
        store.insert_token(TokenRecord(
            prompt_name="cli_prompt", model="claude",
            input_tokens=100, output_tokens=50, call_count=1,
            at_time=datetime.now(timezone.utc), component="memory_system",
        ))
    finally:
        store.close()


def _run_cli(argv: list[str]) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(argv)
    assert rc == 0
    return buf.getvalue()


@pytest.fixture
def populated(tmp_config):
    _populate(tmp_config)
    return tmp_config


def _common_args(cfg: AggregatorConfig) -> list[str]:
    return ["--db", str(cfg.resolved_db_path()), "--substrate", cfg.substrate]


def test_cli_find_spans(populated):
    out = _run_cli([*_common_args(populated), "find-spans", "--component", "scope_of_work"])
    data = json.loads(out)
    assert isinstance(data, list)
    assert any(d["span_id"] == "a" * 16 for d in data)


def test_cli_get_span(populated):
    out = _run_cli([*_common_args(populated), "get-span", "a" * 16])
    data = json.loads(out)
    assert data["name"] == "cli_probe_op"


def test_cli_get_trace(populated):
    out = _run_cli([*_common_args(populated), "get-trace", "t" * 32])
    data = json.loads(out)
    assert any(d["span_id"] == "a" * 16 for d in data)


def test_cli_cost_by_prompt(populated):
    out = _run_cli([*_common_args(populated), "cost-by-prompt"])
    data = json.loads(out)
    assert "cli_prompt" in data
    assert data["cli_prompt"]["input_tokens"] == 100


def test_cli_audit_search(populated):
    out = _run_cli([*_common_args(populated), "audit-search", "--operation", "cli_op"])
    data = json.loads(out)
    assert any(d["operation"] == "cli_op" for d in data)


def test_cli_replay_scope(populated):
    out = _run_cli([*_common_args(populated), "replay-scope", "cli_scope"])
    data = json.loads(out)
    assert data["scope_id"] == "cli_scope"
    # Output should have spans listed.
    assert "spans" in data


def test_cli_why_invokes_nl(populated):
    out = _run_cli([*_common_args(populated), "why", "show me scope spans"])
    data = json.loads(out)
    assert "summary" in data
    assert "cited_span_ids" in data


def test_cli_raw_flag_produces_single_line(populated):
    out = _run_cli([*_common_args(populated), "--raw", "find-spans"])
    # Single line of JSON, no trailing newlines except the print.
    assert out.count("\n") == 1
