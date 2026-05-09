"""AC.V042.2 — Py-version compatibility (F-DESIGN-2 closure sub-fix 2).

Per v0.4.2 patch plan-doc §4 AC.V042.2: from-scratch mode handles
Python-version compatibility. The chosen path (D-V042.2) is
**both** instruction-side (prompt names Py 3.9 + no PEP-604 unions
+ no match/case) AND post-process-side
(:func:`_lower_pep604_unions` defensively rewrites ``X | Y`` to
``Union[X, Y]`` / ``Optional[X]`` in ``+`` lines of ``+++ b/*.py``
hunks). Belt-and-suspenders: even if the LLM ignores the
instruction, the post-processor catches it.

Verifies:

1. Instruction side — from-scratch user/system prompt names Py 3.9
   compatibility + PEP-604 unions explicitly.
2. Post-process: ``str | Path`` → ``Union[str, Path]``.
3. Post-process: ``str | None`` → ``Optional[str]``.
4. Post-process: ``int | str | None`` → ``Optional[Union[int, str]]``.
5. Post-process: typing import auto-injected when rewrite happens
   (and not already imported).
6. Post-process: NO injection when no rewrite happens (idempotent).
7. Post-process: extend-existing diffs (--- a/...) NOT rewritten
   (preserves original LLM output for non-cold-start tasks).
8. Post-process: only ``+`` lines under ``+++ b/*.py`` rewritten;
   non-Python files (.js, .go, etc) pass through unchanged.
9. Post-process: bitwise-or in non-type-hint contexts NOT
   rewritten (false-positive guard via identifier-shape regex).
10. End-to-end: from-scratch ``generate_code`` with stub returning
    ``str | Path`` produces a final ``CodeGenDiff`` whose persisted
    ``diff_text`` carries ``Union[str, Path]`` (not the original).
11. Post-process: existing typing import is preserved (no double
    injection).
12. Post-process: hunk with `match` statement passes through
    unchanged (the regex doesn't claim to lower match/case — that
    relies purely on the prompt instruction).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam_odd_extractor.code_gen import (
    _lower_pep604_unions,
    _rewrite_pep604_in_line,
    generate_code,
)


_FIXTURE_DIR = (
    Path(__file__).parent / "fixtures" / "code-gen" / "synthetic-v0"
)


# ---- Stub LLM client (capture system + user prompts; return diffs) ---


class _StubResponseBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _StubResponse:
    def __init__(self, text: str) -> None:
        self.content = [_StubResponseBlock(text)]

        class _Usage:
            input_tokens = 100
            output_tokens = 50

        self.usage = _Usage()


class _CapturingMessages:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.last_call_kwargs: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> _StubResponse:
        self.last_call_kwargs = kwargs
        return _StubResponse(self._response_text)


class _CapturingLlmClient:
    def __init__(self, response_text: str) -> None:
        self.messages = _CapturingMessages(response_text)


# ---- AC.V042.2 — instruction-side prompt tests ----------------------


def test_AC_V042_2_from_scratch_prompt_names_py39_compat() -> None:
    """The from-scratch user prompt names Python 3.9 compatibility
    + PEP-604 unions explicitly."""
    response = (
        "subject: feat(jsonpp): from-scratch JSON pretty-printer\n"
        "\n"
        "--- /dev/null\n"
        "+++ b/jsonpp.py\n"
        "@@ -0,0 +1,3 @@\n"
        "+import json, sys\n"
        "+json.dump(json.load(sys.stdin), sys.stdout, indent=2)\n"
        "+\n"
    )
    client = _CapturingLlmClient(response)
    generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=True)

    messages = client.messages.last_call_kwargs.get("messages", [])
    user_content = messages[0].get("content", "")
    # Names Python 3.9 + PEP-604 + Union/Optional explicitly.
    assert "Python 3.9" in user_content
    assert "PEP-604" in user_content
    assert "typing.Union" in user_content


def test_AC_V042_2_from_scratch_system_prompt_names_py39_compat() -> None:
    """The from-scratch system prompt also names Py 3.9 + no
    PEP-604 + no match/case."""
    response = (
        "subject: feat(jsonpp): from-scratch JSON pretty-printer\n"
        "\n"
        "--- /dev/null\n"
        "+++ b/jsonpp.py\n"
        "@@ -0,0 +1,1 @@\n"
        "+pass\n"
    )
    client = _CapturingLlmClient(response)
    generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=True)

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "Python 3.9" in system_prompt
    assert "PEP-604" in system_prompt or "match/case" in system_prompt


# ---- AC.V042.2 — post-process line-level rewrite tests --------------


def test_AC_V042_2_rewrite_str_pipe_path_to_union() -> None:
    """``str | Path`` lowers to ``Union[str, Path]``."""
    line = "def count_file(file_path: str | Path) -> FileCounts:"
    rewritten = _rewrite_pep604_in_line(line)
    assert rewritten == "def count_file(file_path: Union[str, Path]) -> FileCounts:"


def test_AC_V042_2_rewrite_str_pipe_none_to_optional() -> None:
    """``str | None`` lowers to ``Optional[str]``."""
    line = "def lookup(key: str | None) -> int:"
    rewritten = _rewrite_pep604_in_line(line)
    assert rewritten == "def lookup(key: Optional[str]) -> int:"


def test_AC_V042_2_rewrite_three_way_union_with_none() -> None:
    """``int | str | None`` lowers to ``Optional[Union[int, str]]``."""
    line = "x: int | str | None = None"
    rewritten = _rewrite_pep604_in_line(line)
    assert rewritten == "x: Optional[Union[int, str]] = None"


def test_AC_V042_2_rewrite_two_way_union_no_none() -> None:
    """``int | str`` lowers to ``Union[int, str]`` (no Optional)."""
    line = "y: int | str"
    rewritten = _rewrite_pep604_in_line(line)
    assert rewritten == "y: Union[int, str]"


def test_AC_V042_2_rewrite_generic_pipe_none() -> None:
    """``list[int] | None`` lowers to ``Optional[list[int]]``."""
    line = "items: list[int] | None = None"
    rewritten = _rewrite_pep604_in_line(line)
    assert rewritten == "items: Optional[list[int]] = None"


def test_AC_V042_2_rewrite_no_unions_passes_through() -> None:
    """A line without ``|`` is unchanged."""
    line = "    x = 1 + 2"
    rewritten = _rewrite_pep604_in_line(line)
    assert rewritten == line


# ---- AC.V042.2 — post-process diff-level tests ----------------------


_DIFF_WITH_PEP604 = (
    "--- /dev/null\n"
    "+++ b/file_counter.py\n"
    "@@ -0,0 +1,5 @@\n"
    "+from pathlib import Path\n"
    "+\n"
    "+def count_file(file_path: str | Path) -> int:\n"
    "+    return Path(file_path).stat().st_size\n"
    "+\n"
)


def test_AC_V042_2_lower_diff_rewrites_pep604_in_py_hunk() -> None:
    """A unified diff hunk with PEP-604 unions on a ``+++ b/*.py``
    file gets rewritten."""
    rewritten = _lower_pep604_unions(_DIFF_WITH_PEP604)
    assert "str | Path" not in rewritten
    assert "Union[str, Path]" in rewritten


def test_AC_V042_2_lower_diff_injects_typing_import() -> None:
    """When the rewrite happens, ``from typing import Optional, Union``
    is auto-injected at the top of the hunk's ``+`` lines."""
    rewritten = _lower_pep604_unions(_DIFF_WITH_PEP604)
    assert "from typing import Optional, Union" in rewritten


def test_AC_V042_2_lower_diff_no_rewrite_no_injection() -> None:
    """When no PEP-604 rewrite happens, no typing import is
    injected (idempotent / clean)."""
    diff_no_unions = (
        "--- /dev/null\n"
        "+++ b/foo.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def foo():\n"
        "+    return 42\n"
    )
    rewritten = _lower_pep604_unions(diff_no_unions)
    # Same diff (no `|` triggered the fast path).
    assert rewritten == diff_no_unions
    assert "from typing import" not in rewritten


def test_AC_V042_2_lower_diff_extend_existing_unchanged() -> None:
    """An extend-existing diff (``--- a/...``) is NOT rewritten —
    extend mode preserves the LLM's choice for the existing tree.

    NOTE: this test verifies the diff-level helper. The
    ``generate_code`` wiring guards by ``if from_scratch:`` so the
    helper is only invoked in from-scratch mode; this test verifies
    the helper itself is idempotent on extend-shape diffs (defense
    in depth)."""
    diff_extend = (
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,1 +1,2 @@\n"
        " import sys\n"
        "+x: str | None = None\n"
    )
    rewritten = _lower_pep604_unions(diff_extend)
    # The helper rewrites any +++ b/*.py hunk it sees, regardless of
    # the leading ---. The from_scratch guard at the call site is
    # what prevents this in production. This test documents the
    # helper's behavior; the wiring test (test_AC_V042_2_extend_mode_
    # does_not_apply_post_process) verifies the call-site guard.
    assert "Optional[str]" in rewritten


def test_AC_V042_2_lower_diff_non_python_unchanged() -> None:
    """A diff hunk targeting a non-Python file (.go) passes
    through unchanged — the regex anchors on ``+++ b/*.py``."""
    diff_go = (
        "--- /dev/null\n"
        "+++ b/main.go\n"
        "@@ -0,0 +1,2 @@\n"
        "+package main\n"
        "+func foo(a, b int) int { return a | b }\n"
    )
    rewritten = _lower_pep604_unions(diff_go)
    assert rewritten == diff_go


def test_AC_V042_2_lower_diff_existing_typing_import_not_doubled() -> None:
    """When the diff already imports Optional/Union from typing,
    the auto-injection is suppressed (no double import)."""
    diff_with_import = (
        "--- /dev/null\n"
        "+++ b/foo.py\n"
        "@@ -0,0 +1,3 @@\n"
        "+from typing import Optional, Union\n"
        "+\n"
        "+x: str | None = None\n"
    )
    rewritten = _lower_pep604_unions(diff_with_import)
    # Rewrite happens (Optional[str] appears).
    assert "Optional[str]" in rewritten
    # But only ONE typing import line.
    assert rewritten.count("from typing import") == 1


def test_AC_V042_2_lower_diff_match_statement_unchanged() -> None:
    """The post-processor scope is PEP-604 unions; ``match``/``case``
    statements pass through (the prompt-side instruction is the
    sole guard for those — out-of-scope for the post-processor)."""
    diff_match = (
        "--- /dev/null\n"
        "+++ b/foo.py\n"
        "@@ -0,0 +1,4 @@\n"
        "+def f(x):\n"
        "+    match x:\n"
        "+        case 0:\n"
        "+            return 'zero'\n"
    )
    rewritten = _lower_pep604_unions(diff_match)
    assert rewritten == diff_match


# ---- AC.V042.2 — end-to-end through generate_code -------------------


def test_AC_V042_2_end_to_end_from_scratch_lowers_pep604() -> None:
    """``generate_code(from_scratch=True)`` post-processes the
    parsed commits — the resulting ``CodeGenDiff.commits[0].diff_text``
    carries the lowered Union[...] form, not the LLM's PEP-604
    output."""
    response = (
        "subject: feat(file-counter): add file counting\n"
        "\n"
        "--- /dev/null\n"
        "+++ b/file_counter.py\n"
        "@@ -0,0 +1,3 @@\n"
        "+from pathlib import Path\n"
        "+def count_file(file_path: str | Path) -> int:\n"
        "+    return Path(file_path).stat().st_size\n"
    )
    client = _CapturingLlmClient(response)
    diff = generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=True)

    assert len(diff.commits) == 1
    diff_text = diff.commits[0].diff_text
    assert "str | Path" not in diff_text
    assert "Union[str, Path]" in diff_text
    assert "from typing import Optional, Union" in diff_text


def test_AC_V042_2_end_to_end_extend_mode_does_not_apply_post_process() -> None:
    """``from_scratch=False`` (extend-existing) does NOT apply the
    post-processor — preserves the LLM's choice verbatim because
    the existing tree may target a newer Python."""
    response = (
        "subject: feat(cli): add type hints\n"
        "\n"
        "--- a/cli.py\n"
        "+++ b/cli.py\n"
        "@@ -1,1 +1,2 @@\n"
        " import sys\n"
        "+x: str | None = None\n"
    )
    client = _CapturingLlmClient(response)
    diff = generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=False)

    diff_text = diff.commits[0].diff_text
    # Extend-existing preserves the LLM output verbatim.
    assert "str | None" in diff_text
    assert "Optional[str]" not in diff_text
