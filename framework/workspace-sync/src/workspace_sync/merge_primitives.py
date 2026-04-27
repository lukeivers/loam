"""α.2 — Classifier + deterministic merge primitives + verifier.

Implements FUTURE_IDEAS Idea 20 (LLM-as-classifier + LLM-as-verifier,
never LLM-as-generator) for the workspace-sync resolver. The pattern
collapses generator-shaped problems into two small-output LLM calls
bracketing a deterministic primitive:

  1. classify (~50 token output) — tag the file's structural class.
  2. apply (deterministic, ~0.01s, free, audit-grade reproducible) —
     the matching primitive runs.
  3. verify (~200 token output) — check that the deterministic step
     preserved meaning; rubber-stamp prevention via a NAMED-class
     input + class_mismatch flag forcing passed=False
     (Hard Constraint #8 binding).
  4. apply or fall back — verify passes → accept; verify fails OR
     classifier returns "unknown" OR primitive raises
     PrimitiveDeclined → fall back to today's LLM-generator path
     (preserves the correctness ceiling, AC.WSα.6).

Five-class taxonomy (D-build.4 / AC.WSα.3 minimum):

  - append-only-list — markdown bullet lists, FUTURE_IDEAS_DRAFT
    sections, etc. Merged via concatenate-with-dedupe by stripped
    first-line of each bullet.
  - log — line-oriented append-only logs (ndjson, run-history files).
    Merged via line-set-union preserving canonical order.
  - tracker-table — markdown pipe-tables with header rows. Merged
    via header-must-match + body-row-set-union.
  - free-prose — no deterministic primitive; primitive declines and
    the orchestrator falls back to AC.WSα.6 LLM-generator.
  - unknown — same fall-through.

D-2 LOCKED 2026-04-27: classify on truncated 50-first + 10-last
lines per side; verifier reads full content + NAMED class +
primitive trace.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .merge_resolver import LLMClient, ResolverFailure


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------


# Five-class taxonomy. Distinct from sync_protected.FileClass (A/B/C);
# named MergeClass to avoid collision.
MergeClass = Literal[
    "append-only-list",
    "log",
    "tracker-table",
    "free-prose",
    "unknown",
]


class MergeClassification(BaseModel):
    """Result of the classify-call (AC.WSα.3)."""

    model_config = ConfigDict(extra="forbid")

    merge_class: MergeClass
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class PrimitiveTrace(BaseModel):
    """Audit-grade trace for a deterministic merge primitive."""

    model_config = ConfigDict(extra="forbid")

    operation: str  # short identifier, e.g. "append-only-list:concat-dedup"
    canonical_sha256: str
    workspace_sha256: str
    merged_sha256: str
    note: str = ""


class MergeVerification(BaseModel):
    """Result of the verify-call (AC.WSα.5).

    ``class_mismatch`` is the FIRST verification step (Hard
    Constraint #8): the verifier reads the candidate plus both
    sides plus the NAMED class and asks "is this file actually
    structurally a {class}?" If no, sets class_mismatch=True
    (and the model_validator forces passed=False — rubber-stamp
    prevention).
    """

    model_config = ConfigDict(extra="forbid")

    passed: bool
    class_mismatch: bool
    concerns: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _class_mismatch_forces_fail(self) -> "MergeVerification":
        if self.class_mismatch and self.passed:
            raise ValueError(
                "class_mismatch=True requires passed=False "
                "(Hard Constraint #8 rubber-stamp prevention)"
            )
        return self


class MergeClassDeclined(Exception):
    """Raised by deterministic primitives when the file structure is
    incompatible with the named class (e.g., append-only-list prefix
    mismatch, tracker-table header mismatch, free-prose / unknown).

    The orchestrator translates the exception's message into the
    audit's ``fallback_reason: "primitive-failed: <message>"`` field.
    """


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _truncate(text: str, head_lines: int, tail_lines: int) -> str:
    """Return head_lines + truncation marker + tail_lines.

    When the file is small enough that head + tail covers it, returns
    the original text unchanged. Otherwise emits a literal marker
    line ``... <middle truncated, M lines> ...`` so the LLM sees
    structure honestly (D-2 LOCKED).
    """
    lines = text.splitlines(keepends=True)
    if len(lines) <= head_lines + tail_lines:
        return text
    head = "".join(lines[:head_lines])
    tail = "".join(lines[-tail_lines:])
    middle_count = len(lines) - head_lines - tail_lines
    return (
        head
        + f"... <middle truncated, {middle_count} lines> ...\n"
        + tail
    )


# ----------------------------------------------------------------------
# Per-class deterministic primitives (D-build.5)
# ----------------------------------------------------------------------


def _split_bullets(text: str) -> tuple[str, list[str], str]:
    """Split a markdown bullet-list into (prefix, bullets, suffix).

    A bullet starts at column 0 with one of ``- ``, ``* ``, or ``+ ``;
    continuation lines (indented) belong to the preceding bullet. The
    prefix is the text before the first bullet; the suffix is text
    after the last bullet's continuation.

    Returns:
        prefix — text before first bullet (may be empty).
        bullets — list of bullet blocks (each bullet's first line + any
                  indented continuation lines).
        suffix — text after the last bullet.
    """
    lines = text.splitlines(keepends=True)
    bullet_starts: list[int] = []
    for i, ln in enumerate(lines):
        stripped = ln.lstrip()
        if (
            ln.startswith(("- ", "* ", "+ "))
            and stripped.startswith(("- ", "* ", "+ "))
            and not ln[0].isspace()
        ):
            bullet_starts.append(i)
    if not bullet_starts:
        return text, [], ""
    prefix = "".join(lines[: bullet_starts[0]])
    bullets: list[str] = []
    for idx, start in enumerate(bullet_starts):
        end = bullet_starts[idx + 1] if idx + 1 < len(bullet_starts) else None
        if end is None:
            # Last bullet: scan forward until a non-indented, non-blank line.
            scan_end = len(lines)
            for j in range(start + 1, len(lines)):
                line = lines[j]
                if line.strip() == "":
                    continue  # blank line stays with bullet
                if line[0].isspace():
                    continue  # indented continuation
                # Non-indented non-blank → end of bullet.
                scan_end = j
                break
            bullets.append("".join(lines[start:scan_end]))
            suffix_start = scan_end
        else:
            bullets.append("".join(lines[start:end]))
    last_end = bullet_starts[-1] + len(bullets[-1].splitlines(keepends=True))
    suffix = "".join(lines[last_end:])
    return prefix, bullets, suffix


def merge_append_only_list(
    canonical_text: str, workspace_text: str
) -> tuple[str, PrimitiveTrace]:
    """Concatenate-with-dedupe by bullet first-line.

    Algorithm:
      1. Split each side into (prefix, bullets, suffix).
      2. Prefix MUST match across both sides; if not, decline.
      3. Output bullets = canonical bullets + (workspace bullets whose
         stripped first line is not already present in canonical).
      4. Output suffix = canonical suffix.
      5. Reassemble: prefix + bullets + suffix.

    Idempotent: running ``merge(merge(c, w), w) == merge(c, w)``
    because dedupe keys on canonical-then-workspace order; re-running
    with the merge as canonical leaves workspace bullets that already
    landed unchanged.
    """
    c_prefix, c_bullets, c_suffix = _split_bullets(canonical_text)
    w_prefix, w_bullets, _w_suffix = _split_bullets(workspace_text)
    if c_prefix.rstrip() != w_prefix.rstrip():
        raise MergeClassDeclined(
            "append-only-list: prefix mismatch — file structure differs "
            "before the first bullet"
        )
    if not c_bullets and not w_bullets:
        raise MergeClassDeclined(
            "append-only-list: neither side has any bullets"
        )

    # Dedupe key: stripped first line of the bullet block.
    canonical_keys = {
        b.splitlines()[0].strip() if b.splitlines() else b.strip()
        for b in c_bullets
    }
    extras: list[str] = []
    for w in w_bullets:
        first_line = (w.splitlines()[0].strip() if w.splitlines() else w.strip())
        if first_line not in canonical_keys:
            extras.append(w)
    merged = c_prefix + "".join(c_bullets) + "".join(extras) + c_suffix
    return (
        merged,
        PrimitiveTrace(
            operation="append-only-list:concat-dedup",
            canonical_sha256=_sha256(canonical_text),
            workspace_sha256=_sha256(workspace_text),
            merged_sha256=_sha256(merged),
            note=(
                f"canonical_bullets={len(c_bullets)} "
                f"workspace_bullets={len(w_bullets)} "
                f"workspace_additions={len(extras)}"
            ),
        ),
    )


def merge_log(
    canonical_text: str, workspace_text: str
) -> tuple[str, PrimitiveTrace]:
    """Line-set-union preserving canonical order.

    Algorithm:
      1. Split each side on ``\\n`` (line-oriented).
      2. Output = canonical lines + workspace lines not in canonical
         (set membership; preserves canonical order; workspace
         additions appended in workspace-order).
      3. Trailing newline normalisation: if either side ends with a
         newline, the merged output ends with a newline.
    """
    c_lines = canonical_text.splitlines()
    w_lines = workspace_text.splitlines()
    c_set = set(c_lines)
    extras = [ln for ln in w_lines if ln not in c_set]
    merged_lines = c_lines + extras
    merged = "\n".join(merged_lines)
    if canonical_text.endswith("\n") or workspace_text.endswith("\n"):
        merged = merged + "\n"
    return (
        merged,
        PrimitiveTrace(
            operation="log:line-union",
            canonical_sha256=_sha256(canonical_text),
            workspace_sha256=_sha256(workspace_text),
            merged_sha256=_sha256(merged),
            note=(
                f"canonical_lines={len(c_lines)} "
                f"workspace_lines={len(w_lines)} "
                f"workspace_additions={len(extras)}"
            ),
        ),
    )


def merge_tracker_table(
    canonical_text: str, workspace_text: str
) -> tuple[str, PrimitiveTrace]:
    """Markdown pipe-table merge.

    Algorithm:
      1. Parse each side: header row, separator row, body rows.
      2. Header rows MUST match (same column count + same column
         names); if not, decline.
      3. Output body = canonical body + (workspace body rows whose
         full-row-string is not already in canonical body); preserves
         canonical order.
      4. Reassemble: header + separator + merged body.
    """

    def _parse(text: str) -> tuple[list[str], list[str]] | None:
        lines = [ln for ln in text.splitlines() if ln.strip().startswith("|")]
        if len(lines) < 2:
            return None
        header = lines[0]
        separator = lines[1]
        # Separator must contain dashes (markdown convention).
        if "-" not in separator:
            return None
        body = lines[2:]
        return ([header, separator], body)

    c_parsed = _parse(canonical_text)
    w_parsed = _parse(workspace_text)
    if c_parsed is None or w_parsed is None:
        raise MergeClassDeclined(
            "tracker-table: one or both sides not a recognisable "
            "markdown pipe-table"
        )
    c_header_block, c_body = c_parsed
    w_header_block, w_body = w_parsed
    if c_header_block != w_header_block:
        raise MergeClassDeclined(
            "tracker-table: header rows differ across canonical and "
            "workspace"
        )

    c_set = set(c_body)
    extras = [r for r in w_body if r not in c_set]
    merged_body = c_body + extras
    merged_lines = c_header_block + merged_body
    merged = "\n".join(merged_lines)
    if canonical_text.endswith("\n") or workspace_text.endswith("\n"):
        merged = merged + "\n"
    return (
        merged,
        PrimitiveTrace(
            operation="tracker-table:row-union",
            canonical_sha256=_sha256(canonical_text),
            workspace_sha256=_sha256(workspace_text),
            merged_sha256=_sha256(merged),
            note=(
                f"canonical_rows={len(c_body)} "
                f"workspace_rows={len(w_body)} "
                f"workspace_additions={len(extras)}"
            ),
        ),
    )


def run_primitive(
    merge_class: str, canonical_text: str, workspace_text: str
) -> tuple[str, PrimitiveTrace]:
    """Dispatch to the deterministic primitive for ``merge_class``.

    Raises ``MergeClassDeclined`` for free-prose, unknown, or any
    primitive's own decline (prefix / header mismatch).
    """
    if merge_class == "append-only-list":
        return merge_append_only_list(canonical_text, workspace_text)
    if merge_class == "log":
        return merge_log(canonical_text, workspace_text)
    if merge_class == "tracker-table":
        return merge_tracker_table(canonical_text, workspace_text)
    if merge_class in ("free-prose", "unknown"):
        raise MergeClassDeclined(
            f"{merge_class}: no deterministic primitive — fall through to "
            "LLM-generator"
        )
    raise MergeClassDeclined(f"unrecognised merge_class: {merge_class!r}")


# ----------------------------------------------------------------------
# Classify-call (D-build.6)
# ----------------------------------------------------------------------


_CLASSIFY_PROMPT = """\
You are classifying the structural shape of a file with a workspace-vs-canonical merge conflict. Return a JSON MergeClassification object.

File path: {path}

Class definitions (choose ONE):
  - append-only-list: file is structurally a flat list of items with one entry per bullet (markdown ``- ``, ``* ``, or ``+ `` at column 0). Items added on either side should be unioned. Examples: FUTURE_IDEAS_DRAFT.md sections, todo lists, simple checklists.
  - log: line-oriented append-only log where each line is an entry (ndjson, run-history file, append-only audit). Items added on either side should be unioned by line membership.
  - tracker-table: markdown pipe-table with a header row + separator + body rows. Rows added on either side (with matching header) should be unioned.
  - free-prose: free-form prose where merge requires understanding of meaning and reordering of paragraphs (most code, READMEs, design docs, plan-docs).
  - unknown: cannot determine structure (binary-ish, malformed, mixed).

## Canonical (release) content (truncated):
```
{canonical_view}
```

## Workspace (operator-edited) content (truncated):
```
{workspace_view}
```

Return MergeClassification JSON: ``{{"merge_class": "...", "confidence": 0.0-1.0, "reasoning": "..."}}``. Keep ``reasoning`` brief (one sentence). Output ≤200 tokens total.
"""


def classify_file(
    *,
    llm_client: LLMClient,
    path: str,
    canonical_text: str,
    workspace_text: str,
) -> tuple[MergeClassification, int]:
    """Run the classify-call and return (classification, token_cost).

    Per D-2 LOCKED, the inputs are truncated to first-50 + last-10
    lines per side (full file when ≤60 lines).
    """
    canonical_view = _truncate(canonical_text, 50, 10)
    workspace_view = _truncate(workspace_text, 50, 10)
    prompt = _CLASSIFY_PROMPT.format(
        path=path,
        canonical_view=canonical_view,
        workspace_view=workspace_view,
    )
    result, tokens = llm_client.invoke(prompt, MergeClassification)
    if not isinstance(result, MergeClassification):
        raise ResolverFailure(
            "classify_file: LLM returned non-MergeClassification: "
            f"{type(result).__name__}"
        )
    return result, int(tokens)


# ----------------------------------------------------------------------
# Verify-call (D-build.7 / Hard Constraint #8)
# ----------------------------------------------------------------------


_VERIFY_PROMPT = """\
You are verifying a deterministic merge candidate against both sides of a workspace-vs-canonical conflict. Return a JSON MergeVerification object.

File path: {path}

The classifier tagged this file as merge_class=``{merge_class}``. The deterministic primitive ``{primitive_op}`` was applied. Verify the candidate.

## Canonical content:
```
{canonical_text}
```

## Workspace content:
```
{workspace_text}
```

## Candidate merged content:
```
{candidate_text}
```

Primitive trace: {primitive_trace}

Verify in THREE steps and report:

1. **Structural class check** (FIRST). Look at WORKSPACE and CANONICAL contents above. Are they actually structurally a ``{merge_class}``? If NO (e.g. you tagged it as append-only-list but the file is actually free-prose with bullet quotations), set ``class_mismatch=true`` and ``passed=false``. This is the rubber-stamp guard — be honest.

2. **Primitive correctness.** Did the ``{primitive_op}`` primitive preserve both sides' material content? List concerns concisely.

3. **Line-level information.** Did any line-level information from canonical or workspace go missing in the candidate? List the omissions.

Return MergeVerification JSON: ``{{"passed": bool, "class_mismatch": bool, "concerns": "..." or null, "confidence": 0.0-1.0}}``. Output ≤500 tokens total.
"""


def verify_merge(
    *,
    llm_client: LLMClient,
    path: str,
    canonical_text: str,
    workspace_text: str,
    candidate_merged_text: str,
    classification: MergeClassification,
    primitive_trace: PrimitiveTrace,
) -> tuple[MergeVerification, int]:
    """Run the verify-call and return (verification, token_cost)."""
    prompt = _VERIFY_PROMPT.format(
        path=path,
        merge_class=classification.merge_class,
        primitive_op=primitive_trace.operation,
        canonical_text=canonical_text,
        workspace_text=workspace_text,
        candidate_text=candidate_merged_text,
        primitive_trace=primitive_trace.note,
    )
    result, tokens = llm_client.invoke(prompt, MergeVerification)
    if not isinstance(result, MergeVerification):
        raise ResolverFailure(
            "verify_merge: LLM returned non-MergeVerification: "
            f"{type(result).__name__}"
        )
    return result, int(tokens)
