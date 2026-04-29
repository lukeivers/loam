"""Amendment #36 — AC36.4 — Handle is sluggified from a first-run
prompt with a sensible default.

Plan §4 AC36.4 outcomes:

- Empty / whitespace input → ``primary`` (the default).
- Free-text input → sluggified (lowercase ASCII, dashes, idempotent).
- ``eve`` rejected with a clear diagnostic (master-plan D3 (a)).

The resolver is a pure function (D-build.1: scaffold itself defaults
to ``primary``; the resolver is exposed for caller-side prompts).
"""

from __future__ import annotations

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    PersonaHandleRejectedError,
    RESERVED_PERSONA_HANDLES,
    resolve_persona_handle,
)


# ---- AC36.4 — defaulting -------------------------------------------------


@pytest.mark.parametrize("raw", [None, "", "   ", "\t", "\n"])
def test_AC36_4_empty_input_resolves_to_primary(raw: str | None) -> None:
    assert resolve_persona_handle(raw) == DEFAULT_PERSONA_HANDLE
    # The default is exactly "primary" per master-plan D3 (a).
    assert DEFAULT_PERSONA_HANDLE == "primary"


# ---- AC36.4 — sluggification --------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Iris", "iris"),
        ("IRIS", "iris"),
        ("Iris  Bright", "iris-bright"),
        ("Iris-Bright", "iris-bright"),
        ("  Iris  ", "iris"),
        ("Iris's", "iris-s"),
    ],
)
def test_AC36_4_freetext_input_sluggifies(raw: str, expected: str) -> None:
    assert resolve_persona_handle(raw) == expected


def test_AC36_4_sluggifier_idempotent_on_fixture_set() -> None:
    """``slug(slug(x)) == slug(x)`` for the AC fixture set."""
    fixtures = ["", "Iris", "Iris  Bright", "Iris's", "IRIS", "Iris-Bright"]
    for raw in fixtures:
        once = resolve_persona_handle(raw)
        twice = resolve_persona_handle(once)
        assert once == twice, (
            f"sluggifier non-idempotent on {raw!r}: once={once!r} twice={twice!r}"
        )


# ---- AC36.4 — eve rejection ---------------------------------------------


def test_AC36_4_eve_input_rejected() -> None:
    """``eve`` is reserved per master-plan D3 (a) — ivers-corp branding."""
    with pytest.raises(PersonaHandleRejectedError) as excinfo:
        resolve_persona_handle("eve")
    err = excinfo.value
    assert "eve" in err.data["resolved"]
    assert err.data["raw_input"] == "eve"
    assert "reserved" in err.data["reason"].lower()


def test_AC36_4_eve_rejection_case_insensitive() -> None:
    """``EVE`` / ``Eve`` lowercase to ``eve`` and reject identically."""
    for variant in ("EVE", "Eve", " eve ", "eve\n"):
        with pytest.raises(PersonaHandleRejectedError):
            resolve_persona_handle(variant)


def test_AC36_4_reserved_handles_set_carries_eve() -> None:
    """The reserved set is observable so callers can pre-flight."""
    assert "eve" in RESERVED_PERSONA_HANDLES


# ---- AC36.4 — pure function: no I/O side effects ------------------------


def test_AC36_4_resolver_is_pure_no_io(tmp_path) -> None:
    """The resolver does not touch the filesystem; calling it
    repeatedly with the same input produces the same output and
    leaves ``tmp_path`` empty."""
    contents_before = list(tmp_path.iterdir())
    for _ in range(3):
        assert resolve_persona_handle("Iris") == "iris"
    contents_after = list(tmp_path.iterdir())
    assert contents_before == contents_after
