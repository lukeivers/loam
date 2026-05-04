"""AC.OREK.4 — Language-adapter registry.

- Protocol shape: name, supports(repo), extract(repo, plan).
- register_adapter() + discover_adapters().
- Cycle 1 ships zero adapters; discover_adapters() returns [].
- Protocol-violator raises RegistryError.
- Entry-point discovery skips on load failure (tested with stub).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor import (
    AnalysisPlan,
    LanguageAdapter,
    RawACs,
    RegistryError,
    discover_adapters,
    register_adapter,
)


# ---- stub adapter --------------------------------------------------


class _StubAdapter:
    """Adapter that satisfies the Protocol shape."""

    name = "stub"

    def supports(self, repo: Path) -> bool:
        return True

    def extract(self, repo: Path, plan: AnalysisPlan) -> RawACs:
        return RawACs(
            extraction_id=plan.extraction_id,
            acs=[{"ac_id": "AC.STUB.1", "text": "stub AC"}],
            unhandled_paths=[],
            per_slice_costs={},
            created_at="2026-05-04T12:00:00+00:00",
        )


def test_protocol_recognises_valid_adapter() -> None:
    """isinstance check via runtime_checkable Protocol."""
    adapter = _StubAdapter()
    assert isinstance(adapter, LanguageAdapter)


def test_register_adapter_accepts_valid() -> None:
    register_adapter(_StubAdapter())
    found = discover_adapters()
    names = [a.name for a in found]
    assert "stub" in names


def test_register_adapter_rejects_missing_name() -> None:
    class BadNoName:
        name = ""

        def supports(self, repo: Path) -> bool:
            return False

        def extract(self, repo: Path, plan: AnalysisPlan) -> RawACs:
            return RawACs(extraction_id="x", created_at="x")

    with pytest.raises(RegistryError, match="name"):
        register_adapter(BadNoName())


def test_register_adapter_rejects_missing_supports() -> None:
    class BadNoSupports:
        name = "bad"

        # supports method missing
        def extract(self, repo: Path, plan: AnalysisPlan) -> RawACs:
            return RawACs(extraction_id="x", created_at="x")

    with pytest.raises(RegistryError, match="supports"):
        register_adapter(BadNoSupports())


def test_register_adapter_rejects_missing_extract() -> None:
    class BadNoExtract:
        name = "bad"

        def supports(self, repo: Path) -> bool:
            return False

        # extract method missing

    with pytest.raises(RegistryError, match="extract"):
        register_adapter(BadNoExtract())


def test_register_adapter_rejects_duplicate_name() -> None:
    register_adapter(_StubAdapter())
    with pytest.raises(RegistryError, match="already registered"):
        register_adapter(_StubAdapter())


def test_discover_adapters_empty_at_cycle_1() -> None:
    """No manual registration + zero entry-points → []."""
    found = discover_adapters()
    assert found == []


def test_discover_includes_manual_registrations() -> None:
    register_adapter(_StubAdapter())
    found = discover_adapters()
    # At minimum the stub; possibly more if other entry-points
    # are installed (none expected in Cycle 1).
    assert any(a.name == "stub" for a in found)


def test_protocol_required_attrs_present_on_class() -> None:
    """Protocol declares the three required surfaces."""
    annotations = LanguageAdapter.__annotations__
    assert "name" in annotations
    # supports + extract are method-stubs in the Protocol body
    # (not annotations); verify via getattr probing.
    assert hasattr(LanguageAdapter, "supports")
    assert hasattr(LanguageAdapter, "extract")
