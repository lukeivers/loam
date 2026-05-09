"""AC.V041.2 — From-scratch prompt mode (F-DESIGN-1 closure sub-fix 2).

Per v0.4.1 patch plan-doc §4 AC.V041.2: when the source repository
has no source files (only docs / config), code-gen uses a
from-scratch prompt instead of the extend-existing prompt. The
from-scratch prompt:

- Instructs "create new files" not "modify existing source."
- Uses ``--- /dev/null`` as the source-side framing.
- Encourages multi-commit emission (composes with AC.V041.1).

Mode selection covers both:

- Explicit ``from_scratch=True`` flag — overrides any auto-detection.
- Auto-detect via :func:`_detect_from_scratch` when ``from_scratch=None``
  and ``repo_path`` is supplied.

Verifies:

1. Explicit ``from_scratch=True`` selects the from-scratch system
   prompt (captured via stub's ``last_call_kwargs``).
2. Explicit ``from_scratch=False`` selects the extend-existing
   system prompt (default v0.4.0 C1 shape).
3. ``_detect_from_scratch`` returns True for an empty repo.
4. ``_detect_from_scratch`` returns True for a docs-only repo
   (markdown + yaml only).
5. ``_detect_from_scratch`` returns False for a repo containing a
   ``.py`` source file.
6. ``_detect_from_scratch`` ignores ``.git/``, ``node_modules/``,
   ``__pycache__/`` directories.
7. Auto-detect path: ``repo_path`` supplied + empty repo → from-scratch
   selected.
8. Default behaviour preserved: ``from_scratch=None`` AND
   ``repo_path=None`` → extend-existing (backward-compat with v0.4.0
   C1 callers that don't pass ``repo_path``).
9. From-scratch prompt content: the user-prompt text contains the
   "create new files" framing + ``--- /dev/null`` reference.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam_odd_extractor.code_gen import (
    _detect_from_scratch,
    generate_code,
)
from loam_odd_extractor.code_gen_spec import CodeGenDiff


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
    """Records the kwargs of every ``create()`` call so tests can
    assert on the system + user prompt content."""

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


# ---- AC.V041.2 — explicit flag tests --------------------------------


def test_AC_V041_2_explicit_from_scratch_true_selects_from_scratch_system_prompt() -> None:
    """``from_scratch=True`` explicitly selects the from-scratch
    system prompt; the system prompt mentions "create new" + "no
    existing source tree" + ``--- /dev/null``."""
    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=True)

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert isinstance(system_prompt, str)
    assert "creating new source files" in system_prompt or "creating new" in system_prompt, (
        f"AC.V041.2 — from_scratch=True system prompt must instruct "
        f"creating new files; got: {system_prompt[:200]!r}"
    )
    assert "/dev/null" in system_prompt, (
        f"AC.V041.2 — from_scratch=True system prompt must reference "
        f"--- /dev/null framing; got: {system_prompt[:200]!r}"
    )


def test_AC_V041_2_explicit_from_scratch_false_selects_extend_system_prompt() -> None:
    """``from_scratch=False`` selects the extend-existing system
    prompt (v0.4.0 C1 default shape); does NOT carry the from-scratch
    "no existing source tree" framing."""
    client = _CapturingLlmClient(_EXTEND_RESPONSE)
    generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=False)

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "existing codebase" in system_prompt, (
        f"AC.V041.2 — from_scratch=False system prompt must reference "
        f"existing codebase; got: {system_prompt[:200]!r}"
    )
    assert "no existing source tree" not in system_prompt.lower(), (
        f"AC.V041.2 — from_scratch=False must NOT carry from-scratch "
        f"framing; got: {system_prompt[:200]!r}"
    )


def test_AC_V041_2_from_scratch_user_prompt_carries_dev_null_framing() -> None:
    """The user-prompt body in from-scratch mode names the
    ``--- /dev/null`` source-side requirement explicitly."""
    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(_FIXTURE_DIR, llm_client=client, from_scratch=True)

    messages = client.messages.last_call_kwargs.get("messages", [])
    assert messages, "messages list must not be empty"
    user_msg_content = messages[0].get("content", "")
    assert "/dev/null" in user_msg_content, (
        f"AC.V041.2 — from_scratch user prompt must instruct "
        f"--- /dev/null source-side framing; got: "
        f"{user_msg_content[-300:]!r}"
    )


# ---- AC.V041.2 — _detect_from_scratch helper ------------------------


def test_AC_V041_2_detect_empty_repo_is_from_scratch(tmp_path) -> None:
    """An empty directory is from-scratch (zero source files)."""
    assert _detect_from_scratch(tmp_path) is True


def test_AC_V041_2_detect_docs_only_repo_is_from_scratch(tmp_path) -> None:
    """A repo with only README.md + SPEC.md is from-scratch (markdown
    is not a source extension)."""
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "SPEC.md").write_text("Behavior: ...\n")
    (tmp_path / "config.yaml").write_text("k: v\n")
    (tmp_path / "package.json").write_text("{}\n")
    assert _detect_from_scratch(tmp_path) is True


def test_AC_V041_2_detect_repo_with_python_file_is_extend_existing(tmp_path) -> None:
    """A repo with even one ``.py`` source file is NOT from-scratch."""
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "main.py").write_text("def main(): pass\n")
    assert _detect_from_scratch(tmp_path) is False


def test_AC_V041_2_detect_ignores_skipped_directories(tmp_path) -> None:
    """``.git/`` / ``node_modules/`` / ``__pycache__/`` files don't
    count toward the source-file tally."""
    (tmp_path / "README.md").write_text("# Test\n")
    # .git/HEAD shouldn't matter
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    # node_modules/foo/index.js shouldn't matter
    nm_dir = tmp_path / "node_modules" / "foo"
    nm_dir.mkdir(parents=True)
    (nm_dir / "index.js").write_text("module.exports = {};\n")
    # __pycache__/x.pyc shouldn't matter
    pc_dir = tmp_path / "__pycache__"
    pc_dir.mkdir()
    (pc_dir / "x.cpython-313.pyc").write_text("\x00\x00\x00\x00")
    # .venv/lib/site-packages/foo.py shouldn't matter
    venv_dir = tmp_path / ".venv" / "lib" / "site-packages"
    venv_dir.mkdir(parents=True)
    (venv_dir / "foo.py").write_text("# venv pkg\n")

    assert _detect_from_scratch(tmp_path) is True


def test_AC_V041_2_detect_nonexistent_dir_is_from_scratch(tmp_path) -> None:
    """A non-existent path is treated as from-scratch (consistent
    with cold-start: nothing to extend)."""
    nonexistent = tmp_path / "does-not-exist"
    assert _detect_from_scratch(nonexistent) is True


# ---- AC.V041.2 — auto-detect path -----------------------------------


def test_AC_V041_2_auto_detect_with_empty_repo_selects_from_scratch(
    tmp_path,
) -> None:
    """``from_scratch=None`` + an empty ``repo_path`` triggers
    auto-detect → from-scratch system prompt selected."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# Empty repo\n")

    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=None,
        repo_path=repo_dir,
    )

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "creating new" in system_prompt.lower() or "no existing" in system_prompt.lower(), (
        f"AC.V041.2 auto-detect — empty repo_path must select "
        f"from-scratch prompt; got: {system_prompt[:200]!r}"
    )


def test_AC_V041_2_auto_detect_with_source_repo_selects_extend(
    tmp_path,
) -> None:
    """``from_scratch=None`` + a repo containing a ``.py`` source file
    triggers auto-detect → extend-existing system prompt selected."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("def main(): pass\n")

    client = _CapturingLlmClient(_EXTEND_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=None,
        repo_path=repo_dir,
    )

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "existing codebase" in system_prompt, (
        f"AC.V041.2 auto-detect — repo with .py source must select "
        f"extend-existing prompt; got: {system_prompt[:200]!r}"
    )


def test_AC_V041_2_default_no_repo_path_preserves_extend_default() -> None:
    """``from_scratch=None`` AND ``repo_path=None`` → extend-existing
    (backward-compatible with v0.4.0 C1 callers that don't pass either).
    """
    client = _CapturingLlmClient(_EXTEND_RESPONSE)
    generate_code(_FIXTURE_DIR, llm_client=client)

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "existing codebase" in system_prompt, (
        f"AC.V041.2 default — when neither from_scratch nor repo_path "
        f"is supplied, extend-existing must be the default; got: "
        f"{system_prompt[:200]!r}"
    )


def test_AC_V041_2_explicit_flag_overrides_repo_path_auto_detect(
    tmp_path,
) -> None:
    """Explicit ``from_scratch=True`` overrides auto-detection — even
    if the ``repo_path`` contains source files, the from-scratch
    prompt is selected."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("def main(): pass\n")

    client = _CapturingLlmClient(_FROM_SCRATCH_RESPONSE)
    generate_code(
        _FIXTURE_DIR,
        llm_client=client,
        from_scratch=True,  # explicit override
        repo_path=repo_dir,
    )

    system_prompt = client.messages.last_call_kwargs.get("system", "")
    assert "no existing source tree" in system_prompt.lower() or (
        "creating new" in system_prompt.lower()
    ), (
        f"AC.V041.2 — explicit from_scratch=True must override "
        f"auto-detect; got: {system_prompt[:200]!r}"
    )
