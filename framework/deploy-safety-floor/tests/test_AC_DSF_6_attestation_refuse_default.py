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

"""AC.DSF.6 — attestation gate + refuse-all-destructive default (F-0/G1
framework-side).

An environment marked ``is_production`` / ``tier: real-infra`` with no
attestation record, or a stale one, refuses every destructive verb and
surfaces, in plain words, that it is not yet protected. (The record is
populated by deploy-tier provider probes — out of scope; the DEFAULT POSTURE
and the refusal are in scope and enforced here.)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.deploy_safety_floor.attestation import parse_attestations
from loam.deploy_safety_floor.config import parse_deploy_config
from loam.deploy_safety_floor.gate import evaluate_bash


_CONFIG = """\
environments:
  - name: prod
    id: 01J9ZPROD0000000000000001
    is_production: true
    tier: real-infra
    reversible: false
    gate: high
    security_profile: prod
    identities:
      hosts: [db.prod.internal]
active: prod
"""

_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)

_DESTRUCTIVE_VERBS = (
    "psql -h db.prod.internal -c 'DROP DATABASE orders'",
    "psql -h db.prod.internal -c 'TRUNCATE TABLE orders'",
    "psql -h db.prod.internal -c 'DELETE FROM orders'",
    "terraform destroy -auto-approve",
    "aws s3 rb s3://acme-prod-data --force",
    "kubectl delete deployment api",
    "rm -rf /srv/data",
)

from loam.deploy_safety_floor.attestation import AttestationStore  # noqa: E402


def test_no_record_refuses_every_destructive_verb() -> None:
    cfg = parse_deploy_config(_CONFIG)
    store = AttestationStore(records=())
    for command in _DESTRUCTIVE_VERBS:
        decision = evaluate_bash(command, cfg, store, _NOW)
        assert decision.denied is True, command
        # Plain-words "not yet protected" surfaced.
        assert "not yet confirmed safe" in decision.reason or "confirmed safe" in decision.reason


def test_stale_record_refuses() -> None:
    cfg = parse_deploy_config(_CONFIG)
    # attested 2 days ago, TTL 1 day -> stale.
    stale_at = (_NOW - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    store = parse_attestations(
        f"""\
attestations:
  - environment_id: 01J9ZPROD0000000000000001
    attested_at: {stale_at}
    ttl_seconds: 86400
    probes:
      - name: deletion_protection
        passed: true
"""
    )
    decision = evaluate_bash(
        "psql -h db.prod.internal -c 'DROP DATABASE orders'", cfg, store, _NOW
    )
    assert decision.denied is True
    assert "expired" in decision.reason


def test_fresh_all_probes_passed_record_allows_floor() -> None:
    """A fresh, all-probes-passed record lifts the floor's default refusal —
    the deploy tier owns the approval above the floor; the floor's job is the
    default-refuse, not the approval."""
    cfg = parse_deploy_config(_CONFIG)
    fresh_at = _NOW.isoformat().replace("+00:00", "Z")
    store = parse_attestations(
        f"""\
attestations:
  - environment_id: 01J9ZPROD0000000000000001
    attested_at: {fresh_at}
    ttl_seconds: 86400
    probes:
      - name: deletion_protection
        passed: true
"""
    )
    decision = evaluate_bash(
        "psql -h db.prod.internal -c 'DROP DATABASE orders'", cfg, store, _NOW
    )
    assert decision.denied is False


def test_fresh_record_with_a_failed_probe_still_refuses() -> None:
    cfg = parse_deploy_config(_CONFIG)
    fresh_at = _NOW.isoformat().replace("+00:00", "Z")
    store = parse_attestations(
        f"""\
attestations:
  - environment_id: 01J9ZPROD0000000000000001
    attested_at: {fresh_at}
    ttl_seconds: 86400
    probes:
      - name: deletion_protection
        passed: false
"""
    )
    decision = evaluate_bash(
        "psql -h db.prod.internal -c 'DROP DATABASE orders'", cfg, store, _NOW
    )
    assert decision.denied is True
    assert "failing" in decision.reason


def test_non_destructive_command_is_not_refused() -> None:
    cfg = parse_deploy_config(_CONFIG)
    decision = evaluate_bash(
        "psql -h db.prod.internal -c 'SELECT count(*) FROM orders'",
        cfg,
        AttestationStore(records=()),
        _NOW,
    )
    assert decision.denied is False
