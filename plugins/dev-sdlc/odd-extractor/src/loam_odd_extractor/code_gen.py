"""v0.4.0 Cycle 1 — Code-gen-from-objectives core (SOFT-altitude).
v0.4.1 — F-DESIGN-1 closure: multi-commit-per-task + from-scratch
prompt mode (per AC.V041.{1,2}).

Per cycle-1 plan-doc §1+§3+§4: takes ``objectives.yaml`` (or
``augmented-objectives.yaml``) + ``gap-inventory.yaml`` +
``build-next.yaml`` from an extraction directory + a selected
build-next candidate gap_id, and produces a :class:`CodeGenDiff`
where each :class:`CodeGenCommit` carries a ``lifted_from`` block
populated per amendment #38 ``LiftedFrom`` schema.

**Subscription-only architectural floor.** All LLM invocation is
routed through an injected ``llm_client`` parameter that matches the
``messages.create(...)`` shape :mod:`claude_print_synthesis_client`
exposes — itself a ``claude -p`` subprocess wrapper, NO Anthropic
SDK, NO ``ANTHROPIC_API_KEY``. The default ``llm_client=None`` raises
at runtime when LLM dispatch is required; production callers wire
in :class:`ClaudePrintAnthropicShimClient`. The cycle-1 SOFT-altitude
smoke (AC.V040C1.3) injects a duck-typed stub returning a controlled
diff text.

C1 deliberately does NOT exercise the live ``claude -p`` subprocess.
C2 closes the outcome-altitude AC against the real ``claude -p``
binary on a real fixture (``jsts-playwright-app``).

Per cycle-1 plan-doc §6 hard-constraint #4: any production-path
``claude -p`` invocation passes ``--strict-mcp-config`` + an empty
MCP-config tempfile per the v0.2.5 C5 propagation invariant. That
constraint binds the production wiring; cycle-1 itself stubs the
call site.

Per cycle-1 plan-doc §13 builder choices:

- D-build.1: CLI flag ``--code-gen`` on ``loam odd-extract <repo>``.
- D-build.2: ``source_commit`` is omitted at code-gen time
  (``LiftedFrom.source_commit = None``).
- D-build.3: per-commit ``objectives:`` block carrier is the
  delimited body section (``---objectives---`` / ``---objectives-end---``).
- D-build.4: synthetic fixture lives at
  ``tests/fixtures/code-gen/synthetic-v0/``.

v0.4.1 method-decisions (per AC.V041.* plan-doc §14):

- D-V041.1 (multi-commit emit shape): the production prompt instructs
  the LLM to emit ``===COMMIT===`` delimited blocks; each block
  carries a ``subject: ...`` first line plus a unified diff. The
  parser :func:`_parse_llm_response` returns ``list[tuple[diff_text,
  subject]]`` (length-1 list for single-commit responses;
  backward-compatible).
- D-V041.2 (from-scratch heuristic): explicit ``from_scratch=True``
  on :func:`generate_code` selects from-scratch prompt mode; when
  ``from_scratch=None`` (default) and a ``repo_path`` is supplied,
  auto-detect is "the repo has zero source files outside docs +
  config + .git/." When ``repo_path`` is None, default to
  extend-existing mode.
- D-V041.3 (build-next tie-breaker primary signal): handled in
  :mod:`build_next` — extends ``_tiebreak_key`` with cluster-size
  (orphan_cluster_size desc) before alphabetical fallback. See
  module-level docstring of :mod:`build_next` for the full hierarchy.

The multi-commit + from-scratch widening preserves the v0.4.0 C1+C2
single-commit + extend-existing behaviour as the default — every
existing test continues to pass without edit. v0.4.1's new tests
exercise the new paths via the same stub-injection pattern.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Protocol

import yaml

from loam.objective_tracker.spec import LiftedFrom

from .code_gen_spec import CodeGenCommit, CodeGenDiff, CodeGenRequest
from .errors import OddExtractorError, StageError
from .spec import (
    AugmentedObjectiveSet,
    BuildNextRecommendation,
    GapInventory,
    Objective,
)


# ====================================================================
# Filenames + module constants
# ====================================================================


_AUGMENTED_OBJECTIVES_FILENAME = "augmented-objectives.yaml"
_OBJECTIVES_FILENAME = "objectives.yaml"
_GAP_INVENTORY_FILENAME = "gap-inventory.yaml"
_BUILD_NEXT_FILENAME = "build-next.yaml"
_CODE_GEN_DIR_NAME = "code-gen"
_CODE_GEN_DIFF_FILENAME = "diff.patch"
_CODE_GEN_MANIFEST_FILENAME = "manifest.json"
_CODE_GEN_SCHEMA_VERSION = 1


# ====================================================================
# LLM client protocol (subscription-only; matches
# `claude_print_synthesis_client.ClaudePrintAnthropicShimClient`)
# ====================================================================


class _MessagesCreateLike(Protocol):
    """Duck-typed contract for the injectable LLM client.

    Mirrors the surface :mod:`claude_print_synthesis_client` exposes —
    a ``messages.create(...)`` returning a ``content[0].text``-shaped
    response. Cycle-1 tests inject a stub matching this shape; the
    production wiring resolves to :class:`ClaudePrintAnthropicShimClient`.
    """

    def create(self, **kwargs: Any) -> Any: ...  # pragma: no cover


class _LlmClientLike(Protocol):
    """The ``client.messages.create(...)`` shape the production code
    consumes (matches :class:`anthropic.Anthropic`'s public surface
    AND :mod:`claude_print_synthesis_client`'s subscription-routed
    shim)."""

    messages: _MessagesCreateLike


# ====================================================================
# AC.V040C1.1 — Code-gen entry point
# ====================================================================


def generate_code(
    extraction_dir: Path | str,
    *,
    selected_candidate_gap_id: str | None = None,
    llm_client: _LlmClientLike | None = None,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 8000,
    from_scratch: bool | None = None,
    repo_path: Path | str | None = None,
) -> CodeGenDiff:
    """Run the code-gen-from-objectives pipeline.

    Per AC.V040C1.1: accepts an extraction directory containing
    ``objectives.yaml`` (or ``augmented-objectives.yaml``) +
    ``gap-inventory.yaml`` + ``build-next.yaml``; produces a
    :class:`CodeGenDiff` where each commit carries an
    ``objectives:`` block per amendment #38 ``LiftedFrom`` schema.

    Per AC.V040C1.2: each :class:`CodeGenCommit.lifted_from` is
    constructed with ``source_doc`` from the originating objective's
    document path, ``source_ac`` from the build-next candidate's
    gap-id-derived AC reference, and ``source_commit=None`` per
    D-build.2 (the commit being authored does not yet have a SHA).

    Per AC.V041.1 (multi-commit-per-task): the parser consumes
    ``===COMMIT===`` delimited blocks in the LLM response; each
    block becomes one :class:`CodeGenCommit`. Single-commit
    responses (no delimiters) yield one commit (backward-compatible).

    Per AC.V041.2 (from-scratch prompt mode): when
    ``from_scratch=True`` the prompt instructs "create new files"
    + ``--- /dev/null`` source-side framing. When ``from_scratch=None``
    + ``repo_path`` is supplied, auto-detect: the repo is from-scratch
    if it has zero non-doc/non-config source files. When ``repo_path``
    is None, default to extend-existing.

    Per the subscription-only constraint: ``llm_client`` is the
    injectable LLM dispatcher matching the ``messages.create(...)``
    shape. Production wiring uses
    :class:`ClaudePrintAnthropicShimClient` (``claude -p`` subprocess);
    cycle-1 tests inject a stub.

    :param extraction_dir: Path to the extraction directory.
    :param selected_candidate_gap_id: The build-next candidate
        (gap_id) to code-gen for. If None, defaults to the
        highest-ranked candidate in build-next.yaml.
    :param llm_client: Injectable LLM client. None raises
        :class:`StageError` (production wiring must inject the
        subscription-routed client; tests inject a stub).
    :param model: Model name passed to ``messages.create(model=...)``.
        Default ``claude-sonnet-4-5`` per token-efficiency rule.
    :param max_tokens: Max-tokens parameter passed to
        ``messages.create(...)``.
    :param from_scratch: Tri-state. ``True`` forces from-scratch
        mode; ``False`` forces extend-existing mode; ``None`` (default)
        auto-detects from ``repo_path`` (or falls back to
        extend-existing when ``repo_path`` is None). Per AC.V041.2.
    :param repo_path: Optional path to the source repository.
        Used only for ``from_scratch=None`` auto-detection. When
        provided, :func:`_detect_from_scratch` examines the tree.
    :returns: :class:`CodeGenDiff` with one or more commits.
    :raises StageError: If required input files missing, no LLM
        client provided, or LLM response cannot be parsed into a
        valid diff.
    """
    extraction_dir_p = Path(extraction_dir).resolve()
    if not extraction_dir_p.is_dir():
        raise StageError(
            f"code_gen: extraction_dir does not exist or is not a "
            f"directory: {extraction_dir_p}"
        )

    if llm_client is None:
        raise StageError(
            "code_gen: llm_client is required. Production wiring must "
            "inject ClaudePrintAnthropicShimClient (subscription-routed "
            "via claude -p subprocess); tests inject a duck-typed stub "
            "matching client.messages.create(...) shape."
        )

    # ---- Load inputs (AC.V040C1.1) ---------------------------------

    objectives = _load_objectives(extraction_dir_p)
    gap_inventory = _load_gap_inventory(extraction_dir_p)
    build_next = _load_build_next(extraction_dir_p)

    # ---- Select candidate ------------------------------------------

    if selected_candidate_gap_id is None:
        if not build_next.candidates:
            raise StageError(
                "code_gen: build-next.yaml has zero candidates; "
                "cannot select a default. Run `--build-next` first or "
                "pass --candidate <gap_id>."
            )
        selected_candidate_gap_id = build_next.candidates[0].gap_id

    candidate = _find_candidate(build_next, selected_candidate_gap_id)
    gap = _find_gap(gap_inventory, selected_candidate_gap_id)
    objective = _resolve_objective(objectives, gap)

    # ---- Resolve from_scratch mode (AC.V041.2) ---------------------

    if from_scratch is None:
        if repo_path is not None:
            from_scratch = _detect_from_scratch(Path(repo_path))
        else:
            from_scratch = False

    # ---- Build the request -----------------------------------------

    request = CodeGenRequest(
        extraction_id=build_next.extraction_id,
        extraction_dir=str(extraction_dir_p),
        selected_candidate_gap_id=selected_candidate_gap_id,
    )

    # ---- LLM dispatch ----------------------------------------------

    prompt = _build_prompt(
        objective, gap, candidate, from_scratch=from_scratch
    )

    if from_scratch:
        system_prompt = (
            "You are a senior engineer creating new source files from "
            "documentation alone. There is NO existing source tree — "
            "every file you author is brand-new (`--- /dev/null` on "
            "the source side of every diff hunk). Multi-file "
            "submissions are common (e.g., a build script + a source "
            "file + a test file). Emit ONE OR MORE commits separated "
            "by a literal `===COMMIT===` line. Each commit starts with "
            "`subject: <one-line summary>` and is followed by a "
            "unified diff. Do not include any explanation outside the "
            "subject + diff."
        )
    else:
        system_prompt = (
            "You are a senior engineer writing minimal patches for an "
            "existing codebase. Produce one or more unified diffs that "
            "close the named acceptance criterion. If the change "
            "naturally decomposes into multiple commits (e.g., schema "
            "+ handler + test), emit each as a separate commit "
            "separated by a literal `===COMMIT===` line. Each commit "
            "starts with `subject: <one-line summary>` and is followed "
            "by a unified diff. Single-commit responses (no "
            "`===COMMIT===` delimiter) are still accepted. Do not "
            "include explanation outside the subject + diff."
        )

    response = llm_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    parsed = _parse_llm_response(response)

    # ---- AC.V040C1.2 + AC.V041.1 — populate per-commit LiftedFrom --

    lifted_from = LiftedFrom(
        source_doc=_resolve_source_doc(objective, gap),
        source_ac=_resolve_source_ac(gap, candidate),
        source_commit=None,  # D-build.2: omitted at code-gen time
    )

    mode_label = "from-scratch" if from_scratch else "extend-existing"
    commits: list[CodeGenCommit] = []
    for idx, (diff_text, subject) in enumerate(parsed):
        body_suffix = (
            f" (commit {idx + 1} of {len(parsed)})"
            if len(parsed) > 1
            else ""
        )
        commits.append(
            CodeGenCommit(
                message_subject=subject,
                message_body=(
                    f"Closes gap {gap.gap_id} (objective "
                    f"{objective.objective_id}). Generated by "
                    f"`loam odd-extract --code-gen` "
                    f"[{mode_label}{body_suffix}]."
                ),
                diff_text=diff_text,
                lifted_from=lifted_from,
            )
        )

    return CodeGenDiff(
        extraction_id=build_next.extraction_id,
        request=request,
        commits=tuple(commits),
    )


# ====================================================================
# Persistence (AC.V040C1.1: produces a persisted artefact)
# ====================================================================


def persist_diff(diff: CodeGenDiff, extraction_dir: Path | str) -> Path:
    """Persist a :class:`CodeGenDiff` to
    ``<extraction_dir>/code-gen/`` as ``diff.patch`` (the
    concatenated commits' diffs) plus ``manifest.json`` (the JSON
    serialisation of the diff payload, including each commit's
    ``lifted_from``).

    Returns the path to the manifest.json file.
    """
    extraction_dir_p = Path(extraction_dir).resolve()
    target_dir = extraction_dir_p / _CODE_GEN_DIR_NAME
    target_dir.mkdir(parents=True, exist_ok=True)

    diff_path = target_dir / _CODE_GEN_DIFF_FILENAME
    manifest_path = target_dir / _CODE_GEN_MANIFEST_FILENAME

    # Concatenate commits as a single .patch file with delimiters
    # between commit messages so a downstream consumer can reconstruct
    # the per-commit shape.
    parts: list[str] = []
    for c in diff.commits:
        parts.append(f"# === COMMIT START ===\n{c.render_full_message()}\n")
        parts.append(c.diff_text)
        if not c.diff_text.endswith("\n"):
            parts.append("\n")
        parts.append("# === COMMIT END ===\n")

    diff_path.write_text("".join(parts), encoding="utf-8")
    manifest_path.write_text(
        diff.model_dump_json(indent=2), encoding="utf-8"
    )
    return manifest_path


def load_diff(extraction_dir: Path | str) -> CodeGenDiff:
    """Round-trip load of a persisted :class:`CodeGenDiff` from
    ``<extraction_dir>/code-gen/manifest.json``.

    Verifies AC.V040C1.2: the per-commit ``lifted_from`` block
    round-trips cleanly through ``model_validate``.
    """
    extraction_dir_p = Path(extraction_dir).resolve()
    manifest_path = (
        extraction_dir_p / _CODE_GEN_DIR_NAME / _CODE_GEN_MANIFEST_FILENAME
    )
    if not manifest_path.is_file():
        raise StageError(
            f"code_gen: no persisted manifest at {manifest_path}"
        )
    return CodeGenDiff.model_validate(json.loads(manifest_path.read_text()))


# ====================================================================
# Per-commit `objectives:` block extraction (AC.V040C1.2)
# ====================================================================


_OBJECTIVES_BLOCK_RE = re.compile(
    r"---objectives---\s*\n(.*?)\n---objectives-end---",
    re.DOTALL,
)


def extract_objectives_block(commit_message: str) -> LiftedFrom:
    """Parse a ``---objectives---`` delimited section from a commit
    message body and return the :class:`LiftedFrom` it carries.

    Per D-build.3 (b): the delimited body section is the canonical
    carrier; this function is the round-trip read-side for AC.V040C1.2.

    :raises StageError: If the block is missing or malformed.
    """
    m = _OBJECTIVES_BLOCK_RE.search(commit_message)
    if m is None:
        raise StageError(
            "code_gen: commit message contains no ---objectives--- "
            "delimited block. The block is required per AC.V040C1.2."
        )
    yaml_text = m.group(1)
    payload = yaml.safe_load(yaml_text)
    if not isinstance(payload, dict):
        raise StageError(
            "code_gen: objectives: block must be a YAML mapping; "
            f"got {type(payload).__name__}."
        )
    # Translate `null` source_commit YAML scalar to None for LiftedFrom.
    return LiftedFrom.model_validate(payload)


# ====================================================================
# Internal helpers — input loaders
# ====================================================================


def _load_objectives(extraction_dir_p: Path) -> list[Objective]:
    """Load objectives.yaml (or augmented-objectives.yaml).

    Prefers augmented-objectives.yaml when present (it's the
    Stage-3 generate output that build-next consumes); falls back to
    objectives.yaml. Returns the list of :class:`Objective` records.
    """
    augmented_p = extraction_dir_p / _AUGMENTED_OBJECTIVES_FILENAME
    if augmented_p.is_file():
        payload = yaml.safe_load(augmented_p.read_text())
        return list(AugmentedObjectiveSet.model_validate(payload).objectives)
    plain_p = extraction_dir_p / _OBJECTIVES_FILENAME
    if plain_p.is_file():
        payload = yaml.safe_load(plain_p.read_text())
        # objectives.yaml has the same `objectives:` list shape per
        # AugmentedObjectiveSet; reuse the validator (forward-compat
        # tolerant: if the un-augmented shape lacks fields, this raises
        # at validate time and the user is steered to run `--generate`
        # first).
        return list(AugmentedObjectiveSet.model_validate(payload).objectives)
    raise StageError(
        f"code_gen: neither {_AUGMENTED_OBJECTIVES_FILENAME} nor "
        f"{_OBJECTIVES_FILENAME} found at {extraction_dir_p}. Run "
        f"`loam odd-extract <repo>` (init+analyze+generate) first."
    )


def _load_gap_inventory(extraction_dir_p: Path) -> GapInventory:
    p = extraction_dir_p / _GAP_INVENTORY_FILENAME
    if not p.is_file():
        raise StageError(
            f"code_gen: {_GAP_INVENTORY_FILENAME} not found at "
            f"{extraction_dir_p}. Run `--verify` first."
        )
    return GapInventory.model_validate(yaml.safe_load(p.read_text()))


def _load_build_next(extraction_dir_p: Path) -> BuildNextRecommendation:
    p = extraction_dir_p / _BUILD_NEXT_FILENAME
    if not p.is_file():
        raise StageError(
            f"code_gen: {_BUILD_NEXT_FILENAME} not found at "
            f"{extraction_dir_p}. Run `--build-next` first."
        )
    return BuildNextRecommendation.model_validate(yaml.safe_load(p.read_text()))


# ====================================================================
# Internal helpers — selection + provenance resolution
# ====================================================================


def _find_candidate(rec: BuildNextRecommendation, gap_id: str) -> Any:
    for c in rec.candidates:
        if c.gap_id == gap_id:
            return c
    raise StageError(
        f"code_gen: build-next.yaml has no candidate with gap_id="
        f"{gap_id!r}. Available: "
        f"{[c.gap_id for c in rec.candidates]!r}"
    )


def _find_gap(inv: GapInventory, gap_id: str) -> Any:
    for g in inv.gaps:
        if g.gap_id == gap_id:
            return g
    raise StageError(
        f"code_gen: gap-inventory.yaml has no gap with gap_id="
        f"{gap_id!r}. Available: {[g.gap_id for g in inv.gaps]!r}"
    )


def _resolve_objective(
    objectives: list[Objective], gap: Any
) -> Objective:
    """Resolve the `Objective` referenced by a `Gap.objective_id`.

    For ``implementation_orphan`` gaps (objective_id is None), the
    code-gen path is not yet supported at C1 — orphan-only gaps
    require methodology refinement (the lifted_from.source_doc is
    not derivable). Surface as :class:`StageError` for owner ruling
    at C2 / v0.4.1 patch.
    """
    if gap.objective_id is None:
        raise StageError(
            f"code_gen: gap {gap.gap_id!r} has objective_id=None "
            "(implementation_orphan gaps are not yet supported at "
            "v0.4.0 Cycle 1; surface for v0.4.1 / C2 methodology "
            "refinement). HALT."
        )
    for o in objectives:
        if o.objective_id == gap.objective_id:
            return o
    raise StageError(
        f"code_gen: gap {gap.gap_id!r} references objective_id="
        f"{gap.objective_id!r} which is not present in objectives "
        f"set. Available: "
        f"{[o.objective_id for o in objectives]!r}"
    )


def _resolve_source_doc(objective: Objective, gap: Any) -> str:
    """Resolve the `lifted_from.source_doc` for a code-gen commit.

    Per the synthetic-fixture shape: the source-doc is the path to
    the originating objectives.yaml-style document. Production
    invocations resolve to the actual `<extraction_dir>/...yaml`
    path; for cycle-1 SOFT smoke we use a stable identifier the
    fixture asserts on.

    Falls back to `objectives.yaml#<objective_id>` when no
    document-level provenance is available on the objective.
    """
    # Objective.source field exists per spec.py — `extracted` /
    # `added_by_user` / etc. We use it as a sub-key on the source_doc
    # string when present.
    src = getattr(objective, "source", None)
    if src:
        return f"objectives.yaml#{objective.objective_id}::{src}"
    return f"objectives.yaml#{objective.objective_id}"


def _resolve_source_ac(gap: Any, candidate: Any) -> str:
    """Resolve the `lifted_from.source_ac` for a code-gen commit.

    Per amendment #38: `source_ac` is "the clause/AC label inside
    the source document this record was lifted from." For code-gen,
    the originating AC is the gap (the named gap is the AC the
    code-gen commit closes). Format: `<gap_id>` (e.g.,
    `G.BACKING.o-security-1`).
    """
    return gap.gap_id


# ====================================================================
# Internal helpers — prompt + response parsing
# ====================================================================


def _build_prompt(
    objective: Objective,
    gap: Any,
    candidate: Any,
    *,
    from_scratch: bool = False,
) -> str:
    """Build the LLM prompt for a code-gen commit.

    Per AC.V041.2: the prompt branches on ``from_scratch``:

    - ``from_scratch=False`` (default; v0.4.0 C1+C2 shape) — the
      prompt instructs "produce a unified diff" assuming an
      existing source tree. Multi-commit emission via
      ``===COMMIT===`` delimiter (v0.4.1 widening) is opt-in for
      the LLM when the change naturally decomposes.
    - ``from_scratch=True`` (v0.4.1 NEW) — the prompt instructs
      "create new files; there is no existing source tree." Source
      side of every hunk is ``--- /dev/null``. Multi-commit
      emission is encouraged so a build-script + source-file +
      test-file submission can land as three commits.

    The exact prompt shape is not in AC scope (no method-in-AC) —
    only the AC contracts on output shape (multi-commit-parseable
    + from-scratch-marker present) bind the builder.
    """
    common_header = (
        f"Objective: {objective.text}\n\n"
        f"Gap to close: {gap.gap_id}\n"
        f"Gap rationale: {getattr(gap, 'rationale', '(none)')}\n\n"
        f"Candidate context: {getattr(candidate, 'rationale', '(none)')}\n\n"
    )
    if from_scratch:
        return (
            common_header
            + "There is NO existing source tree. Create new files "
            "from scratch. The source side of every diff hunk MUST be "
            "`--- /dev/null` (every file is brand-new). The objective "
            "may require multiple files (e.g., a build script + a "
            "source file + a test file) — when it does, emit each as "
            "a SEPARATE commit, separated by a literal line "
            "`===COMMIT===` (no leading or trailing whitespace on the "
            "delimiter line). Each commit starts with "
            "`subject: <one-line summary>` followed by a blank line "
            "then the unified diff. Output ONLY commits — no "
            "explanation, no markdown fence."
        )
    return (
        common_header
        + "Produce a unified diff (one or more file hunks) that closes "
        "the gap. If the change naturally decomposes into multiple "
        "commits (e.g., schema + handler + test), emit each as a "
        "separate commit separated by a literal line `===COMMIT===` "
        "(no leading or trailing whitespace on the delimiter line). "
        "Each commit starts with `subject: <one-line summary>` "
        "followed by a blank line then the unified diff. Single-commit "
        "responses (no `===COMMIT===` delimiter) are still accepted "
        "for changes that don't naturally decompose. Output ONLY "
        "commits — no explanation, no markdown fence."
    )


_RESPONSE_SUBJECT_RE = re.compile(
    r"^subject:\s*(.+?)\s*$", re.MULTILINE
)
_COMMIT_DELIMITER_RE = re.compile(r"^===COMMIT===\s*$", re.MULTILINE)


def _parse_llm_response(response: Any) -> list[tuple[str, str]]:
    """Extract the list of ``(diff_text, subject)`` tuples from an
    LLM ``messages.create(...)`` response.

    Per AC.V041.1: the response may carry one or more commits
    separated by ``===COMMIT===`` delimiters. Single-commit responses
    (no delimiter present) yield a length-1 list (backward-compatible
    with v0.4.0 C1+C2's single-tuple contract — callers iterate the
    list and produce one :class:`CodeGenCommit` per entry).

    Per :mod:`claude_print_synthesis_client` shape: ``response.content[0].text``
    is the str payload. Format expected per commit:

        subject: <commit subject>
        --- a/<file>     # or `--- /dev/null` in from-scratch mode
        +++ b/<file>
        @@ ...

    Multi-commit responses interleave additional commits separated by
    a sole ``===COMMIT===`` line.

    :raises StageError: If response shape unexpected, no commit
        contains a ``subject:`` line, or any commit has empty diff
        body.
    """
    try:
        text = response.content[0].text
    except (AttributeError, IndexError, TypeError) as e:
        raise StageError(
            f"code_gen: LLM response shape unexpected: {e}. Expected "
            "`response.content[0].text` -> str."
        ) from e

    if not isinstance(text, str) or not text.strip():
        raise StageError(
            "code_gen: LLM response text empty or non-string."
        )

    # Split on the multi-commit delimiter. A response without the
    # delimiter is a single-commit response; the split yields a
    # length-1 list of the entire payload.
    parts = _COMMIT_DELIMITER_RE.split(text)
    out: list[tuple[str, str]] = []
    for idx, part in enumerate(parts):
        part = part.strip("\n")
        if not part.strip():
            # Empty segment (e.g., trailing delimiter) — skip silently.
            continue
        m = _RESPONSE_SUBJECT_RE.search(part)
        if m is None:
            raise StageError(
                f"code_gen: LLM response commit segment {idx + 1} of "
                f"{len(parts)} missing `subject: ...` line. Segment "
                f"was:\n" + part[:500]
            )
        subject = m.group(1).strip()
        # Strip the subject line from the diff body.
        diff_text = _RESPONSE_SUBJECT_RE.sub("", part, count=1).lstrip("\n")
        if not diff_text.strip():
            raise StageError(
                f"code_gen: LLM response commit segment {idx + 1} had "
                f"subject but no diff body."
            )
        out.append((diff_text, subject))

    if not out:
        raise StageError(
            "code_gen: LLM response had no parseable commit segments. "
            "Response was:\n" + text[:500]
        )
    return out


# ====================================================================
# AC.V041.2 — From-scratch detection
# ====================================================================


# Source-file extensions that count as "real source" for the
# extend-existing detection. Doc/config/build-meta files do NOT count.
_SOURCE_FILE_EXTENSIONS = frozenset({
    ".py", ".pyi",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".rb", ".erb",
    ".go",
    ".rs",
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp",
    ".java", ".kt", ".scala",
    ".swift",
    ".cs",
    ".php",
    ".pl", ".pm",
    ".sh", ".bash", ".zsh",
    ".lua",
    ".elm",
    ".clj", ".cljs",
    ".ex", ".exs",
    ".hs",
    ".ml", ".mli",
    ".sql",
})

# Directory names skipped during from-scratch detection.
_SKIPPED_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv", ".venv", "env", ".env",
    "build", "dist", "target",
    ".loam",
})


def _detect_from_scratch(repo_path: Path) -> bool:
    """Auto-detect from-scratch mode for a repo.

    Per AC.V041.2: returns True when the repo has zero source files
    (per :data:`_SOURCE_FILE_EXTENSIONS`) outside skipped directories
    (per :data:`_SKIPPED_DIRECTORIES`). Markdown / YAML / TOML / JSON
    config files don't count as source — a docs-only repo with
    `README.md` + `SPEC.md` + `pyproject.toml` is from-scratch.

    :param repo_path: Path to the source repository.
    :returns: True if from-scratch (no source files); False if
        extend-existing (≥1 source file).
    """
    if not repo_path.is_dir():
        # Non-existent or not-a-directory → treat as from-scratch
        # (consistent with cold-start: there's nothing to extend).
        return True
    for entry in repo_path.rglob("*"):
        if entry.is_dir():
            continue
        # Skip files under skipped directories.
        rel_parts = entry.relative_to(repo_path).parts
        if any(part in _SKIPPED_DIRECTORIES for part in rel_parts[:-1]):
            continue
        if entry.suffix.lower() in _SOURCE_FILE_EXTENSIONS:
            return False
    return True
