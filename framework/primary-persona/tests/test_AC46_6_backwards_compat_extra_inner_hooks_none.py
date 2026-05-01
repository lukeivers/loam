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

"""AC46.6 — Backwards-compat: existing test suites stay green.

Outcome (per umbrella plan §4a):
  - When ``extra_inner_hooks=None`` (the pre-amendment default),
    ``build_first_run_stanza`` and ``build_supervisor_stanza`` produce
    output byte-identical to the pre-amendment-#46 path. (This is the
    same backwards-compat surface amendment #45 already preserves;
    #46 does not regress it.)
  - The new UserPromptSubmit hook entry is single-contributor; future
    multi-contributor generalisation is deferred.

This test file lives under primary-persona/tests/ rather than
hands-off-lifecycle/tests/ because the AC's "existing #32/#33/#37 test
suites stay green" outcome is naturally exercised by running the
primary-persona suite as a whole — every #32/#33/#37 test continues to
pass under the amendment #46 changes (no regression).

The hands-off-lifecycle side of AC46.6 (extra_inner_hooks=None
identity) is exercised by the unchanged ``test_AC45_*`` tests under
``hands-off-lifecycle/tests/``.
"""

from __future__ import annotations

from loam.primary_persona.context_composer import ComposedContextPayload, TriggerKind
from loam.primary_persona.session_start_gate import compose_session_fields


def test_AC46_6_composer_register_unchanged_for_unrelated_contributors() -> None:
    """The composer's ``register`` API and TriggerKind enum surface
    are unchanged. A test that constructed a composer + registered a
    contributor pre-amendment-#46 still works post-amendment."""
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    composer.register(
        name="test-contributor",
        trigger_kind=TriggerKind.session,
        fn=lambda ctx: "hello",
    )
    contributors = composer.contributors(trigger_kind=TriggerKind.session)
    assert len(contributors) == 1
    assert contributors[0].name == "test-contributor"


def test_AC46_6_session_start_emit_works_without_persona() -> None:
    """A workspace without ``personas/`` produces a session-level
    payload (the starter-pending contributor is simply not registered).
    This proves the amendment #46 wiring degrades cleanly when content
    that hasn't been authored is missing."""
    from pathlib import Path
    import tempfile

    from loam.primary_persona.session_start_emitter import emit_session_start_context

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "CLAUDE.md").write_text(
            "## Session-start discipline\n- `docs/x.md`\n"
        )
        (root / "docs").mkdir()
        (root / "docs" / "x.md").write_text("y")
        text = emit_session_start_context(root)
        # The session-level payload is non-empty (corpus paths, gate
        # state, etc.) without a persona being loaded.
        assert "[pos-v2 session-start" in text
        assert "starter-pending" not in text
