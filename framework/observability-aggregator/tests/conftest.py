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

"""Shared fixtures."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest
from opentelemetry import trace

from loam.observability_aggregator import AggregatorConfig, open_store
from loam.observability_aggregator.config import IngestConfig, RetentionConfig


@pytest.fixture
def fresh_otel_provider():
    """Reset OTel's global TracerProvider so a test can install its own.

    OTel SDK guards `set_tracer_provider` with a Once primitive — only
    the first call wins, subsequent calls log a warning and noop. In
    production this is correct; in tests we need a fresh provider per
    test.
    """
    # Reset the Once before the test.
    trace._TRACER_PROVIDER_SET_ONCE = threading.Lock().__class__()
    # The Once class lives in opentelemetry.util — easier to instantiate
    # a fresh one of the right type.
    from opentelemetry.util._once import Once
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None
    yield
    # Tear down: reset again so subsequent tests get a fresh provider.
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None


@pytest.fixture
def tmp_config(tmp_path: Path) -> AggregatorConfig:
    return AggregatorConfig(
        base_dir=str(tmp_path),
        substrate="duckdb",
        db_path=str(tmp_path / "obs.duckdb"),
        retention=RetentionConfig(),
        ingest=IngestConfig(
            memory_sink_dir=str(tmp_path / "memory_sinks"),
            spool_path=str(tmp_path / "spool.jsonl"),
        ),
    )


@pytest.fixture
def tmp_config_sqlite(tmp_path: Path) -> AggregatorConfig:
    return AggregatorConfig(
        base_dir=str(tmp_path),
        substrate="sqlite",
        db_path=str(tmp_path / "obs.sqlite"),
        retention=RetentionConfig(),
        ingest=IngestConfig(
            memory_sink_dir=str(tmp_path / "memory_sinks"),
            spool_path=str(tmp_path / "spool.jsonl"),
        ),
    )


@pytest.fixture
def store(tmp_config):
    s = open_store(tmp_config)
    yield s
    s.close()


@pytest.fixture
def store_sqlite(tmp_config_sqlite):
    s = open_store(tmp_config_sqlite)
    yield s
    s.close()
