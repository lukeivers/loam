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

"""Foundation revision Stage 3b F1a — principles-install resolver +
universal-install action.

The principles spec at ``framework/docs/principles/principles.md``
is the universal/exportable principle-tier of loam's methodology
stack. Adopters can install it at one of two scopes:

- "universal" — write a reference from ``~/.claude/CLAUDE.md`` to
  the spec path so every Claude Code session on this machine has
  the principles in its global session-start context.
- "local" (default) — do nothing global; the workspace's own
  session-start corpus carries the principles by virtue of the
  workspace being a loam workspace.

The resolver is a pure function (mirroring
``resolve_persona_handle`` from amendment #36). The install action
is idempotent — a second universal-install call leaves
``~/.claude/CLAUDE.md`` unchanged.

Test surface:

- AC.F1a.1 — empty/None input resolves to "local" (the default).
- AC.F1a.2 — affirmative tokens resolve to "universal".
- AC.F1a.3 — negative tokens resolve to "local".
- AC.F1a.4 — non-matching input resolves to ``None`` (caller re-prompts).
- AC.F1a.5 — case-insensitive matching.
- AC.F1a.6 — resolver is pure (no I/O).
- AC.F1a.7 — universal install writes the marker block.
- AC.F1a.8 — universal install is idempotent (second call leaves file).
- AC.F1a.9 — universal install creates ``~/.claude/CLAUDE.md`` when
  absent.
- AC.F1a.10 — universal install preserves existing file content
  (append, not overwrite).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PRINCIPLES_INSTALL_CHOICE,
    install_principles_reference_universal,
    resolve_principles_install_choice,
)


# ---- AC.F1a.1 — empty/None resolves to default (local) -------------------


@pytest.mark.parametrize("raw", [None, "", "   ", "\t", "\n"])
def test_F1a_empty_input_resolves_to_local_default(raw: str | None) -> None:
    assert resolve_principles_install_choice(raw) == DEFAULT_PRINCIPLES_INSTALL_CHOICE
    # The default is exactly "local" per the foundation-revision plan
    # §1 F1a (default local; universal install requires explicit
    # affirmative input).
    assert DEFAULT_PRINCIPLES_INSTALL_CHOICE == "local"


# ---- AC.F1a.2 — affirmative tokens resolve to "universal" ---------------


@pytest.mark.parametrize(
    "raw",
    ["universal", "u", "yes", "y", "global", "g"],
)
def test_F1a_affirmative_tokens_resolve_universal(raw: str) -> None:
    assert resolve_principles_install_choice(raw) == "universal"


# ---- AC.F1a.3 — negative tokens resolve to "local" ----------------------


@pytest.mark.parametrize(
    "raw",
    ["local", "l", "no", "n", "skip", "default"],
)
def test_F1a_negative_tokens_resolve_local(raw: str) -> None:
    assert resolve_principles_install_choice(raw) == "local"


# ---- AC.F1a.4 — non-matching input resolves to None ---------------------


@pytest.mark.parametrize(
    "raw",
    ["maybe", "later", "ehh", "okay", "sure", "perhaps", "qwerty"],
)
def test_F1a_unknown_input_returns_none_for_re_prompt(raw: str) -> None:
    """Non-empty, non-matching input surfaces ambiguity — the
    resolver does NOT silently default to local because that would
    drop a possible "yes" from a user who typed something the
    resolver doesn't recognise."""
    assert resolve_principles_install_choice(raw) is None


# ---- AC.F1a.5 — case-insensitive matching -------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("UNIVERSAL", "universal"),
        ("Universal", "universal"),
        ("YES", "universal"),
        (" Y ", "universal"),
        ("LOCAL", "local"),
        ("Local", "local"),
        ("NO", "local"),
        (" n\n", "local"),
    ],
)
def test_F1a_resolver_is_case_insensitive(raw: str, expected: str) -> None:
    assert resolve_principles_install_choice(raw) == expected


# ---- AC.F1a.6 — resolver is a pure function ------------------------------


def test_F1a_resolver_is_pure_no_io(tmp_path: Path) -> None:
    """The resolver does not touch the filesystem; calling it
    repeatedly with the same input produces the same output and
    leaves ``tmp_path`` empty."""
    contents_before = list(tmp_path.iterdir())
    for _ in range(3):
        assert resolve_principles_install_choice("universal") == "universal"
        assert resolve_principles_install_choice("local") == "local"
        assert resolve_principles_install_choice("maybe") is None
    contents_after = list(tmp_path.iterdir())
    assert contents_before == contents_after


def test_F1a_resolver_idempotent_on_returned_values() -> None:
    """The resolver is idempotent on the values it returns:
    ``resolve(resolve(x)) == resolve(x)`` for the universal/local
    tokens."""
    for token in ["universal", "local"]:
        once = resolve_principles_install_choice(token)
        twice = resolve_principles_install_choice(once)
        assert once == twice, (
            f"resolver non-idempotent on {token!r}: once={once!r} twice={twice!r}"
        )


# ---- AC.F1a.7 — universal install writes the marker block ---------------


def test_F1a_universal_install_writes_marker_block(tmp_path: Path) -> None:
    """A universal-install call writes the principles-install block
    into ``~/.claude/CLAUDE.md`` (overridden by ``claude_md_path``
    for the test)."""
    claude_md = tmp_path / "CLAUDE.md"
    spec_path = "/path/to/framework/docs/principles/principles.md"
    wrote = install_principles_reference_universal(
        spec_path=spec_path,
        claude_md_path=claude_md,
    )
    assert wrote is True
    content = claude_md.read_text()
    # Marker is present so subsequent installs can detect prior install.
    assert "<!-- loam:principles-install -->" in content
    # The spec path is in the body so the user can navigate to it.
    assert spec_path in content
    # The block is recognisably about principles.
    assert "principles" in content.lower()


# ---- AC.F1a.8 — universal install is idempotent --------------------------


def test_F1a_universal_install_idempotent_on_second_call(
    tmp_path: Path,
) -> None:
    """A second universal-install call with the same path returns
    ``False`` and leaves the file unchanged."""
    claude_md = tmp_path / "CLAUDE.md"
    spec_path = "/path/to/framework/docs/principles/principles.md"
    first = install_principles_reference_universal(
        spec_path=spec_path,
        claude_md_path=claude_md,
    )
    assert first is True
    content_after_first = claude_md.read_text()

    second = install_principles_reference_universal(
        spec_path=spec_path,
        claude_md_path=claude_md,
    )
    assert second is False
    content_after_second = claude_md.read_text()
    assert content_after_first == content_after_second


# ---- AC.F1a.9 — universal install creates the file when absent ----------


def test_F1a_universal_install_creates_claude_md_when_absent(
    tmp_path: Path,
) -> None:
    """If ``~/.claude/CLAUDE.md`` doesn't exist, the install action
    creates it (and any missing parent directories)."""
    nested = tmp_path / "fresh-home" / ".claude" / "CLAUDE.md"
    assert not nested.exists()
    spec_path = "/path/to/framework/docs/principles/principles.md"
    wrote = install_principles_reference_universal(
        spec_path=spec_path,
        claude_md_path=nested,
    )
    assert wrote is True
    assert nested.exists()
    content = nested.read_text()
    assert "<!-- loam:principles-install -->" in content
    assert spec_path in content


# ---- AC.F1a.10 — universal install preserves existing content ----------


def test_F1a_universal_install_preserves_existing_content(
    tmp_path: Path,
) -> None:
    """The install action APPENDS to ``~/.claude/CLAUDE.md`` — does
    not overwrite. Pre-existing user content survives intact."""
    claude_md = tmp_path / "CLAUDE.md"
    pre_existing = (
        "# Global — User Name\n\n"
        "## Communication rules\n"
        "- Lead with the answer.\n"
        "- No filler.\n\n"
        "## Token efficiency\n"
        "- Sonnet for routine tasks.\n"
    )
    claude_md.write_text(pre_existing)

    spec_path = "/path/to/framework/docs/principles/principles.md"
    wrote = install_principles_reference_universal(
        spec_path=spec_path,
        claude_md_path=claude_md,
    )
    assert wrote is True
    content_after = claude_md.read_text()

    # Pre-existing content survives intact — substring check.
    assert pre_existing in content_after
    # The install block was appended (not prepended).
    pre_idx = content_after.index(pre_existing)
    marker_idx = content_after.index("<!-- loam:principles-install -->")
    assert marker_idx > pre_idx, (
        "install block must be appended after existing content, "
        f"not prepended (pre at {pre_idx}, marker at {marker_idx})"
    )


# ---- Cross-check: choice-then-action wiring ------------------------------


def test_F1a_resolver_universal_then_install_action(tmp_path: Path) -> None:
    """End-to-end check that a 'yes' input resolves to 'universal'
    and that the universal-install action then writes the block.
    This is the wiring the future first-run UX layer will use."""
    claude_md = tmp_path / "CLAUDE.md"
    spec_path = (
        "/Users/example/loam-workspace/framework/docs/principles/principles.md"
    )

    user_typed = "yes"
    choice = resolve_principles_install_choice(user_typed)
    assert choice == "universal"

    if choice == "universal":
        install_principles_reference_universal(
            spec_path=spec_path,
            claude_md_path=claude_md,
        )

    assert claude_md.exists()
    assert spec_path in claude_md.read_text()


def test_F1a_resolver_local_then_no_install_action(tmp_path: Path) -> None:
    """An empty input resolves to 'local' (the default), and the
    caller's branch on that choice does NOT write the universal
    install block. Documents the intended UX wiring."""
    claude_md = tmp_path / "CLAUDE.md"
    spec_path = (
        "/Users/example/loam-workspace/framework/docs/principles/principles.md"
    )

    user_typed = ""
    choice = resolve_principles_install_choice(user_typed)
    assert choice == "local"

    if choice == "universal":
        install_principles_reference_universal(
            spec_path=spec_path,
            claude_md_path=claude_md,
        )

    # Local install: no universal-side action; CLAUDE.md untouched.
    assert not claude_md.exists()
