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

"""AC.LOCAL.2 — the enabled LOCAL command set contains no irreversible action
(verified by absence of any prod/destroy verb — the floor idles); and a
destructive-SQL guard at LOCAL warns, it does not block (local DB disposable),
while a non-local target is deferred to the sealed floor (fail-closed)."""

from __future__ import annotations

from loam.local_deploy_tier.command_set import (
    IRREVERSIBLE_VERBS,
    SqlGuardLevel,
    enabled_local_verbs,
    guard_local_sql,
    is_local_target,
    local_command_set_is_floor_idle,
    local_set_irreversible_overlap,
)


def test_local_command_set_has_no_irreversible_verb() -> None:
    """The guarantee: no prod/destroy verb is reachable at LOCAL, so the floor
    has nothing to gate (it idles). Verified by the EMPTY overlap."""
    assert local_set_irreversible_overlap() == frozenset()
    assert local_command_set_is_floor_idle() is True
    # And concretely: none of the irreversible verbs is enabled.
    assert enabled_local_verbs().isdisjoint(IRREVERSIBLE_VERBS)


def test_irreversible_verbs_are_genuinely_irreversible() -> None:
    """Sanity on the absence-check: the verbs declared irreversible are the
    prod/destroy verbs (promote / deploy / provision / destroy), so the
    disjointness test is meaningful, not vacuous."""
    for verb in ("promote", "deploy-prod", "provision", "destroy"):
        assert verb in IRREVERSIBLE_VERBS


def test_destructive_sql_against_local_target_warns_not_blocks() -> None:
    """A drop/reset against a provably-local target WARNS (advises) and
    proceeds — the local DB is a free undo. The level is WARN, never a block."""
    for command in ("DROP TABLE users", "psql -c 'TRUNCATE TABLE orders'", "supabase db reset"):
        decision = guard_local_sql(command, target="postgres://localhost:5432/app")
        assert decision.level is SqlGuardLevel.WARN, command
        assert decision.sub_action
        assert "local" in decision.message.lower()
    # WARN is the strongest LOCAL outcome — there is no BLOCK level at all.
    assert not hasattr(SqlGuardLevel, "BLOCK")


def test_destructive_sql_against_unknown_target_defers_to_floor() -> None:
    """A destructive op whose target is NOT provably local is DEFERRED to the
    sealed floor (fail-closed) — the LOCAL warn-downgrade does not apply, so a
    managed-DB URL never gets a free pass from this tier."""
    decision = guard_local_sql(
        "DROP DATABASE app", target="postgres://db.prod.example.com:5432/app"
    )
    assert decision.level is SqlGuardLevel.DEFER
    decision_unknown = guard_local_sql("DROP TABLE t", target="")
    assert decision_unknown.level is SqlGuardLevel.DEFER


def test_non_destructive_command_is_clean() -> None:
    decision = guard_local_sql("SELECT * FROM users", target="postgres://localhost/app")
    assert decision.level is SqlGuardLevel.NONE


def test_local_target_predicate_is_fail_closed() -> None:
    """Provably-local markers are local; everything else is not (a false
    'local' on a managed URL is the one mistake with prod blast radius)."""
    assert is_local_target("postgres://localhost:5432/app") is True
    assert is_local_target("postgres://127.0.0.1/app") is True
    assert is_local_target("sqlite:///./dev.db") is True
    assert is_local_target("postgres://@db:5432/app") is True
    assert is_local_target("postgres://db.prod.example.com/app") is False
    assert is_local_target("") is False
    assert is_local_target("some-managed-host.rds.amazonaws.com") is False
