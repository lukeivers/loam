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

"""AC.DSF.1 — the config abstraction is inert, typed policy.

A ``deploy.yaml`` carrying ``is_production`` / ``tier`` / ``reversible`` /
``gate`` / ``security_profile`` / immutable-id per environment parses into a
typed model; an invalid ``tier`` or a missing ``is_production`` is rejected
at load (fail-CLOSED load). The file itself triggers no action — only a gate
reading it does.
"""

from __future__ import annotations

import pytest

from loam.deploy_safety_floor.config import (
    ConfigError,
    GateLevel,
    Tier,
    parse_deploy_config,
)


_VALID = """\
environments:
  - name: prod
    id: 01J9ZQEXAMPLEULID000000001
    is_production: true
    tier: real-infra
    reversible: false
    gate: high
    security_profile: prod
    identities:
      hosts: [db.prod.example.com]
      buckets: ["s3://acme-prod-data"]
      accounts: ["acct-1234567890"]
  - name: local
    id: 01J9ZQEXAMPLEULID000000002
    is_production: false
    tier: local
    reversible: true
    gate: none
    security_profile: dev
active: local
"""


def test_valid_config_parses_into_a_typed_model() -> None:
    cfg = parse_deploy_config(_VALID)
    assert len(cfg.environments) == 2
    prod = cfg.by_name("prod")
    assert prod is not None
    assert prod.is_production is True
    assert prod.tier == Tier.real_infra
    assert prod.reversible is False
    assert prod.gate == GateLevel.high
    assert prod.security_profile == "prod"
    assert prod.id == "01J9ZQEXAMPLEULID000000001"
    assert prod.identities.hosts == ("db.prod.example.com",)
    assert cfg.active_environment() is not None
    assert cfg.active_environment().name == "local"


def test_missing_is_production_is_rejected_at_load() -> None:
    bad = """\
environments:
  - name: prod
    id: 01J9ZQEXAMPLEULID000000001
    tier: real-infra
    reversible: false
    gate: high
    security_profile: prod
"""
    with pytest.raises(ConfigError) as exc:
        parse_deploy_config(bad)
    assert "is_production" in str(exc.value)


def test_invalid_tier_is_rejected_at_load() -> None:
    bad = """\
environments:
  - name: prod
    id: 01J9ZQEXAMPLEULID000000001
    is_production: true
    tier: wherever
    reversible: false
    gate: high
    security_profile: prod
"""
    with pytest.raises(ConfigError) as exc:
        parse_deploy_config(bad)
    assert "tier" in str(exc.value)


def test_unparseable_config_fails_closed_not_to_empty() -> None:
    """A broken policy file raises — it must NOT silently degrade to an empty
    (no-environments) config that would disable the floor."""
    with pytest.raises(ConfigError):
        parse_deploy_config("environments: [ this is : not valid yaml ][")


def test_config_load_triggers_no_action() -> None:
    """Parsing is pure — it returns a model and performs no side effect. The
    typed model exposes only data; there is no 'apply' / 'run' on it."""
    cfg = parse_deploy_config(_VALID)
    # The model is a frozen dataclass of data; it has no action method.
    assert not hasattr(cfg, "apply")
    assert not hasattr(cfg, "run")
    for env in cfg.environments:
        assert not hasattr(env, "execute")
