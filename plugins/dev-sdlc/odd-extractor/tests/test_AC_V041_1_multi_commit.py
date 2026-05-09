"""AC.V041.1 — Multi-commit-per-task emission (F-DESIGN-1 closure sub-fix 1).

Per v0.4.1 patch plan-doc §4 AC.V041.1: when the LLM response carries
multiple commits separated by ``===COMMIT===`` delimiters, the
code-gen pipeline emits a :class:`CodeGenDiff` with multiple
:class:`CodeGenCommit` records. Each commit carries its own
``objectives:`` block (same ``lifted_from`` from the parent
build-next candidate, per AC.V041.1).

Single-commit responses (no delimiter) continue to produce a
length-1 :attr:`CodeGenDiff.commits` tuple — backward-compatible
with v0.4.0 C1's contract.

NO real ``claude -p`` invocation in this module. The stub-injection
pattern from :mod:`test_AC_V040C1_3_soft_smoke_synthetic` is reused:
a duck-typed ``messages.create()`` returning a controlled response.

Verifies:

1. Multi-commit response with two ``===COMMIT===`` segments produces
   a :class:`CodeGenDiff` with ``len(commits) == 2``.
2. Each commit carries the same ``lifted_from`` (from the parent
   candidate) but has distinct ``message_subject`` + ``diff_text``.
3. Three-commit response produces ``len(commits) == 3``.
4. Single-commit response (no delimiter) still produces
   ``len(commits) == 1`` (backward-compatibility).
5. Trailing ``===COMMIT===`` delimiter (empty trailing segment) is
   tolerated — empty segments skipped.
6. From-scratch shape (``--- /dev/null`` source-side) is preserved
   in each commit's diff_text per AC.V041.1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.objective_tracker.spec import LiftedFrom

from loam_odd_extractor.code_gen import generate_code
from loam_odd_extractor.code_gen_spec import CodeGenDiff


_FIXTURE_DIR = (
    Path(__file__).parent / "fixtures" / "code-gen" / "synthetic-v0"
)


# ---- Stub LLM client (duck-typed; mirrors C1 test pattern) ----------


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


class _StubMessages:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.last_call_kwargs: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> _StubResponse:
        self.last_call_kwargs = kwargs
        return _StubResponse(self._response_text)


class _StubLlmClient:
    def __init__(self, response_text: str) -> None:
        self.messages = _StubMessages(response_text)


# ---- Multi-commit response fixtures ---------------------------------


_TWO_COMMIT_RESPONSE = (
    "subject: feat(jsonpp): from-scratch JSON pretty-printer\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/jsonpp.py\n"
    "@@ -0,0 +1,5 @@\n"
    "+import json, sys\n"
    "+def main():\n"
    "+    data = json.load(sys.stdin)\n"
    "+    json.dump(data, sys.stdout, indent=2)\n"
    "+main()\n"
    "===COMMIT===\n"
    "subject: feat(build): compile.sh wrapper for jsonpp\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/compile.sh\n"
    "@@ -0,0 +1,3 @@\n"
    "+#!/bin/bash\n"
    "+cp jsonpp.py executable\n"
    "+chmod +x executable\n"
)

_THREE_COMMIT_RESPONSE = (
    "subject: feat(schema): pydantic shape\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/schema.py\n"
    "@@ -0,0 +1,2 @@\n"
    "+from pydantic import BaseModel\n"
    "+class M(BaseModel): pass\n"
    "===COMMIT===\n"
    "subject: feat(handler): http handler\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/handler.py\n"
    "@@ -0,0 +1,2 @@\n"
    "+def handle(req): return {}\n"
    "+\n"
    "===COMMIT===\n"
    "subject: test(handler): handler smoke\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/test_handler.py\n"
    "@@ -0,0 +1,2 @@\n"
    "+def test_smoke(): assert handle({}) == {}\n"
    "+\n"
)

_SINGLE_COMMIT_RESPONSE = (
    "subject: feat(cli): add hello subcommand greeting handler\n"
    "\n"
    "--- a/mytool/cli.py\n"
    "+++ b/mytool/cli.py\n"
    "@@ -1,5 +1,9 @@\n"
    " import sys\n"
    " \n"
    " def main() -> int:\n"
    "+    if len(sys.argv) >= 2 and sys.argv[1] == \"hello\":\n"
    "+        print(\"hello, world!\")\n"
    "+        return 0\n"
    "     return 1\n"
)

_TRAILING_DELIMITER_RESPONSE = (
    "subject: feat(a): only commit\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/a.py\n"
    "@@ -0,0 +1,1 @@\n"
    "+# a\n"
    "===COMMIT===\n"
)


# ---- AC.V041.1 tests ------------------------------------------------


def test_AC_V041_1_two_commit_response_yields_two_commits() -> None:
    """Two ``===COMMIT===``-delimited segments produce two commits."""
    client = _StubLlmClient(_TWO_COMMIT_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    assert isinstance(diff, CodeGenDiff)
    assert len(diff.commits) == 2, (
        f"AC.V041.1 — two-commit response must yield 2 CodeGenCommit "
        f"records; got {len(diff.commits)}"
    )


def test_AC_V041_1_per_commit_lifted_from_preserved() -> None:
    """Each emitted commit carries the same ``lifted_from`` (from the
    parent build-next candidate) per AC.V041.1; subjects + diff_text
    are distinct."""
    client = _StubLlmClient(_TWO_COMMIT_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    c0, c1 = diff.commits
    # lifted_from is identical (parent candidate) — the v0.4.1 contract
    # is "same source_doc + source_ac for sibling commits closing the
    # same gap."
    assert c0.lifted_from == c1.lifted_from
    assert isinstance(c0.lifted_from, LiftedFrom)
    # Subjects + diffs are distinct (LLM authored different content
    # per commit).
    assert c0.message_subject != c1.message_subject
    assert c0.diff_text != c1.diff_text
    # Both diffs use the from-scratch source-side framing.
    assert "--- /dev/null" in c0.diff_text
    assert "--- /dev/null" in c1.diff_text


def test_AC_V041_1_three_commit_response_yields_three_commits() -> None:
    """Three ``===COMMIT===``-delimited segments produce three commits."""
    client = _StubLlmClient(_THREE_COMMIT_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    assert len(diff.commits) == 3, (
        f"AC.V041.1 — three-commit response must yield 3 CodeGenCommit "
        f"records; got {len(diff.commits)}"
    )
    # Each carries a distinct subject.
    subjects = [c.message_subject for c in diff.commits]
    assert len(set(subjects)) == 3, (
        f"each commit must have a distinct subject; got {subjects!r}"
    )


def test_AC_V041_1_single_commit_response_backward_compatible() -> None:
    """A response with NO ``===COMMIT===`` delimiter produces exactly
    one commit (backward-compatible with v0.4.0 C1's contract)."""
    client = _StubLlmClient(_SINGLE_COMMIT_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    assert len(diff.commits) == 1, (
        f"AC.V041.1 backward-compat — single-commit response (no "
        f"delimiter) must yield exactly 1 commit; got "
        f"{len(diff.commits)}"
    )


def test_AC_V041_1_trailing_delimiter_tolerated() -> None:
    """A response ending with a ``===COMMIT===`` delimiter (empty
    trailing segment) is tolerated — empty segments skipped, valid
    commit count = 1."""
    client = _StubLlmClient(_TRAILING_DELIMITER_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    assert len(diff.commits) == 1, (
        f"AC.V041.1 — trailing delimiter must not be parsed as an "
        f"additional empty commit; got {len(diff.commits)}"
    )


def test_AC_V041_1_per_commit_objectives_block_round_trips() -> None:
    """Each commit's rendered message contains a valid
    ``---objectives---`` block that round-trips via
    ``extract_objectives_block`` → ``LiftedFrom``. Per AC.V041.1
    "each commit carries its own ``objectives:`` block."
    """
    from loam_odd_extractor.code_gen import extract_objectives_block

    client = _StubLlmClient(_THREE_COMMIT_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    for idx, commit in enumerate(diff.commits):
        rendered = commit.render_full_message()
        parsed = extract_objectives_block(rendered)
        assert isinstance(parsed, LiftedFrom)
        assert parsed == commit.lifted_from, (
            f"AC.V041.1 — commit {idx + 1}/{len(diff.commits)} "
            f"objectives block must round-trip cleanly"
        )


def test_AC_V041_1_persist_diff_handles_multi_commit(tmp_path) -> None:
    """:func:`persist_diff` already iterates ``diff.commits`` — the
    multi-commit case must round-trip through persist + load without
    drift on any commit."""
    import shutil

    from loam_odd_extractor.code_gen import persist_diff, load_diff

    target = tmp_path / "extraction"
    shutil.copytree(_FIXTURE_DIR, target)

    client = _StubLlmClient(_TWO_COMMIT_RESPONSE)
    diff = generate_code(target, llm_client=client)
    persist_diff(diff, target)
    loaded = load_diff(target)

    assert len(loaded.commits) == len(diff.commits) == 2
    for orig, ldd in zip(diff.commits, loaded.commits):
        assert orig.diff_text == ldd.diff_text
        assert orig.message_subject == ldd.message_subject
        assert orig.lifted_from == ldd.lifted_from
