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

"""AC.MPF.4 — _serialise_turn skips empty contributors.

Outcome (per locked plan §4 AC.MPF.4): when a contributor returns
empty (or whitespace-only) text, ``_serialise_turn`` skips that
contributor entirely (no header, no whitespace-padded line). When
NO contributor produced text, the ``contributor_outputs:`` header
itself is omitted.

Pre-amendment-#95 the loop carried ``for ln in text.splitlines()
or [""]:`` which always emitted at least one indent-padded line per
contributor — yielding the ``[memory-retrieval]\\n    \\n``
whitespace shape that Surface 2c diagnosed. Post-amendment-#95 the
loop guards on ``text.strip()`` and continues on empty.
"""

from __future__ import annotations

from loam.primary_persona.context_composer import (
    CorpusGateState,
    _serialise_turn,
)


def _serialise(contributor_outputs):
    return _serialise_turn(
        prompt="anything",
        resolved_component=None,
        corpus_gate_state=CorpusGateState.loaded,
        missing_paths=(),
        contributor_outputs=contributor_outputs,
    )


def test_AC_MPF_4_all_empty_contributors_omits_header_and_blocks() -> None:
    """When every contributor returned empty text, neither
    ``contributor_outputs:`` header nor any per-contributor block
    appears in the serialised turn payload.
    """
    out = _serialise([("memory-retrieval", ""), ("other", "  ")])
    assert "contributor_outputs:" not in out
    assert "[memory-retrieval]" not in out
    assert "[other]" not in out


def test_AC_MPF_4_mixed_empty_and_non_empty() -> None:
    """When some contributors are empty and some produce text, only
    the non-empty ones render. The header appears once.
    """
    out = _serialise(
        [
            ("alpha", "first line"),
            ("beta", ""),
            ("gamma", "third line"),
        ]
    )
    assert out.count("contributor_outputs:") == 1
    assert "[alpha]" in out
    assert "[beta]" not in out
    assert "[gamma]" in out
    assert "first line" in out
    assert "third line" in out


def test_AC_MPF_4_no_trailing_whitespace_only_lines() -> None:
    """Direct surface check on the diagnostic's empirical bug shape:
    no contributor block produces an indent-only line in the output.
    """
    out = _serialise([("memory-retrieval", "")])
    # Pre-amendment shape: "  [memory-retrieval]\n    \n"
    # Post-amendment: header skipped entirely.
    for line in out.splitlines():
        # Only acceptable indent-only lines: none. Every emitted line
        # must carry non-whitespace content.
        assert line.strip() != "" or line == "", (
            f"unexpected indent-only line in serialised output: {line!r}"
        )


def test_AC_MPF_4_non_empty_contributor_renders_normally() -> None:
    """Backwards-compat: a contributor with normal multi-line text
    renders as before (header + indented body).
    """
    out = _serialise(
        [
            (
                "memory-retrieval",
                "[memory-retrieval]\n  (no results for this query)",
            )
        ]
    )
    assert "contributor_outputs:" in out
    assert "[memory-retrieval]" in out
    assert "(no results for this query)" in out


def test_AC_MPF_4_whitespace_only_contributor_treated_as_empty() -> None:
    """Defensive: a contributor returning ``"   \\n  \\t  \\n"`` is
    indistinguishable from empty (text.strip() is "").
    """
    out = _serialise([("ws", "   \n  \t  \n")])
    assert "[ws]" not in out
    assert "contributor_outputs:" not in out
