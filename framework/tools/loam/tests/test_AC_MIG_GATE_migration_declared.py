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

"""AC.MIG-GATE.* — the release-gate rejects gate-less releases (7th gate)."""

from __future__ import annotations

from pathlib import Path

from loam_cli.release import gates


def _write_migration(d: Path, *, slug: str, operation: str, version: str | None) -> None:
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"slug: {slug}", f"operation: {operation}", "reversible: true"]
    if version is not None:
        lines.append(f"version: {version}")
    (d / f"{slug}.migration.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_AC_MIG_GATE_1_red_when_missing_green_when_present(tmp_path: Path) -> None:
    """`check_migration_declared` returns RED when no migration matches the
    version (with a specific corrective hint); GREEN when one exists."""
    md = tmp_path / "docs" / "state-migrations"
    md.mkdir(parents=True)

    # RED: no declared migration for v9.9.9.
    red = gates.check_migration_declared(tmp_path, "v9.9.9")
    assert red.ok is False
    assert red.name == "migration-declared"
    assert "declares NO user-state migration" in red.message
    assert "v9.9.9" in red.message

    # GREEN: a migration stamped with the version exists.
    _write_migration(md, slug="my-slice", operation="structural-only", version="v9.9.9")
    green = gates.check_migration_declared(tmp_path, "v9.9.9")
    assert green.ok is True
    assert "declares a user-state migration" in green.message


def test_AC_MIG_GATE_2_no_op_declaration_passes(tmp_path: Path) -> None:
    """A version whose declared migration is operation: no-op PASSES the gate
    (the gate forces a declaration, not a non-trivial migration)."""
    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="code-only-slice", operation="no-op", version="v1.0.0")
    res = gates.check_migration_declared(tmp_path, "v1.0.0")
    assert res.ok is True


def test_AC_MIG_GATE_2b_plan_doc_slug_match(tmp_path: Path) -> None:
    """A scope-descriptive plan-doc (no version stamp yet) resolves via the
    plan-doc slug — the dogfood / pre-release path."""
    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="cool-feature-slice", operation="no-op", version=None)
    plan_doc = tmp_path / "docs" / "plans" / "cool-feature-slice-plan.md"
    res = gates.check_migration_declared(tmp_path, "v1.2.3", plan_doc=plan_doc)
    assert res.ok is True


def test_AC_MIG_GATE_3_composes_in_all_gates(
    staged_repo: Path, fixture_version: str
) -> None:
    """The gate is part of ALL_GATES and runs in the same run_all pass — one
    report, no short-circuit (leverage-loam-first, not a parallel CI)."""
    assert gates.check_migration_declared in gates.ALL_GATES
    # The substrate-audit gate (AC.SOL-GATE.*, N2) appended an 8th gate;
    # the boundary-respected gate (AC.BLOCK-ENFORCE.*, N1) appended a 9th.
    assert len(gates.ALL_GATES) == 9

    # run_all (against the canonical staged-release fixture, which declares a
    # migration) returns a verdict for every gate including the migration gate,
    # in one pass — the migration verdict GREEN alongside the others.
    results = gates.run_all(staged_repo, fixture_version)
    names = [r.name for r in results]
    assert "migration-declared" in names
    assert len(results) == 9
    by_name = {r.name: r for r in results}
    assert by_name["migration-declared"].ok is True
