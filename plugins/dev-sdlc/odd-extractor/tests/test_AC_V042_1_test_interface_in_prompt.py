"""AC.V042.1 — Test-interface section as load-bearing context in
from-scratch prompt (F-DESIGN-2 closure sub-fix 1).

Per v0.4.2 patch plan-doc §4 AC.V042.1: when ``from_scratch=True``
and ``repo_path`` points at a docs-only repo containing a SPEC
document with a "Test interface" section, the from-scratch prompt
MUST embed that section as load-bearing context and instruct the
LLM to author the SPEC's named build artefacts (e.g.,
``compile.sh``, ``executable``) as first-class commits.

Verifies:

1. ``_extract_test_interface_excerpt`` finds the SPEC.md "Test
   interface" section and returns it.
2. ``_extract_test_interface_excerpt`` falls back to the full doc
   body when the SPEC has no named "Test interface" section.
3. ``_extract_test_interface_excerpt`` returns ``None`` when the
   docs-only dir contains no SPEC-bearing markdown.
4. ``generate_code`` with ``from_scratch=True`` + ``repo_path``
   embeds the Test interface excerpt in the user prompt under the
   ``Test interface from SPEC:`` header.
5. The system prompt instructs ``compile.sh`` / executable
   authoring (named-artefact requirement).
6. The system prompt instructs SPEC-CLI matching (subprocess form,
   output format).
7. When ``from_scratch=False`` the SPEC excerpt is NOT injected
   (extend-existing mode preserves v0.4.0 behavior).
8. The excerpt is capped at the documented threshold to bound
   prompt token count.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam_odd_extractor.code_gen import (
    _extract_test_interface_excerpt,
    _SPEC_EXCERPT_MAX_CHARS,
    generate_code,
)


_FIXTURE_DIR = (
    Path(__file__).parent / "fixtures" / "code-gen" / "synthetic-v0"
)


# ---- Stub LLM client (capture system + user prompts) ----------------


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


_FROM_SCRATCH_RESPONSE = (
    "subject: feat(jsonpp): from-scratch JSON pretty-printer\n"
    "\n"
    "--- /dev/null\n"
    "+++ b/jsonpp.py\n"
    "@@ -0,0 +1,3 @@\n"
    "+import json, sys\n"
    "+json.dump(json.load(sys.stdin), sys.stdout, indent=2)\n"
    "+\n"
)

_EXTEND_RESPONSE = (
    "subject: feat(cli): extend hello handler\n"
    "\n"
    "--- a/cli.py\n"
    "+++ b/cli.py\n"
    "@@ -1,1 +1,2 @@\n"
    " import sys\n"
    "+# extended\n"
)


# Realistic SPEC content matching the wcclone task shape.
_WCCLONE_SPEC_BODY = """# wcclone specification

## Objective

Build a wcclone command-line program that takes a single filename
argument and prints `<lines> <words> <bytes>` to stdout.

## Acceptance criteria

- AC1: `compile.sh` produces an `executable` file in the working directory.
- AC2: The program accepts one argument.

## Build constraints

- Any single-file implementation language is acceptable.
- The build script `compile.sh` must produce an executable named `executable`.

## Test interface

The test suite invokes the program as:

```python
result = subprocess.run(["./executable", "/path/to/file"],
                        capture_output=True, text=True, timeout=10)
result.stdout.strip()  # "<lines> <words> <bytes>"
```
"""


# ---- AC.V042.1 — _extract_test_interface_excerpt helper -------------


def test_AC_V042_1_extract_finds_test_interface_section(tmp_path) -> None:
    """The extractor finds the SPEC.md "Test interface" section
    and returns it (heading + body)."""
    (tmp_path / "SPEC.md").write_text(_WCCLONE_SPEC_BODY)
    excerpt = _extract_test_interface_excerpt(tmp_path)
    assert excerpt is not None
    assert "Test interface" in excerpt
    assert "subprocess.run" in excerpt
    assert "executable" in excerpt
    # The full SPEC's "Build constraints" section IS included because
    # it lives under a sibling H2; the extractor returns only the
    # "Test interface" H2 body. Verify scope: the "Acceptance criteria"
    # H2 (which is upstream) should NOT be in the excerpt.
    assert "AC1: `compile.sh` produces" not in excerpt


def test_AC_V042_1_extract_falls_back_to_full_doc_when_no_section(
    tmp_path,
) -> None:
    """When the SPEC has no "Test interface"-style heading, the
    extractor returns the full doc body (capped) so the LLM still
    sees the SPEC as load-bearing."""
    (tmp_path / "SPEC.md").write_text(
        "# Project\n\n## Goal\n\nBuild a thing that runs as "
        "`./executable arg1 arg2`.\n"
    )
    excerpt = _extract_test_interface_excerpt(tmp_path)
    assert excerpt is not None
    # No named section matched -> full doc fallback. Prefix is the
    # "(from <filename>; full doc)" tag.
    assert "full doc" in excerpt
    assert "./executable arg1 arg2" in excerpt


def test_AC_V042_1_extract_returns_none_for_repo_without_spec(
    tmp_path,
) -> None:
    """A repo without any SPEC.md / README.md / TESTING.md returns
    ``None`` so the prompt falls back to the v0.4.1 shape."""
    (tmp_path / "config.yaml").write_text("k: v\n")
    excerpt = _extract_test_interface_excerpt(tmp_path)
    assert excerpt is None


def test_AC_V042_1_extract_finds_readme_when_spec_absent(
    tmp_path,
) -> None:
    """README.md is the documented fallback when no SPEC.md exists."""
    (tmp_path / "README.md").write_text(_WCCLONE_SPEC_BODY)
    excerpt = _extract_test_interface_excerpt(tmp_path)
    assert excerpt is not None
    assert "subprocess.run" in excerpt


def test_AC_V042_1_extract_caps_excerpt_at_documented_threshold(
    tmp_path,
) -> None:
    """A pathological multi-MB SPEC is capped at the documented
    threshold to bound prompt token count."""
    pathological = "## Test interface\n\n" + ("X" * (_SPEC_EXCERPT_MAX_CHARS + 1000))
    (tmp_path / "SPEC.md").write_text(pathological)
    excerpt = _extract_test_interface_excerpt(tmp_path)
    assert excerpt is not None
    # Excerpt is capped (allow some prefix/suffix overhead — the
    # truncated marker adds ~20 chars).
    assert len(excerpt) <= _SPEC_EXCERPT_MAX_CHARS + 100
    assert "truncated" in excerpt


def test_AC_V042_1_extract_handles_nested_spec(tmp_path) -> None:
    """A SPEC nested under a `docs/` subdir is found via the second
    pass walk."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "SPEC.md").write_text(_WCCLONE_SPEC_BODY)
    excerpt = _extract_test_interface_excerpt(tmp_path)
    assert excerpt is not None
    assert "subprocess.run" in excerpt


# ---- AC.V042.1 — generate_code prompt-injection tests ---------------


def test_AC_V042_1_from_scratch_with_repo_path_injects_test_interface(
    tmp_path,
) -> None:
    """``generate_code(from_scratch=True, repo_path=<docs-only repo>)``
    embeds the Test interface excerpt in the user prompt under the
    canonical heading."""
    (tmp_path / "SPEC.md").write_text(_WCCLONE_SPEC_BODY)

    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=True,
        repo_path=tmp_path,
    )

    messages = client.messages.last_call_kwargs.get("messages", [])
    assert messages
    user_content = messages[0].get("content", "")

    # Heading is present.
    assert "Test interface from SPEC:" in user_content, (
        f"AC.V042.1 — user prompt must carry "
        f"'Test interface from SPEC:' heading; got: "
        f"{user_content[-500:]!r}"
    )
    # Load-bearing snippet from the SPEC is present (the
    # subprocess.run line is the structural pinpoint).
    assert "subprocess.run" in user_content, (
        f"AC.V042.1 — user prompt must carry the SPEC's Test "
        f"interface body (subprocess.run line); got: "
        f"{user_content[-500:]!r}"
    )
    # Named artefact `executable` is present.
    assert "executable" in user_content


def test_AC_V042_1_system_prompt_instructs_compile_sh_authoring(
    tmp_path,
) -> None:
    """The from-scratch system prompt instructs the LLM to author
    the SPEC's named build script (e.g., ``compile.sh``) as a
    first-class commit."""
    (tmp_path / "SPEC.md").write_text(_WCCLONE_SPEC_BODY)

    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=True,
        repo_path=tmp_path,
    )

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert isinstance(system_prompt, str)
    # Names compile.sh + executable explicitly.
    assert "compile.sh" in system_prompt, (
        f"AC.V042.1 — from-scratch system prompt must name "
        f"compile.sh as an example named artefact; got: "
        f"{system_prompt!r}"
    )
    assert "executable" in system_prompt
    # Instructs first-class commit authoring for SPEC artefacts.
    assert "first-class commit" in system_prompt or "MUST author" in system_prompt


def test_AC_V042_1_system_prompt_instructs_spec_cli_matching(
    tmp_path,
) -> None:
    """The from-scratch system prompt instructs the LLM to match
    the SPEC's CLI form (subprocess shape, output format)."""
    (tmp_path / "SPEC.md").write_text(_WCCLONE_SPEC_BODY)

    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=True,
        repo_path=tmp_path,
    )

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "EXACTLY" in system_prompt or "exactly" in system_prompt
    assert (
        "output format" in system_prompt
        or "trailing newlines" in system_prompt
        or "subprocess" in system_prompt
    )


def test_AC_V042_1_extend_existing_does_not_inject_spec_excerpt(
    tmp_path,
) -> None:
    """``from_scratch=False`` (extend-existing mode) does NOT inject
    the SPEC excerpt — backward-compat with v0.4.0 / v0.4.1."""
    (tmp_path / "SPEC.md").write_text(_WCCLONE_SPEC_BODY)
    # Make tmp_path look like an existing repo so auto-detect goes
    # extend-existing (even if we explicitly set from_scratch=False
    # below, this also documents the orthogonal auto-detect path).
    (tmp_path / "main.py").write_text("def main(): pass\n")

    client = _CapturingLlmClient(_EXTEND_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=False,
        repo_path=tmp_path,
    )

    messages = client.messages.last_call_kwargs.get("messages", [])
    user_content = messages[0].get("content", "")
    assert "Test interface from SPEC:" not in user_content


def test_AC_V042_1_from_scratch_no_repo_path_falls_back_to_v041_shape(
    tmp_path,
) -> None:
    """``from_scratch=True`` without ``repo_path`` falls back to the
    v0.4.1 prompt shape (no ``Test interface from SPEC:`` block)."""
    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=True,
        # No repo_path — no SPEC source available.
    )

    messages = client.messages.last_call_kwargs.get("messages", [])
    user_content = messages[0].get("content", "")
    # No SPEC excerpt heading — graceful fallback.
    assert "Test interface from SPEC:" not in user_content
    # But the v0.4.1 from-scratch framing still present.
    assert "/dev/null" in user_content


def test_AC_V042_1_from_scratch_repo_path_without_spec_falls_back(
    tmp_path,
) -> None:
    """``from_scratch=True`` + ``repo_path`` pointing at a repo
    without a SPEC.md / README.md falls back gracefully (no
    SPEC excerpt heading)."""
    (tmp_path / "config.yaml").write_text("k: v\n")
    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=True,
        repo_path=tmp_path,
    )

    messages = client.messages.last_call_kwargs.get("messages", [])
    user_content = messages[0].get("content", "")
    assert "Test interface from SPEC:" not in user_content
    # v0.4.1 from-scratch framing still present.
    assert "/dev/null" in user_content
