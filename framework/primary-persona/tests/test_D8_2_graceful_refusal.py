"""AC D8.2 — Graceful refusal on missing corpus.

Outcome (from amendment plan §4 D8.2): on a workspace where at least
one baseline corpus path is absent, the session-start composer returns
an ``additionalContext`` payload whose ``corpus_gate_state`` sentinel
is ``partial`` or ``missing`` and whose body names every missing
baseline path in a structured diagnostic block. The session proceeds
— the composer does not raise and does not request ``continue:
false``. A subsequent ``on_user_prompt_submit`` invocation on the
same session observes the ``missing`` / ``partial`` sentinel via the
shared composer and does not block the turn.

Owner ruling D-2 governs: refusal is GRACEFUL. No ``decision: "block"``,
no ``continue: false``. Turn contributors may narrow their own
contribution on observing the sentinel, but the gate itself issues
no structural refusal.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    CorpusGateState,
)
from loam.primary_persona.session_start_gate import compose_session_fields


def _seed_partial_workspace(root: Path, missing: set[str]) -> None:
    """Seed a baseline workspace with CLAUDE.md + the session-start
    discipline section; selectively omit *missing* paths so the
    composer's gate transitions the sentinel."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "# test workspace\n\n"
        "## Session-start discipline\n\n"
        "Read:\n\n"
        "- `docs/odd-methodology.md`\n"
        "- `docs/odd-in-loam.md`\n"
        "- `docs/rebuild/VALUE_PROPOSITION.md`\n"
        "- `docs/rebuild/STATE.md`\n"
        "- `docs/rebuild/FUTURE_IDEAS.md`\n"
        "\n---\n\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "rebuild").mkdir()
    all_paths = {
        "docs/odd-methodology.md",
        "docs/odd-in-loam.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/FUTURE_IDEAS.md",
    }
    for rel in all_paths - missing:
        full = root / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("content")


def test_D8_2_partial_sentinel_on_one_missing_path(tmp_path: Path) -> None:
    """One missing baseline path → sentinel is ``partial``, not
    ``loaded``, not ``missing``."""
    _seed_partial_workspace(tmp_path, missing={"docs/rebuild/STATE.md"})
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert payload.corpus_gate_state == CorpusGateState.partial


def test_D8_2_missing_sentinel_when_every_baseline_absent(tmp_path: Path) -> None:
    """Every baseline path absent → sentinel is ``missing`` (CLAUDE.md
    itself absent as well)."""
    # Do NOT write CLAUDE.md or any doc; workspace is empty.
    tmp_path.mkdir(parents=True, exist_ok=True)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert payload.corpus_gate_state == CorpusGateState.missing


def test_D8_2_missing_paths_named_in_diagnostic(tmp_path: Path) -> None:
    """The missing-paths enumeration names every absent baseline path
    in a structured diagnostic block."""
    _seed_partial_workspace(
        tmp_path,
        missing={"docs/rebuild/STATE.md", "docs/odd-in-loam.md"},
    )
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    payload = composer.on_session_start(tmp_path)

    assert "docs/rebuild/STATE.md" in payload.missing_paths
    assert "docs/odd-in-loam.md" in payload.missing_paths
    # The serialised additionalContext body surfaces the diagnostic
    # block so Claude can read the structured reason.
    assert "docs/rebuild/STATE.md" in payload.additional_context_text
    assert "docs/odd-in-loam.md" in payload.additional_context_text


def test_D8_2_composer_does_not_raise_on_missing_corpus(tmp_path: Path) -> None:
    """Session-start composer does not raise when corpus is missing —
    graceful degradation per owner ruling D-2."""
    tmp_path.mkdir(parents=True, exist_ok=True)  # empty workspace
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    # Must not raise — degrade to a diagnostic-shaped payload instead.
    payload = composer.on_session_start(tmp_path)
    # Sentinel is not loaded but the payload exists.
    assert payload.corpus_gate_state != CorpusGateState.loaded
    assert payload.additional_context_text  # non-empty diagnostic


def test_D8_2_turn_observes_sentinel_and_does_not_block(tmp_path: Path) -> None:
    """A subsequent ``on_user_prompt_submit`` invocation observes the
    ``missing`` / ``partial`` sentinel via the shared composer and does
    not block the turn. The turn-payload surface returns normally."""
    _seed_partial_workspace(tmp_path, missing={"docs/rebuild/STATE.md"})
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    composer.on_session_start(tmp_path)

    # The turn must not raise. No decision: "block" semantics here —
    # the gate issues no structural refusal per owner ruling D-2.
    turn = composer.on_user_prompt_submit(prompt="any message")

    assert turn.corpus_gate_state == CorpusGateState.partial
    assert "docs/rebuild/STATE.md" in turn.missing_paths
    # The turn payload carries the diagnostic visibly so any turn-
    # level contributor (D7) may narrow its own contribution.
    assert "docs/rebuild/STATE.md" in turn.additional_context_text
