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

"""Aggregator configuration.

One YAML section in `~/.loam/observability.yaml` or programmatic
config. Every retention knob, storage substrate choice, and ingest
path lives here. Defaults are workspace-tunable per the brief.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml


Substrate = Literal["duckdb", "sqlite"]


# ---- retention defaults (Luke's decaying-granularity pattern) --------
#
# The brief specifies:
#   0-7 days: full fidelity.
#   7-30 days: daily rollup + top-N longest spans kept raw.
#   30-365 days: monthly rollup.
#   365+ days: yearly rollup, or audit-only at a workspace-set cutoff.

DEFAULT_FULL_FIDELITY_DAYS = 7
DEFAULT_DAILY_ROLLUP_END_DAYS = 30
DEFAULT_MONTHLY_ROLLUP_END_DAYS = 365
DEFAULT_TOP_N_RAW_PER_DAY = 20  # Eve-flagged inference, brief notes "sensible default"


@dataclass
class RetentionConfig:
    full_fidelity_days: int = DEFAULT_FULL_FIDELITY_DAYS
    daily_rollup_end_days: int = DEFAULT_DAILY_ROLLUP_END_DAYS
    monthly_rollup_end_days: int = DEFAULT_MONTHLY_ROLLUP_END_DAYS
    audit_cutoff_days: int | None = None  # None => keep yearly forever
    top_n_raw_per_day: int = DEFAULT_TOP_N_RAW_PER_DAY


@dataclass
class IngestConfig:
    memory_sink_dir: str = "./data/observability"
    spool_path: str | None = None  # default derived from base_dir
    batch_size: int = 256
    batch_interval_seconds: float = 2.0
    # Aggregator's own tracer namespace; spans matching are filtered at
    # ingest to prevent observing-its-own-observation recursion.
    self_namespace_prefix: str = "loam.aggregator"


@dataclass
class AggregatorConfig:
    base_dir: str = "~/.loam"
    substrate: Substrate = "duckdb"
    db_path: str | None = None  # default derived from base_dir
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    ingest: IngestConfig = field(default_factory=IngestConfig)

    def resolved_base_dir(self) -> Path:
        return Path(os.path.expanduser(self.base_dir)).resolve()

    def resolved_db_path(self) -> Path:
        if self.db_path:
            return Path(os.path.expanduser(self.db_path)).resolve()
        suffix = ".duckdb" if self.substrate == "duckdb" else ".sqlite"
        return self.resolved_base_dir() / f"observability{suffix}"

    def resolved_spool_path(self) -> Path:
        if self.ingest.spool_path:
            return Path(os.path.expanduser(self.ingest.spool_path)).resolve()
        return self.resolved_base_dir() / "obs_spool.jsonl"

    def resolved_memory_sink_dir(self) -> Path:
        return Path(os.path.expanduser(self.ingest.memory_sink_dir)).resolve()

    def ensure_dirs(self) -> None:
        self.resolved_base_dir().mkdir(parents=True, exist_ok=True)
        self.resolved_db_path().parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AggregatorConfig":
        with open(path, "rt", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, d: dict) -> "AggregatorConfig":
        d = d.get("observability", d)  # accept top-level or nested
        retention_d = d.get("retention", {}) or {}
        ingest_d = d.get("ingest", {}) or {}
        return cls(
            base_dir=d.get("base_dir", "~/.loam"),
            substrate=d.get("substrate", "duckdb"),
            db_path=d.get("db_path"),
            retention=RetentionConfig(**retention_d),
            ingest=IngestConfig(**ingest_d),
        )
