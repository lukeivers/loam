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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.MSC.3 — named-thread durable surfaces in the session-start
corpus (Gap A part a closed).

Outcome (plan §4 AC.MSC.3): the session-start baseline-corpus presence
set includes the named-thread durable surface(s) that record "where we
were + open owner rulings" (FIDRAFT-class). When that surface exists on
disk, a fresh session's session-start payload reflects its presence
and its live-thread content is reachable at session-start; when
absent, the existing graceful-missing sentinel path applies unchanged.

Verification (plan §4): with the named-thread surface present, assert
it appears in the session-start corpus-presence set / contributor
output; with it absent, assert the session-start payload still
composes (graceful-missing, no raise) per the existing
``corpus_gate_state`` contract.

D-MSC.3 selected mechanism (builder's call): the session-start
corpus path-list is the ``## Session-start discipline`` section of
``CLAUDE.dev.md`` (parsed by ``session_start_gate.discover_baseline_
corpus``). Adding ``docs/FUTURE_IDEAS_DRAFT.md`` to that list is the
corpus-membership edit. This test asserts the OUTCOME (the named
surface is in the discovered corpus when CLAUDE carries it; payload
composes graceful-missing when the surface is absent) — the mechanism
(path-list vs dedicated config vs direct read) is not pinned.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.primary_persona.session_start_gate import (
    discover_baseline_corpus,
    compose_session_fields,
)


def _claude_md_with_fidraft(root: Path) -> None:
    """A workspace CLAUDE.md whose session-start-discipline list
    includes the named-thread durable surface (the D-MSC.3
    mechanism, mirrored at the workspace level the gate parses)."""
    (root / "CLAUDE.md").write_text(
        "# ws\n\n"
        "## Session-start discipline\n\n"
        "Before acting, read:\n\n"
        "- `docs/STATE.md`\n"
        "- `docs/FUTURE_IDEAS.md`\n"
        "- `docs/FUTURE_IDEAS_DRAFT.md`\n"
        "\n---\n\n"
    )


def test_AC_MSC_3_named_surface_in_discovered_corpus(
    tmp_path: Path,
) -> None:
    """When CLAUDE.md's session-start list names the FIDRAFT durable
    surface, ``discover_baseline_corpus`` returns it as a baseline
    corpus path."""
    _claude_md_with_fidraft(tmp_path)
    paths = discover_baseline_corpus(tmp_path)
    assert "docs/FUTURE_IDEAS_DRAFT.md" in paths, (
        "the named-thread durable surface must be in the session-start "
        f"baseline corpus; got {paths}"
    )


def test_AC_MSC_3_present_surface_reflected_in_session_fields(
    tmp_path: Path,
) -> None:
    """With the named surface on disk, the session-start field dict's
    corpus-presence set marks it present."""
    _claude_md_with_fidraft(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "STATE.md").write_text("state")
    (tmp_path / "docs" / "FUTURE_IDEAS.md").write_text("ideas")
    (tmp_path / "docs" / "FUTURE_IDEAS_DRAFT.md").write_text(
        "- **F-INVERTED-FRAME — live thread; owner ruling pending.**"
    )
    fields = compose_session_fields(tmp_path)
    corpus = dict(fields["corpus_paths"])
    assert "docs/FUTURE_IDEAS_DRAFT.md" in corpus, (
        "named surface must appear in corpus_paths"
    )
    assert corpus["docs/FUTURE_IDEAS_DRAFT.md"] is True, (
        "named surface present on disk must be marked present"
    )
    assert "docs/FUTURE_IDEAS_DRAFT.md" not in fields["missing_paths"]


def test_AC_MSC_3_absent_surface_graceful_missing(tmp_path: Path) -> None:
    """When the named surface is absent, the session-start payload
    still composes (graceful-missing, no raise) and the surface is
    flagged in missing_paths per the existing corpus_gate_state
    contract."""
    _claude_md_with_fidraft(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "STATE.md").write_text("state")
    (tmp_path / "docs" / "FUTURE_IDEAS.md").write_text("ideas")
    # docs/FUTURE_IDEAS_DRAFT.md deliberately absent.
    fields = compose_session_fields(tmp_path)  # must not raise
    assert "docs/FUTURE_IDEAS_DRAFT.md" in fields["missing_paths"], (
        "absent named surface must be flagged in missing_paths"
    )
    # The payload still composes — sentinel is partial (some present,
    # some missing), not an exception.
    assert str(fields["corpus_gate_state"]) in (
        "CorpusGateState.partial",
        "partial",
    ), f"expected partial sentinel, got {fields['corpus_gate_state']}"


def test_AC_MSC_3_canonical_claude_dev_md_carries_named_surface(
    tmp_path: Path,
) -> None:
    """The canonical D-MSC.3 mechanism edit landed.

    In a real loam DEV workspace the session-start corpus reaches the
    persona through TWO paths and the named-thread surface must be in
    the corpus by the relevant one:

      - the dev-mode partition: ``loam-mode``'s session-start emitter
        loads ``CLAUDE.dev.md`` whole into additionalContext (dev
        mode); the ``## Session-start discipline`` section is the
        corpus path-list. The D-MSC.3 edit adds
        ``docs/FUTURE_IDEAS_DRAFT.md`` to that section.

    Asserting the OUTCOME: (1) the canonical CLAUDE.dev.md's
    session-start-discipline section (parsed with the SAME regex
    ``discover_baseline_corpus`` uses) names the surface; (2) the
    loam-mode dev-mode emitter surfaces that line into the
    session-start payload.

    Cold-clone correctness (AC.MSCCF.1): ``_read_dev_intent_inner``
    checks ``personas_dir.is_dir()`` before iterating; if absent the
    reader is never consulted and dev-mode cannot be forced via the
    reader alone. This test creates a minimal on-disk personas
    structure at ``tmp_path`` so the directory check passes, then
    routes the emit call through ``tmp_path``. Passes in both the
    dev-tree and a bare cold-clone (v1.9.1 PATCH fix).
    """
    repo_root = Path(__file__).resolve().parents[3]
    claude_dev = repo_root / "CLAUDE.dev.md"
    assert claude_dev.is_file(), "CLAUDE.dev.md must exist"

    # (1) The session-start-discipline section names the surface,
    # parsed with the gate's own section + backtick-path regexes so
    # this asserts the corpus-membership contract, not mere substring
    # presence.
    import re

    text = claude_dev.read_text(encoding="utf-8")
    header_re = re.compile(
        r"^##\s+Session-start discipline\s*$", re.MULTILINE | re.IGNORECASE
    )
    next_header_re = re.compile(r"^(##[^#]|---)\s*", re.MULTILINE)
    backtick_re = re.compile(r"`([^`\n]+\.md)`")
    m = header_re.search(text)
    assert m, "CLAUDE.dev.md must carry a Session-start discipline section"
    tail = text[m.end() :]
    nh = next_header_re.search(tail)
    section = tail[: nh.start() if nh else len(tail)]
    section_paths = [
        p
        for p in backtick_re.findall(section)
        if p.endswith(".md")
        and "amendment-*" not in p
        and not p.startswith("/")
    ]
    assert "docs/FUTURE_IDEAS_DRAFT.md" in section_paths, (
        "the D-MSC.3 mechanism edit must place docs/FUTURE_IDEAS_DRAFT.md "
        f"inside the CLAUDE.dev.md session-start section; got "
        f"{section_paths}"
    )

    # (2) The dev-mode session-start emitter surfaces that line into
    # additionalContext (dev mode). Drive loam-mode's emitter with a
    # path-aware reader: the dev-intent probe reads a persona contract
    # (return YAML with dev_intent: yes to force dev mode); the
    # dev-extension read returns the canonical CLAUDE.dev.md.
    #
    # AC.MSCCF.1 fixture: create the minimal on-disk personas directory
    # that _read_dev_intent_inner requires before it consults the reader.
    # Without this, the is_dir() guard returns "absent" in a cold clone
    # (workspace/personas/ is user state, not git-tracked). The reader
    # still supplies all file *content* (dev_intent YAML for the
    # contract path; CLAUDE.dev.md text for the dev-extension path).
    personas_dir = tmp_path / "workspace" / "personas" / "loam"
    personas_dir.mkdir(parents=True)
    (personas_dir / "contract.yaml").write_text(
        ""
    )  # empty; reader supplies content

    from loam_mode.session_start import emit_session_start_context

    def _reader(path: Path) -> str:
        if path.name.endswith(".yaml") or "contract" in path.name:
            return "is_primary: true\ndev_intent: yes\n"
        # The dev-extension file read (CLAUDE.dev.md path).
        return text

    payload = emit_session_start_context(tmp_path, reader=_reader)
    assert "docs/FUTURE_IDEAS_DRAFT.md" in payload, (
        "the dev-mode session-start payload must surface the "
        f"named-thread durable surface; payload head={payload[:160]!r}"
    )
