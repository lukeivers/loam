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

"""AC.DSF.4 — write-time prod-string block (G2 closeable part).

A prod-shaped connection string (matching a declared-prod identity) written
into a non-prod / local config file is blocked at write time, with the secret
value never echoed into any reply, brief, or log.
"""

from __future__ import annotations

from loam.deploy_safety_floor.config import parse_deploy_config
from loam.deploy_safety_floor.gate import evaluate_write


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

# A connection string containing the declared-prod host + a credential.
_PROD_CONN = "DATABASE_URL=postgres://admin:s3cr3t-p4ss@db.prod.internal:5432/orders"


def test_prod_string_into_local_env_file_is_blocked() -> None:
    cfg = parse_deploy_config(_CONFIG)
    decision = evaluate_write(".env.local", _PROD_CONN, cfg)
    assert decision.denied is True


def test_blocked_message_never_echoes_the_secret_value() -> None:
    cfg = parse_deploy_config(_CONFIG)
    decision = evaluate_write(".env.local", _PROD_CONN, cfg)
    assert decision.denied is True
    # Neither the password nor the full connection string appears anywhere in
    # the user-facing reason.
    assert "s3cr3t-p4ss" not in decision.reason
    assert _PROD_CONN not in decision.reason
    assert "db.prod.internal" not in decision.reason
    # The destination file IS named (so the user can act).
    assert ".env.local" in decision.reason


def test_prod_string_into_a_prod_config_is_allowed() -> None:
    """The block targets prod strings landing in NON-prod files; a prod string
    in a production-suffixed file is not the AC.DSF.4 failure mode."""
    cfg = parse_deploy_config(_CONFIG)
    decision = evaluate_write(".env.production", _PROD_CONN, cfg)
    assert decision.denied is False


def test_non_prod_string_into_local_file_is_allowed() -> None:
    cfg = parse_deploy_config(_CONFIG)
    decision = evaluate_write(
        ".env.local", "DATABASE_URL=postgres://localhost:5432/scratch", cfg
    )
    assert decision.denied is False
