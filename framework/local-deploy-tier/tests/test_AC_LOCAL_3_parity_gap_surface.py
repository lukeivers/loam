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

"""AC.LOCAL.3 — when the LOCAL backing service differs from a downstream env's,
the divergence is surfaced in PLAIN LANGUAGE before any promotion is offered.

A SQLite-local vs Postgres-downstream engine gap, and a version gap, each show
up as an owner-facing sentence; a matching service produces no gap; the honest
residual caveat is always present (a clean diff never over-claims parity)."""

from __future__ import annotations

from loam.local_deploy_tier.local_config import BackingService, EnvProfile
from loam.local_deploy_tier.parity import (
    RESIDUAL_PARITY_CAVEAT,
    compute_parity_gaps,
    parity_report,
)


def _env(name: str, tier: str, services: tuple[BackingService, ...]) -> EnvProfile:
    return EnvProfile(name=name, tier=tier, role=None, backing_services=services)


def test_engine_divergence_is_surfaced_in_plain_language() -> None:
    """SQLite local vs Postgres downstream — the classic silent parity break —
    is named in the owner's words, not as a raw config diff."""
    local = _env("dev", "local", (BackingService("db", "sqlite"),))
    prod = _env("prod", "staging", (BackingService("db", "postgres", "16.3"),))
    report = parity_report(local, prod)
    assert report.has_gaps
    gap = next(g for g in report.gaps if g.service == "db")
    assert gap.axis == "engine"
    summary = report.plain_language_summary().lower()
    assert "sqlite" in summary and "postgres" in summary
    # Plain words, not a unified-diff / YAML dump.
    assert "---" not in summary and "+++" not in summary


def test_version_divergence_is_surfaced() -> None:
    """Same engine, different pinned version — a real parity risk — is named."""
    local = _env("dev", "local", (BackingService("db", "postgres", "14.2"),))
    prod = _env("prod", "staging", (BackingService("db", "postgres", "16.3"),))
    gaps = compute_parity_gaps(local.backing_services, prod.backing_services)
    assert len(gaps) == 1
    assert gaps[0].axis == "version"
    assert "14.2" in gaps[0].plain_language and "16.3" in gaps[0].plain_language


def test_unpinned_latest_never_silently_matches_a_pinned_version() -> None:
    """``latest`` is a silent parity break — it must NOT read as equal to a
    pinned tag (research §3 rule 1)."""
    local = _env("dev", "local", (BackingService("db", "postgres", "latest"),))
    prod = _env("prod", "staging", (BackingService("db", "postgres", "16.3"),))
    gaps = compute_parity_gaps(local.backing_services, prod.backing_services)
    assert len(gaps) == 1
    assert gaps[0].axis == "version"


def test_missing_service_on_either_side_is_a_gap() -> None:
    local = _env("dev", "local", (BackingService("db", "postgres", "16.3"),))
    prod = _env(
        "prod", "staging",
        (BackingService("db", "postgres", "16.3"), BackingService("cache", "redis", "7")),
    )
    gaps = compute_parity_gaps(local.backing_services, prod.backing_services)
    assert len(gaps) == 1
    assert gaps[0].service == "cache"
    assert gaps[0].axis == "missing-local"


def test_matching_services_produce_no_gap_but_keep_the_honest_caveat() -> None:
    """A clean diff is genuinely clean — AND still carries the caveat that a
    local machine is never identical to the live setup (no over-claim)."""
    local = _env("dev", "local", (BackingService("db", "postgres", "16.3"),))
    prod = _env("prod", "staging", (BackingService("db", "postgres", "16.3"),))
    report = parity_report(local, prod)
    assert report.has_gaps is False
    assert report.caveat == RESIDUAL_PARITY_CAVEAT
    assert RESIDUAL_PARITY_CAVEAT in report.plain_language_summary()
