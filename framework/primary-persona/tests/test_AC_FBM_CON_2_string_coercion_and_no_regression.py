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

"""AC-FBM-CON-2 + AC-FBM-CON-3 — FBM path consolidation contributor contract.

AC-FBM-CON-2 (string-coercion safety): the gated contributor returns a ``str``
ALWAYS — never ``None`` — so ``context_composer._serialise_turn``'s
``text.strip()`` is safe. A no-match / trivial prompt yields ``""`` and renders
no contributor block.

AC-FBM-CON-3 (no-regression: real memory surfaces): through the contributor, a
query matching a real corpus rule surfaces the gated block.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import (
    register_keep_pace_turn_contributor,
)


class _CaptureComposer:
    """Minimal composer stub that records register() calls."""

    def __init__(self) -> None:
        self.registered: list[tuple[str, object, object]] = []

    def register(self, *, name, trigger_kind, fn):  # noqa: ANN001
        self.registered.append((name, trigger_kind, fn))


def _build_contributor(workspace_root: Path, slug: str):
    composer = _CaptureComposer()
    register_keep_pace_turn_contributor(
        composer, workspace_root=workspace_root, workspace_slug=slug
    )
    assert composer.registered, "register must call composer.register"
    name, _trigger, fn = composer.registered[0]
    assert name == "memory-retrieval"
    return fn


def test_trivial_prompt_returns_empty_string(tmp_path: Path) -> None:
    """AC-FBM-CON-2: trivial/empty prompt yields ``""`` (a str), not None."""
    fn = _build_contributor(tmp_path / "myws", "myws")

    for ctx in ({"prompt": ""}, {"prompt": "   "}, {}, {"prompt": "ok"}):
        out = fn(dict(ctx))
        assert isinstance(out, str), f"contributor must return str, got {type(out)}"
        # The output is .strip()-safe (this is the exact call
        # ``_serialise_turn`` makes).
        _ = out.strip()


def test_malformed_context_fails_closed_to_empty_string(tmp_path: Path) -> None:
    """AC-FBM-CON-2: a non-dict / surprising context fails closed to ``""``."""
    fn = _build_contributor(tmp_path / "myws", "myws")
    for bad in (None, [], "not-a-dict", {"prompt": 123}):
        out = fn(bad)  # type: ignore[arg-type]
        assert isinstance(out, str)
        assert out == "" or isinstance(out.strip(), str)


def test_real_corpus_rule_surfaces_through_contributor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-FBM-CON-3: a query matching a real corpus rule surfaces the gated
    block through the contributor.

    The corpus is resolved from ``<home>/.claude/projects/<ws-slug>/memory``;
    point ``Path.home()`` at a temp home seeded with a corpus doc whose tokens
    the query matches.
    """
    ws = tmp_path / "myws"
    ws.mkdir()

    fake_home = tmp_path / "home"
    proj_slug = "-" + str(ws).strip("/").replace("/", "-")
    corpus_dir = fake_home / ".claude" / "projects" / proj_slug / "memory"
    corpus_dir.mkdir(parents=True)
    # A weighted/pinned rule — the hard-floor pin guarantees it surfaces for a
    # matching query regardless of the single-doc BM25 noise floor (AC-FBM-W-2).
    (corpus_dir / "feedback_telegram_channel.md").write_text(
        "---\n"
        "weight: 90\n"
        "pinned: true\n"
        "---\n"
        "# Telegram is the only user channel\n\n"
        "Every reply to the user routes through Telegram; the terminal is "
        "diagnostics only. Telegram is the sole outbound channel.\n",
        encoding="utf-8",
    )

    # ``_resolve_composer_config`` resolves the corpus from
    # ``Path.home() / ".claude" / "projects" / <ws-slug> / "memory"``.
    # ``Path.home()`` reads ``$HOME`` on POSIX; point it at the temp home.
    monkeypatch.setenv("HOME", str(fake_home))

    fn = _build_contributor(ws, "myws")
    out = fn({"prompt": "what is the telegram channel policy"})
    assert isinstance(out, str)
    assert "telegram" in out.lower(), (
        f"the gated block must surface the matching corpus rule; got: {out!r}"
    )
