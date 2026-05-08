"""v0.4.0 Cycle 1 — Code-gen Pydantic shapes.

Per cycle-1 plan-doc §3 fence + AC.V040C1.{1,2}: structural contracts
for the code-gen-from-objectives pipeline. Consumes:

- ``BuildNextRecommendation`` from :mod:`loam_odd_extractor.spec`
  (sealed shape from v0.2.4 Cycle 3).
- ``LiftedFrom`` from :mod:`loam.objective_tracker.spec`
  (sealed shape from amendment #38).

Produces:

- :class:`CodeGenRequest` — the typed input to ``generate_code(...)``.
- :class:`CodeGenCommit` — one commit in the produced diff, carrying
  its ``lifted_from`` provenance pointer.
- :class:`CodeGenDiff` — the deliverable artefact (ordered tuple of
  commits + the unified-diff text + the originating extraction id).

The Pydantic round-trip + per-commit ``lifted_from`` block-population
is the AC.V040C1.2 contract; the synthetic-fixture smoke
(AC.V040C1.3) constructs a ``CodeGenDiff`` from a stub-injected LLM
client and asserts the block round-trips through Pydantic.

NO Anthropic SDK, NO ``ANTHROPIC_API_KEY`` — the LLM client is the
injectable parameter on :func:`code_gen.generate_code`; production
wiring uses :mod:`claude_print_synthesis_client`. Cycle-1 tests pass
a duck-typed stub matching the ``messages.create(...)`` shape.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from loam.objective_tracker.spec import LiftedFrom


# ---- CodeGenRequest -------------------------------------------------


class CodeGenRequest(BaseModel):
    """Typed input to :func:`code_gen.generate_code`.

    Per AC.V040C1.1: a code-gen invocation accepts an extraction
    directory containing ``objectives.yaml`` (or
    ``augmented-objectives.yaml``) + ``gap-inventory.yaml`` +
    ``build-next.yaml``. This model wraps the resolved-and-validated
    inputs.

    Stored on disk only as an audit echo; the canonical inputs live
    at the extraction directory's per-stage YAML files.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    extraction_id: str = Field(min_length=1)
    extraction_dir: str = Field(min_length=1)
    """Absolute path string to the extraction directory."""
    selected_candidate_gap_id: str = Field(min_length=1)
    """The build-next candidate selected for code-gen (gap_id)."""


# ---- CodeGenCommit --------------------------------------------------


class CodeGenCommit(BaseModel):
    """One commit in the produced :class:`CodeGenDiff`.

    Per AC.V040C1.2: each commit carries an ``objectives:`` block
    populated per amendment #38 ``LiftedFrom`` schema. The block is
    written into the commit-message body via the delimited-section
    carrier (D-build.3 choice (b)).

    Per the dispatcher recommendation D-build.2 (a):
    ``lifted_from.source_commit`` is omitted at code-gen time
    (defaults to ``None`` on the LiftedFrom model). Future
    enhancement: post-write rewrite to populate after the commit
    SHA exists.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    message_subject: str = Field(min_length=1)
    """The commit-message subject line."""

    message_body: str = Field(default="")
    """The commit-message body (excluding the objectives: delimited
    section, which is appended at serialisation time)."""

    diff_text: str = Field(min_length=1)
    """The unified-diff text for this commit (one or more file
    hunks)."""

    lifted_from: LiftedFrom
    """Provenance pointer per amendment #38. ``source_commit`` is
    None at code-gen time (the commit being authored does not yet
    have a SHA)."""

    def render_full_message(self) -> str:
        """Render the full commit message including the
        ``---objectives---`` delimited section.

        Format::

            <subject>

            <body>

            ---objectives---
            source_doc: <doc>
            source_ac: <ac>
            source_commit: null
            ---objectives-end---

        Per D-build.3 choice (b): structured commit-message body
        section with delimiters. Multiline YAML preserves the
        LiftedFrom shape cleanly. Extraction by regex on the
        delimited block.
        """
        body_part = f"\n\n{self.message_body}" if self.message_body else ""
        # Render LiftedFrom as YAML-shaped block. We hand-render rather
        # than depend on yaml.dump to keep ordering deterministic + the
        # parser regex simple.
        sc = self.lifted_from.source_commit
        sc_repr = "null" if sc is None else sc
        objectives_block = (
            "\n\n---objectives---\n"
            f"source_doc: {self.lifted_from.source_doc}\n"
            f"source_ac: {self.lifted_from.source_ac}\n"
            f"source_commit: {sc_repr}\n"
            "---objectives-end---\n"
        )
        return f"{self.message_subject}{body_part}{objectives_block}"


# ---- CodeGenDiff ----------------------------------------------------


class CodeGenDiff(BaseModel):
    """The deliverable artefact: ordered tuple of commits + the
    aggregate unified-diff text + the originating extraction id.

    Per AC.V040C1.1: code-gen produces "a unified diff or branch as a
    persisted artefact." This model is the in-memory shape; the
    persisted form is whatever :mod:`code_gen.persist_diff` writes
    (e.g. ``<extraction_dir>/code-gen/diff.patch`` plus a per-commit
    manifest). Cycle 1 verifies the in-memory shape; on-disk
    persistence shape is method (builder's call within fence).

    Per AC.V040C1.2: each ``CodeGenCommit.lifted_from`` populates
    via ``LiftedFrom`` schema; round-trip preservation is verified
    at AC.V040C1.3 smoke time.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    extraction_id: str = Field(min_length=1)
    request: CodeGenRequest
    commits: tuple[CodeGenCommit, ...] = Field(min_length=1)
    """Ordered tuple of commits the code-gen pipeline produced.
    Single-commit case is the C1 baseline; multi-commit case is
    attempted but may be deferred to C2 / v0.4.1 if the per-commit
    ``lifted_from`` shape requires methodology refinement."""
