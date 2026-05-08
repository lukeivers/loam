"""AC.V040C1.3 — SOFT-altitude smoke vs synthetic fixture.

Per cycle-1 plan-doc §4 AC.V040C1.3: a smoke test invokes the
code-gen entry-point against the synthetic fixture at
``tests/fixtures/code-gen/synthetic-v0/``. LLM dispatch is stubbed
via a duck-typed ``messages.create()`` returning a controlled diff.

Test asserts:

1. Entry-point produces a non-empty diff/branch artefact.
2. Each commit's ``objectives:`` block validates via
   ``LiftedFrom.model_validate``.
3. ``lifted_from.source_doc`` matches the source objective's origin
   doc.
4. ``lifted_from.source_ac`` matches the source build-next
   candidate's gap-id-derived AC reference.

`outcome-altitude: true` BUT against synthetic fixture only — C2's
AC.V040C2.* closes the real-world outcome-altitude requirement with
real ``claude -p`` + real ``jsts-playwright-app`` fixture.

NO real ``claude -p`` invocation in this module. NO Anthropic SDK.
NO ``ANTHROPIC_API_KEY``. The stub is the LLM dispatch surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loam.objective_tracker.spec import LiftedFrom

from loam_odd_extractor.code_gen import (
    extract_objectives_block,
    generate_code,
    persist_diff,
    load_diff,
)
from loam_odd_extractor.code_gen_spec import CodeGenDiff


_FIXTURE_DIR = (
    Path(__file__).parent / "fixtures" / "code-gen" / "synthetic-v0"
)


# ---- Stub LLM client (duck-typed) -----------------------------------


class _StubResponseBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _StubResponse:
    def __init__(self, text: str) -> None:
        self.content = [_StubResponseBlock(text)]
        # Mirror the usage shape claude_print_synthesis_client returns.
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


_CONTROLLED_DIFF_RESPONSE = (
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


# ---- AC tests --------------------------------------------------------


def test_AC_V040C1_3_fixture_exists() -> None:
    """Sanity: the synthetic fixture exists on disk."""
    assert _FIXTURE_DIR.is_dir(), (
        f"synthetic-v0 fixture must exist at {_FIXTURE_DIR}"
    )
    for required in (
        "augmented-objectives.yaml",
        "gap-inventory.yaml",
        "build-next.yaml",
    ):
        p = _FIXTURE_DIR / required
        assert p.is_file(), f"required fixture file missing: {p}"


def test_AC_V040C1_3_smoke_produces_non_empty_diff() -> None:
    """End-to-end: generate_code against synthetic fixture +
    stub-injected client produces a non-empty CodeGenDiff with
    at least one commit."""
    client = _StubLlmClient(_CONTROLLED_DIFF_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    assert isinstance(diff, CodeGenDiff)
    assert len(diff.commits) >= 1, (
        "AC.V040C1.3 — generate_code must produce at least one commit"
    )
    assert diff.commits[0].diff_text.strip() != "", (
        "commit diff_text must be non-empty"
    )
    assert "@@" in diff.commits[0].diff_text, (
        "commit diff_text must look like a unified diff"
    )


def test_AC_V040C1_3_lifted_from_validates() -> None:
    """Per AC.V040C1.3 #2: the per-commit lifted_from validates via
    LiftedFrom.model_validate (already covered by Pydantic
    construction; this test exercises the round-trip via the
    rendered commit message)."""
    client = _StubLlmClient(_CONTROLLED_DIFF_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)

    commit = diff.commits[0]
    msg = commit.render_full_message()
    parsed = extract_objectives_block(msg)
    assert isinstance(parsed, LiftedFrom)
    assert parsed == commit.lifted_from, (
        "round-trip from CodeGenCommit → rendered message → "
        "extract_objectives_block must preserve LiftedFrom"
    )


def test_AC_V040C1_3_source_doc_matches_objective_origin() -> None:
    """Per AC.V040C1.3 #3: lifted_from.source_doc references the
    originating objective."""
    client = _StubLlmClient(_CONTROLLED_DIFF_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)
    commit = diff.commits[0]

    # The synthetic fixture has one objective: O.greeting.1 with
    # source="extracted". The code_gen module's _resolve_source_doc
    # fallback constructs `objectives.yaml#<objective_id>::<source>`.
    assert "O.greeting.1" in commit.lifted_from.source_doc, (
        f"AC.V040C1.3 — source_doc must reference originating "
        f"objective_id; got {commit.lifted_from.source_doc!r}"
    )


def test_AC_V040C1_3_source_ac_matches_gap_id() -> None:
    """Per AC.V040C1.3 #4: lifted_from.source_ac references the
    source build-next candidate's gap-id-derived AC reference."""
    client = _StubLlmClient(_CONTROLLED_DIFF_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)
    commit = diff.commits[0]

    # _resolve_source_ac uses the gap_id directly. The synthetic
    # fixture's only candidate has gap_id=G.BACKING.o-greeting-1.
    assert commit.lifted_from.source_ac == "G.BACKING.o-greeting-1", (
        f"AC.V040C1.3 — source_ac must equal the gap_id; got "
        f"{commit.lifted_from.source_ac!r}"
    )


def test_AC_V040C1_3_source_commit_null_at_code_gen_time() -> None:
    """Per D-build.2 (a): source_commit is omitted at code-gen time."""
    client = _StubLlmClient(_CONTROLLED_DIFF_RESPONSE)
    diff = generate_code(_FIXTURE_DIR, llm_client=client)
    commit = diff.commits[0]
    assert commit.lifted_from.source_commit is None, (
        "D-build.2 (a) — source_commit must be None at code-gen time"
    )


def test_AC_V040C1_3_persist_round_trip(tmp_path) -> None:
    """The produced diff persists + reloads via persist_diff/load_diff
    with no LiftedFrom drift (close to outcome-altitude probe shape
    AC.V040C2.* will exercise against real claude -p)."""
    # Copy fixture to tmp_path so persist_diff can write under it
    # without polluting the source tree.
    import shutil

    target = tmp_path / "extraction"
    shutil.copytree(_FIXTURE_DIR, target)

    client = _StubLlmClient(_CONTROLLED_DIFF_RESPONSE)
    diff = generate_code(target, llm_client=client)
    persist_diff(diff, target)
    loaded = load_diff(target)

    assert loaded.commits[0].lifted_from == diff.commits[0].lifted_from
    assert loaded.commits[0].diff_text == diff.commits[0].diff_text
    # Manifest sidecar exists.
    assert (target / "code-gen" / "manifest.json").is_file()
    assert (target / "code-gen" / "diff.patch").is_file()


def test_AC_V040C1_3_no_anthropic_sdk_imported() -> None:
    """Subscription-only constraint: code_gen module does NOT
    import the Anthropic SDK directly (would require
    ANTHROPIC_API_KEY).

    Reads the source as a parsed AST to distinguish actual import
    statements + os.environ references from documentation strings
    that name the prohibited surface.
    """
    import ast
    from loam_odd_extractor import code_gen as cg_module

    src = Path(cg_module.__file__).read_text()
    tree = ast.parse(src)

    forbidden_imports = {"anthropic"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in forbidden_imports, (
                    f"subscription-only constraint violated: "
                    f"code_gen.py imports `{alias.name}`. Must route "
                    f"through claude_print_synthesis_client."
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            assert root not in forbidden_imports, (
                f"subscription-only constraint violated: code_gen.py "
                f"imports from `{node.module}`. Must route through "
                f"claude_print_synthesis_client."
            )

    # Cross-check: no os.environ['ANTHROPIC_API_KEY'] / os.getenv(...)
    # reference. We allow the string in docstrings (the docstring
    # names what the module DOES NOT do) but disallow it inside
    # function bodies / Subscript / Call args.
    class _ApiKeyRefVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.violations: list[str] = []

        def visit_Constant(self, node: ast.Constant) -> None:  # type: ignore[override]
            if (
                isinstance(node.value, str)
                and node.value == "ANTHROPIC_API_KEY"
            ):
                # Allow the string only inside a docstring (module-
                # level Expr). We approximate "in docstring" by
                # walking the parents — but ast nodes don't carry
                # parents; approximate by allowing the literal only
                # if it's inside the module-level docstring (first
                # Expr of the module body).
                self.violations.append(
                    "ANTHROPIC_API_KEY string literal found in code "
                    "(only allowed in docstrings)"
                )

    # Skip the module docstring (tree.body[0] is Expr containing
    # Constant str — that's the docstring).
    body_to_check = tree.body[1:] if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ) else tree.body
    for stmt in body_to_check:
        # Skip nested docstrings inside class/function defs by
        # walking only the executable subtree (not the docstring
        # which is the first Expr of a body).
        v = _ApiKeyRefVisitor()
        # Walk the stmt skipping its own docstring if it's a
        # function/class def.
        sub_body = getattr(stmt, "body", None)
        if (
            isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and sub_body
            and isinstance(sub_body[0], ast.Expr)
            and isinstance(getattr(sub_body[0], "value", None), ast.Constant)
            and isinstance(sub_body[0].value.value, str)
        ):
            for inner in sub_body[1:]:
                v.visit(inner)
        else:
            v.visit(stmt)
        assert not v.violations, (
            f"subscription-only constraint violated in {stmt}: "
            f"{v.violations}"
        )


def test_AC_V040C1_3_llm_client_required() -> None:
    """generate_code raises if no llm_client is injected (production
    wiring must inject ClaudePrintSynthesisClient; this test verifies
    the contract)."""
    from loam_odd_extractor.errors import StageError

    with pytest.raises(StageError) as exc_info:
        generate_code(_FIXTURE_DIR, llm_client=None)
    assert "llm_client" in str(exc_info.value).lower()
