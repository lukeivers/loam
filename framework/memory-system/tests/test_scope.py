"""D6 — scope-of-work mapper tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import scope


@pytest.fixture
def tmp_scope_source(tmp_path):
    registry = tmp_path / "scope_registry.json"
    return scope.MockScopeSource(registry_path=registry)


def test_register_and_fetch_scope(tmp_scope_source: scope.MockScopeSource) -> None:
    rec = tmp_scope_source.register_scope("pos:test-a", name="Test A", description="smoke")
    assert rec.scope_id == "pos:test-a"
    assert tmp_scope_source.get_scope("pos:test-a") == rec


def test_register_is_idempotent(tmp_scope_source: scope.MockScopeSource) -> None:
    rec1 = tmp_scope_source.register_scope("s1")
    rec2 = tmp_scope_source.register_scope("s1")
    assert rec1 is rec2


def test_list_scopes(tmp_scope_source: scope.MockScopeSource) -> None:
    tmp_scope_source.register_scope("a")
    tmp_scope_source.register_scope("b")
    ids = {s.scope_id for s in tmp_scope_source.list_scopes()}
    assert ids == {"a", "b"}


def test_ensure_auto_registers_when_enabled(tmp_scope_source: scope.MockScopeSource) -> None:
    rec = tmp_scope_source.ensure("fresh-scope")
    assert rec.scope_id == "fresh-scope"
    assert tmp_scope_source.get_scope("fresh-scope") is not None


def test_ensure_falls_back_to_default_on_none(tmp_scope_source: scope.MockScopeSource) -> None:
    rec = tmp_scope_source.ensure(None)
    assert rec.scope_id == tmp_scope_source.default_scope_id


def test_registry_persists_across_instances(tmp_path) -> None:
    registry = tmp_path / "scope_registry.json"
    s1 = scope.MockScopeSource(registry_path=registry)
    s1.register_scope("persist", name="persisting scope")

    s2 = scope.MockScopeSource(registry_path=registry)
    rec = s2.get_scope("persist")
    assert rec is not None
    assert rec.name == "persisting scope"
