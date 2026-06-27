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

"""AC.DSF.3 — rename-safety preserved.

An environment renamed away from "production" while ``is_production: true``
retains the full prod gate; gate height derives from STRUCTURED fields, not
the name. (Regression guard — the design's existing-correct property must
not break.)
"""

from __future__ import annotations

from datetime import datetime, timezone

from loam.deploy_safety_floor.attestation import AttestationStore
from loam.deploy_safety_floor.classifier import compute_gate_strength
from loam.deploy_safety_floor.config import GateLevel, parse_deploy_config
from loam.deploy_safety_floor.gate import evaluate_bash


# The production environment is named "banana" — nothing in its name says
# "production". Its gate height must come from is_production / tier only.
_RENAMED_CONFIG = """\
environments:
  - name: banana
    id: 01J9ZPROD0000000000000001
    is_production: true
    tier: real-infra
    reversible: false
    gate: high
    security_profile: prod
    identities:
      hosts: [db.banana.internal]
active: banana
"""

# A control: an env literally NAMED "production" but is_production: false and
# tier local — the name must NOT confer a prod gate.
_DECOY_CONFIG = """\
environments:
  - name: production
    id: 01J9ZDECOY000000000000003
    is_production: false
    tier: local
    reversible: true
    gate: none
    security_profile: dev
    identities:
      hosts: [db.decoy.internal]
active: production
"""

_NOW = datetime(2026, 6, 27, tzinfo=timezone.utc)


def test_renamed_prod_env_keeps_full_prod_gate() -> None:
    cfg = parse_deploy_config(_RENAMED_CONFIG)
    env = cfg.by_name("banana")
    assert env is not None
    # Production-ness + gate height come from structured fields, not the name.
    assert env.is_production_class is True
    assert env.declared_gate == GateLevel.high

    command = "psql -h db.banana.internal -c 'DROP DATABASE orders'"
    strength = compute_gate_strength(command, cfg)
    assert strength.effective == GateLevel.high
    decision = evaluate_bash(command, cfg, AttestationStore(records=()), _NOW)
    assert decision.denied is True


def test_name_alone_does_not_confer_a_prod_gate() -> None:
    cfg = parse_deploy_config(_DECOY_CONFIG)
    env = cfg.by_name("production")
    assert env is not None
    assert env.is_production_class is False
    assert env.declared_gate == GateLevel.none

    command = "psql -h db.decoy.internal -c 'DROP DATABASE scratch'"
    strength = compute_gate_strength(command, cfg)
    assert strength.effective == GateLevel.none
    decision = evaluate_bash(command, cfg, AttestationStore(records=()), _NOW)
    assert decision.denied is False
