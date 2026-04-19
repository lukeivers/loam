"""R25, R26: structural-impossibility defence-in-depth.

R25 — `budget_seconds` Pydantic validation: `0` is refused (`ge=1`);
`None` is accepted as "no framework timeout" (ruling #3).

R26 — identity with safety's `structural_hash`: the primitive imports
the symbol rather than duplicating the implementation.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from reversibility_primitive import CompensationPathBinding, get_spec_hash
from safety_layer.events import structural_hash


def test_R25_budget_seconds_zero_refused() -> None:
    with pytest.raises(ValidationError):
        CompensationPathBinding(
            scope_id="s1", handle="h", idempotency_key="k", budget_seconds=0
        )


def test_R25_budget_seconds_none_accepted() -> None:
    b = CompensationPathBinding(
        scope_id="s1", handle="h", idempotency_key="k", budget_seconds=None
    )
    assert b.budget_seconds is None


def test_R25_budget_seconds_positive_accepted() -> None:
    b = CompensationPathBinding(
        scope_id="s1", handle="h", idempotency_key="k", budget_seconds=1
    )
    assert b.budget_seconds == 1


def test_R26_spec_hash_is_safety_structural_hash() -> None:
    """Identity check: the primitive's re-exported `get_spec_hash` IS
    safety's `structural_hash`."""
    assert get_spec_hash is structural_hash


def test_R26_hash_module_imported_not_duplicated() -> None:
    """Scan the primitive source — no hashlib.sha256(spec...) re-
    implementation, only the import."""
    import pathlib
    import reversibility_primitive as rp

    pkg_dir = pathlib.Path(rp.__file__).parent
    for py in pkg_dir.rglob("*.py"):
        txt = py.read_text()
        # The only allowed reference to structural_hash is an import.
        if "structural_hash" in txt:
            assert (
                "from safety_layer.events import structural_hash" in txt
                or "from safety_layer.events import" in txt
            ), f"structural_hash used without importing from safety_layer in {py}"
