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

"""AC.DSF.2 — classifier keys off the resolved target; gate = max(declared,
resolved) (G2).

A destructive command resolved against a target matching the config's
declared-prod identity (host/bucket/account) is gated at the prod level EVEN
WHEN the active environment is declared non-prod; gate strength is shown to
derive from ``max(declared, resolved)``, never the declared label alone.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loam.deploy_safety_floor.attestation import AttestationStore
from loam.deploy_safety_floor.classifier import compute_gate_strength
from loam.deploy_safety_floor.config import GateLevel, parse_deploy_config
from loam.deploy_safety_floor.gate import evaluate_bash


# Active env is the LOCAL (non-prod, gate: none) one; prod declares a host
# identity. A command pointing at the prod host while "in" local must still
# be prod-gated.
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
  - name: local
    id: 01J9ZLOCAL000000000000002
    is_production: false
    tier: local
    reversible: true
    gate: none
    security_profile: dev
active: local
"""

_NOW = datetime(2026, 6, 27, tzinfo=timezone.utc)


def test_resolved_prod_target_raises_gate_to_high_despite_nonprod_active() -> None:
    cfg = parse_deploy_config(_CONFIG)
    command = "psql -h db.prod.internal -c 'DROP DATABASE orders'"
    strength = compute_gate_strength(command, cfg)

    # Declared protection comes from the active (local) env: none.
    assert strength.declared == GateLevel.none
    # The resolved target matches the declared-prod host -> production-ness high.
    assert strength.resolved == GateLevel.high
    # Effective gate is the MAX of the two — prod-gated.
    assert strength.effective == GateLevel.high
    assert strength.is_production_gated is True
    assert strength.resolved_environment is not None
    assert strength.resolved_environment.name == "prod"


def test_command_with_no_declared_target_stays_at_declared_level() -> None:
    cfg = parse_deploy_config(_CONFIG)
    command = "psql -h localhost -c 'DROP DATABASE scratch'"
    strength = compute_gate_strength(command, cfg)
    assert strength.resolved == GateLevel.none
    assert strength.effective == GateLevel.none
    assert strength.is_production_gated is False


def test_prod_resolved_destructive_is_denied_when_unattested() -> None:
    """The resolved-prod gate is enforced end-to-end: a destructive command
    on the prod host, with no attestation, is denied even from the non-prod
    active env."""
    cfg = parse_deploy_config(_CONFIG)
    command = "psql -h db.prod.internal -c 'DROP DATABASE orders'"
    decision = evaluate_bash(command, cfg, AttestationStore(records=()), _NOW)
    assert decision.denied is True
    assert decision.gate_strength is not None
    assert decision.gate_strength.effective == GateLevel.high
    assert decision.target_environment is not None
    assert decision.target_environment.name == "prod"
