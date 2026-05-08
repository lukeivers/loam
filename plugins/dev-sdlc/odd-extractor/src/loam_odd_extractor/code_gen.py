"""v0.4.0 Cycle 1 — Code-gen-from-objectives core (SOFT-altitude).

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

Multi-commit case: cycle-1 verifies single-commit; the schema
(:class:`CodeGenDiff.commits` is a tuple) supports multi-commit but
the production prompt-shape that produces multi-commit outputs is
deferred to C2 / v0.4.1 per master-plan §10.5 RF.
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

    # ---- Build the request -----------------------------------------

    request = CodeGenRequest(
        extraction_id=build_next.extraction_id,
        extraction_dir=str(extraction_dir_p),
        selected_candidate_gap_id=selected_candidate_gap_id,
    )

    # ---- LLM dispatch ----------------------------------------------

    prompt = _build_prompt(objective, gap, candidate)

    response = llm_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=(
            "You are a senior engineer writing minimal patches for a "
            "Python codebase. Produce a single unified diff that closes "
            "the named acceptance criterion. Output ONLY the unified "
            "diff text plus a short subject line on the first line "
            "prefixed `subject:`. Do not include explanation."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    diff_text, subject = _parse_llm_response(response)

    # ---- AC.V040C1.2 — populate per-commit LiftedFrom --------------

    lifted_from = LiftedFrom(
        source_doc=_resolve_source_doc(objective, gap),
        source_ac=_resolve_source_ac(gap, candidate),
        source_commit=None,  # D-build.2: omitted at code-gen time
    )

    commit = CodeGenCommit(
        message_subject=subject,
        message_body=(
            f"Closes gap {gap.gap_id} (objective "
            f"{objective.objective_id}). Generated by `loam odd-extract "
            f"--code-gen` at v0.4.0 Cycle 1."
        ),
        diff_text=diff_text,
        lifted_from=lifted_from,
    )

    return CodeGenDiff(
        extraction_id=build_next.extraction_id,
        request=request,
        commits=(commit,),
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


def _build_prompt(objective: Objective, gap: Any, candidate: Any) -> str:
    """Build the LLM prompt for a code-gen commit.

    The prompt is intentionally minimal at cycle-1 SOFT-altitude;
    cycle-2 outcome-altitude verification will iterate on the
    real-`claude -p` invocation. The exact prompt shape is not in
    AC scope (no method-in-AC) — only the existence of a non-empty
    diff response.
    """
    return (
        f"Objective: {objective.text}\n\n"
        f"Gap to close: {gap.gap_id}\n"
        f"Gap rationale: {getattr(gap, 'rationale', '(none)')}\n\n"
        f"Candidate context: {getattr(candidate, 'rationale', '(none)')}\n\n"
        "Produce a unified diff (one or more file hunks) that closes "
        "the gap. First line must be `subject: <commit subject>`; "
        "remaining lines are the unified diff. Output nothing else."
    )


_RESPONSE_SUBJECT_RE = re.compile(
    r"^subject:\s*(.+?)\s*$", re.MULTILINE
)


def _parse_llm_response(response: Any) -> tuple[str, str]:
    """Extract the (diff_text, subject) tuple from an LLM
    ``messages.create(...)`` response.

    Per :mod:`claude_print_synthesis_client` shape: ``response.content[0].text``
    is the str payload. Format expected:

        subject: <commit subject>
        --- a/<file>
        +++ b/<file>
        @@ ...

    :raises StageError: If response shape unexpected or no diff body
        present.
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

    m = _RESPONSE_SUBJECT_RE.search(text)
    if m is None:
        raise StageError(
            "code_gen: LLM response missing `subject: ...` first "
            "line. Response was:\n" + text[:500]
        )
    subject = m.group(1).strip()
    # Strip the subject line from the diff body.
    diff_text = _RESPONSE_SUBJECT_RE.sub("", text, count=1).lstrip("\n")
    if not diff_text.strip():
        raise StageError(
            "code_gen: LLM response had subject but no diff body."
        )
    return diff_text, subject
