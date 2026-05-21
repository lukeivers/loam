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

"""Clause-(h) LLM-mediated merge resolver.

Per-conflict resolver that decides between accepting canonical
content, preserving workspace content, or producing a synthesised
three-way merge. The verdict is structured (Pydantic-typed) and
carries a free-text rationale + a 0.0-1.0 confidence score that the
audit log surfaces low-confidence-first for human review.

A.2 (FUTURE_IDEAS_DRAFT Bundle A.2 — QQ-refined) rewrites the
``MergeResolver.resolve()`` body so the LLM is used as
**classifier + verifier**, not as **generator**, on the common
mergeable case:

  1. **Classify** (~50-token output) — is this conflict
     structurally-mergeable by a deterministic primitive?
  2. **Deterministic merge** — if yes, run the appropriate
     primitive (text-3way / yaml-key-merge / append-only). Free.
  3. **Verify** (~200-token output) — did the deterministic
     merge lose meaning relative to the source content?
  4. **Decide** — verifier-pass → return a `MergeVerdict`
     pointing at the deterministic merge output; classifier-no
     or verifier-fail → fall back to the preserved
     LLM-as-generator path.

External callers see no API change: `.resolve()` still returns a
`MergeVerdict` with the same fields. AC.LMV.1-.5 cover the new
flow; the existing `test_merge_resolver.py` contracts still hold.

Budgeting (BB D-1 locks):
  - per_conflict_token_budget: 5_000  (workspace-tunable via
    ~/.loam/upgrade-config.yaml)
  - cumulative_token_budget:  100_000  (workspace-tunable)

Failure modes:
  - ``BudgetExhausted`` - cumulative ceiling hit; halt-and-resume.
  - ``ResolverFailure`` - LLM call failed (network, schema-reject,
    timeout). Fail-closed; clause-(h) returns failed → rollback.

The resolver is duck-typed against any object exposing
``invoke(prompt: str, response_model: type[BaseModel]) -> tuple[BaseModel, int]``
where the int is the token cost of the call. A ``StubLLMClient`` for
tests appears in ``self-upgrade/tests/conftest.py``. The production
adapter wraps ``ClaudePrintLLMClient`` (memory-system) — wired in
``cli.py`` at ``cmd_upgrade`` time.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ----- existing public types (unchanged surface) -------------------


class MergeVerdict(BaseModel):
    """Structured response from the LLM merge resolver."""

    model_config = ConfigDict(extra="forbid")

    resolution: Literal[
        "inferred-accept-canonical",
        "inferred-accept-workspace",
        "inferred-merged",
    ]
    merged_content: str | None = None
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _merged_requires_content(self) -> "MergeVerdict":
        if self.resolution == "inferred-merged":
            if self.merged_content is None or self.merged_content == "":
                raise ValueError(
                    "resolution=inferred-merged requires non-empty "
                    "merged_content"
                )
        if self.rationale.strip() == "":
            raise ValueError("rationale must be non-empty")
        return self


class ResolverBudget(BaseModel):
    """Per-conflict and cumulative token budgets (BB D-1 defaults)."""

    model_config = ConfigDict(extra="forbid")

    per_conflict_token_budget: int = Field(default=5_000, gt=0)
    cumulative_token_budget: int = Field(default=100_000, gt=0)


class BudgetExhausted(Exception):
    """Raised when a resolver call would exceed the cumulative ceiling."""

    def __init__(self, message: str, *, used: int, ceiling: int) -> None:
        super().__init__(message)
        self.used = used
        self.ceiling = ceiling


class ResolverFailure(Exception):
    """Raised on LLM call failure (network, schema-reject, timeout).

    Fail-closed: clause-(h) treats this as a verifier failure and
    triggers the existing rollback path. The framework MUST NOT
    silently treat a resolver failure as accept-canonical or
    accept-workspace.
    """


class LLMClient(Protocol):
    """Duck-typed surface the resolver expects.

    ``invoke(prompt, response_model)`` runs the LLM call and parses the
    result against ``response_model`` (Pydantic). Returns a tuple of the
    parsed model + the token cost of the call. Implementations raise
    ``ResolverFailure`` for any failure mode that should fail-close
    clause-(h).
    """

    def invoke(
        self,
        prompt: str,
        response_model: type[BaseModel],
    ) -> tuple[BaseModel, int]:
        ...


# ----- A.2: classifier + verifier types ----------------------------


Strategy = Literal[
    "text-3way",
    "yaml-key-merge",
    "append-only",
    "none",
]


class ClassifierVerdict(BaseModel):
    """AC.LMV.1 — classifier output.

    The classifier decides whether the conflict is structurally
    mergeable by a deterministic primitive and which primitive to
    use. ``strategy="none"`` means fall through to the LLM-as-
    generator path.
    """

    model_config = ConfigDict(extra="forbid")

    mergeable: bool
    strategy: Strategy
    reason: str

    @model_validator(mode="after")
    def _strategy_consistent(self) -> "ClassifierVerdict":
        if self.mergeable and self.strategy == "none":
            raise ValueError(
                "ClassifierVerdict: mergeable=True requires "
                "strategy != 'none'"
            )
        if not self.mergeable and self.strategy != "none":
            raise ValueError(
                "ClassifierVerdict: mergeable=False requires "
                "strategy == 'none'"
            )
        if self.reason.strip() == "":
            raise ValueError("ClassifierVerdict: reason must be non-empty")
        return self


class VerifierVerdict(BaseModel):
    """AC.LMV.3 — verifier output.

    The verifier inspects a deterministic merge output and reports
    whether it lost meaning relative to the source content. A
    ``verified=False`` result triggers fallback to the LLM-as-
    generator path.
    """

    model_config = ConfigDict(extra="forbid")

    verified: bool
    concerns: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _concerns_when_unverified(self) -> "VerifierVerdict":
        if not self.verified and not self.concerns:
            raise ValueError(
                "VerifierVerdict: verified=False requires "
                "at least one concern"
            )
        return self


# ----- A.2: deterministic merge primitives -------------------------


def deterministic_text_3way(
    canonical_text: str,
    workspace_text: str,
    prior_text: str | None,
) -> tuple[str, bool]:
    """AC.LMV.2 — three-way text merge via ``git merge-file``.

    Returns ``(merged, ok)``. ``ok=False`` means the primitive
    bailed (unresolvable conflict markers, missing prior, git
    error). When ``prior_text`` is None, falls back to an empty
    common ancestor — which makes any overlapping change a
    conflict; that is the conservative behaviour.
    """
    if prior_text is None:
        prior_text = ""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            base_p = os.path.join(tmp, "base")
            ours_p = os.path.join(tmp, "ours")
            theirs_p = os.path.join(tmp, "theirs")
            # ours = workspace; theirs = canonical. This labels
            # workspace as "current" and canonical as "incoming".
            with open(base_p, "w", encoding="utf-8") as f:
                f.write(prior_text)
            with open(ours_p, "w", encoding="utf-8") as f:
                f.write(workspace_text)
            with open(theirs_p, "w", encoding="utf-8") as f:
                f.write(canonical_text)
            # ``git merge-file -p`` writes merged output to stdout
            # instead of modifying ours_p. Returncode = number of
            # conflicts (0 = clean merge). Any positive value
            # means unresolved hunks; we bail.
            completed = subprocess.run(  # noqa: S603,S607
                [
                    "git",
                    "merge-file",
                    "-p",
                    "-q",
                    ours_p,
                    base_p,
                    theirs_p,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode != 0:
                # Any non-zero return = conflicts present OR git
                # error. Either way, bail to the LLM fallback.
                return ("", False)
            merged = completed.stdout.decode("utf-8", errors="replace")
            return (merged, True)
    except (OSError, subprocess.SubprocessError):
        return ("", False)


def deterministic_yaml_key_merge(
    canonical_text: str,
    workspace_text: str,
    prior_text: str | None,
) -> tuple[str, bool]:
    """AC.LMV.2 — three-way key-merge on top-level YAML mappings.

    Strategy: parse all three sides as YAML; if any side fails to
    parse OR is not a mapping at the top level, bail. Otherwise
    compute:

      - keys added by canonical (not in prior) → take canonical's value.
      - keys added by workspace (not in prior) → take workspace's value.
      - keys modified by canonical only → canonical's value.
      - keys modified by workspace only → workspace's value.
      - keys modified by both → bail (true conflict; defer to LLM).
      - keys deleted by canonical only → drop.
      - keys deleted by workspace only → drop.

    Returns ``(merged_yaml_text, ok)``. ``ok=False`` means a parse
    failure, non-mapping top level, or unresolvable double-modify.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return ("", False)

    try:
        canonical = yaml.safe_load(canonical_text)
        workspace = yaml.safe_load(workspace_text)
        prior = yaml.safe_load(prior_text) if prior_text is not None else {}
    except yaml.YAMLError:
        return ("", False)

    if not isinstance(canonical, dict) or not isinstance(workspace, dict):
        return ("", False)
    if prior is None:
        prior = {}
    if not isinstance(prior, dict):
        return ("", False)

    merged: dict[str, object] = {}
    all_keys = set(canonical) | set(workspace) | set(prior)
    for key in all_keys:
        in_can = key in canonical
        in_ws = key in workspace
        in_prior = key in prior

        can_val = canonical.get(key)
        ws_val = workspace.get(key)
        prior_val = prior.get(key)

        if in_can and in_ws:
            if can_val == ws_val:
                merged[key] = can_val
            elif in_prior and can_val == prior_val:
                # canonical unchanged, workspace modified -> workspace
                merged[key] = ws_val
            elif in_prior and ws_val == prior_val:
                # workspace unchanged, canonical modified -> canonical
                merged[key] = can_val
            else:
                # Both modified (or both added, differently). True
                # conflict; defer to LLM-as-generator.
                return ("", False)
        elif in_can and not in_ws:
            if in_prior and prior_val == can_val:
                # workspace deleted, canonical unchanged -> drop.
                continue
            # workspace deleted, canonical modified, OR added by
            # canonical only -> take canonical.
            merged[key] = can_val
        elif in_ws and not in_can:
            if in_prior and prior_val == ws_val:
                # canonical deleted, workspace unchanged -> drop.
                continue
            # canonical deleted, workspace modified, OR added by
            # workspace only -> take workspace.
            merged[key] = ws_val
        # else: in_prior only -> both deleted -> drop.

    try:
        text = yaml.safe_dump(
            merged, sort_keys=True, default_flow_style=False
        )
    except yaml.YAMLError:
        return ("", False)
    return (text, True)


def deterministic_append_only(
    canonical_text: str,
    workspace_text: str,
    prior_text: str | None,
) -> tuple[str, bool]:
    """AC.LMV.2 — append-only merge for changelog-shaped files.

    Both sides MUST share an unbroken common prefix (the
    historical entries). Each side's unique tail (entries added
    since the common prefix) is concatenated: canonical first,
    then workspace's unique-suffix entries. Returns
    ``(merged_text, ok)`` where ``ok=False`` means the prefix
    discipline failed (one side rewrote history) or one side is
    empty.
    """
    can_lines = canonical_text.splitlines(keepends=True)
    ws_lines = workspace_text.splitlines(keepends=True)
    if not can_lines or not ws_lines:
        return ("", False)

    # Find longest common prefix.
    prefix_len = 0
    for c_line, w_line in zip(can_lines, ws_lines, strict=False):
        if c_line == w_line:
            prefix_len += 1
        else:
            break

    # If no common prefix, this isn't an append-only relationship.
    if prefix_len == 0:
        return ("", False)

    # If prior_text was provided, the common prefix should at
    # least reach the prior length; otherwise one side rewrote
    # history.
    if prior_text is not None:
        prior_lines = prior_text.splitlines(keepends=True)
        if prefix_len < len(prior_lines):
            return ("", False)

    can_tail = can_lines[prefix_len:]
    ws_tail = ws_lines[prefix_len:]
    # Lines present in canonical's tail are kept first (preserves
    # canonical-history); then workspace-tail lines not already in
    # canonical's tail are appended.
    can_tail_set = set(can_tail)
    ws_unique_tail = [ln for ln in ws_tail if ln not in can_tail_set]

    merged_lines = can_lines[:prefix_len] + can_tail + ws_unique_tail
    return ("".join(merged_lines), True)


_STRATEGY_DISPATCH = {
    "text-3way": deterministic_text_3way,
    "yaml-key-merge": deterministic_yaml_key_merge,
    "append-only": deterministic_append_only,
}


# ----- A.2: classifier + verifier prompt builders ------------------


_PREVIEW_CHARS = 500


def build_classifier_prompt(
    *,
    path: str,
    canonical_text: str,
    workspace_text: str,
) -> str:
    """AC.LMV.1 — short prompt asking for a ClassifierVerdict.

    Sends only the path + a ~500-char preview of each side; the
    classifier doesn't need the full body to decide structural
    mergeability.
    """
    can_preview = canonical_text[:_PREVIEW_CHARS]
    ws_preview = workspace_text[:_PREVIEW_CHARS]
    return "\n".join(
        [
            "Classify whether this merge conflict is structurally-",
            "mergeable by a deterministic primitive.",
            "",
            f"File path: {path}",
            "",
            "Strategies (pick at most one):",
            "  - text-3way: ordered text file (source code, prose) where",
            "    git's three-way line merge would resolve cleanly.",
            "  - yaml-key-merge: YAML config (top-level mapping) where",
            "    keys can be merged independently.",
            "  - append-only: changelog/log file where both sides only",
            "    APPEND new entries (no edits to existing entries).",
            "  - none: not structurally mergeable; defer to full",
            "    LLM-as-generator merge.",
            "",
            f"## Canonical preview (first {_PREVIEW_CHARS} chars):",
            "```",
            can_preview,
            "```",
            "",
            f"## Workspace preview (first {_PREVIEW_CHARS} chars):",
            "```",
            ws_preview,
            "```",
            "",
            "Return a ClassifierVerdict JSON with: mergeable (bool),",
            "strategy (one of the four labels), reason (one-sentence).",
        ]
    )


def build_verifier_prompt(
    *,
    path: str,
    strategy: str,
    canonical_text: str,
    workspace_text: str,
    merged_text: str,
) -> str:
    """AC.LMV.3 — prompt asking whether merged_text preserves meaning.

    The verifier sees the merged output plus both source sides.
    Returns a structured ``VerifierVerdict``. ``verified=False``
    must list at least one concern.
    """
    return "\n".join(
        [
            "You are verifying a deterministic three-way merge.",
            "",
            f"File path: {path}",
            f"Strategy used: {strategy}",
            "",
            "## Canonical source:",
            "```",
            canonical_text,
            "```",
            "",
            "## Workspace source:",
            "```",
            workspace_text,
            "```",
            "",
            "## Merged output:",
            "```",
            merged_text,
            "```",
            "",
            "Question: does the merged output preserve the meaning",
            "of BOTH sides? Specifically, check that no section,",
            "key, or semantic intent was dropped.",
            "",
            "Return a VerifierVerdict JSON with: verified (bool),",
            "concerns (list of strings; non-empty when verified=false).",
        ]
    )


def build_prompt(
    *,
    path: str,
    canonical_text: str,
    workspace_text: str,
    prior_text: str | None,
) -> str:
    """Build the LLM-as-generator fallback prompt for a single conflict.

    Preserved from pre-A.2 verbatim — the fallback path uses this
    when the classifier says no OR the verifier rejects the
    deterministic merge.
    """
    parts = [
        "You are resolving a three-way merge conflict in a loam workspace.",
        "",
        f"File path: {path}",
        "",
        "## Canonical (release) content:",
        "```",
        canonical_text,
        "```",
        "",
        "## Workspace (operator-edited) content:",
        "```",
        workspace_text,
        "```",
    ]
    if prior_text is not None:
        parts.extend([
            "",
            "## Prior-release content (the common ancestor):",
            "```",
            prior_text,
            "```",
        ])
    parts.extend([
        "",
        "Choose ONE of three resolutions:",
        "  - inferred-accept-canonical: take canonical; workspace edit was redundant or superseded.",
        "  - inferred-accept-workspace: keep workspace; canonical's change does not apply here.",
        "  - inferred-merged: synthesise a merge that preserves both intents (provide merged_content).",
        "",
        "Return a MergeVerdict JSON with: resolution, merged_content (string or null), rationale, confidence (0.0-1.0).",
        "Confidence reflects how certain you are the resolution preserves both sides' intent.",
    ])
    return "\n".join(parts)


# ----- MergeResolver: A.2 four-stage orchestration -----------------


class MergeResolver:
    """Per-conflict resolver with cumulative budget tracking.

    A.2 (this version) wires a four-stage flow inside ``.resolve()``:
    classify → deterministic-merge → verify → accept-or-fallback.
    The external API is unchanged: ``.resolve()`` returns a
    ``MergeVerdict`` and raises ``BudgetExhausted`` / ``ResolverFailure``
    on the same boundaries it did pre-A.2.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        budget: ResolverBudget | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.budget = budget or ResolverBudget()
        self._cumulative_used: int = 0
        self._call_count: int = 0

    @property
    def cumulative_used(self) -> int:
        return self._cumulative_used

    @property
    def call_count(self) -> int:
        return self._call_count

    def resolve(
        self,
        *,
        path: str,
        canonical_text: str,
        workspace_text: str,
        prior_text: str | None = None,
    ) -> MergeVerdict:
        """A.2 — four-stage classify → det-merge → verify → fallback.

        Raises:
            BudgetExhausted: cumulative ceiling already met or would be
                exceeded by this call's per-conflict budget.
            ResolverFailure: LLM call failed (network, schema-reject,
                timeout).
        """
        # AC.LMV.4 / pre-flight: cumulative budget gate. We charge
        # the per-conflict budget against the ceiling before any
        # LLM call so an exhausted budget never silently spends.
        self._check_budget_gate()

        # AC.LMV.1: classifier call.
        try:
            classifier = self._classify(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
            )
        except ResolverFailure:
            # Classifier failed at the LLM boundary — fall back to
            # the generator path. This keeps A.2 strictly safer
            # than pre-A.2: a classifier failure does not poison
            # the resolve, it just bypasses the optimization.
            return self._resolve_with_generator(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                prior_text=prior_text,
            )

        # AC.LMV.4: classifier-says-no → straight to generator.
        if not classifier.mergeable or classifier.strategy == "none":
            return self._resolve_with_generator(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                prior_text=prior_text,
            )

        # AC.LMV.2: dispatch to deterministic primitive.
        primitive = _STRATEGY_DISPATCH.get(classifier.strategy)
        if primitive is None:
            return self._resolve_with_generator(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                prior_text=prior_text,
            )
        merged_text, ok = primitive(
            canonical_text, workspace_text, prior_text
        )
        if not ok:
            # Primitive bailed (parse-fail, conflict markers, etc.).
            return self._resolve_with_generator(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                prior_text=prior_text,
            )

        # AC.LMV.3: verifier call on the deterministic output.
        try:
            verifier = self._verify(
                path=path,
                strategy=classifier.strategy,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                merged_text=merged_text,
            )
        except ResolverFailure:
            # Verifier LLM failed — be conservative; fall back.
            return self._resolve_with_generator(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                prior_text=prior_text,
            )

        # AC.LMV.5: verifier-says-fail → fallback.
        if not verifier.verified:
            return self._resolve_with_generator(
                path=path,
                canonical_text=canonical_text,
                workspace_text=workspace_text,
                prior_text=prior_text,
            )

        # AC.LMV.4: verifier-pass → emit a MergeVerdict pointing at
        # the deterministic merge output. Confidence is set high
        # (0.95) because two LLM calls agreed on the structural
        # mergeability and the deterministic primitive ran clean;
        # the rationale records the path through the flow.
        rationale_parts = [
            f"A.2: classifier={classifier.strategy} "
            f"({classifier.reason});",
            "deterministic merge produced output; verifier confirmed",
            "meaning preserved.",
        ]
        if verifier.concerns:
            rationale_parts.append(
                "verifier-concerns(non-blocking): "
                + "; ".join(verifier.concerns)
            )
        self._call_count += 1
        return MergeVerdict(
            resolution="inferred-merged",
            merged_content=merged_text,
            rationale=" ".join(rationale_parts),
            confidence=0.95,
        )

    # ----- internal helpers --------------------------------------

    def _check_budget_gate(self) -> None:
        projected = (
            self._cumulative_used + self.budget.per_conflict_token_budget
        )
        if self._cumulative_used >= self.budget.cumulative_token_budget:
            raise BudgetExhausted(
                f"cumulative ceiling reached: {self._cumulative_used} >= "
                f"{self.budget.cumulative_token_budget}",
                used=self._cumulative_used,
                ceiling=self.budget.cumulative_token_budget,
            )
        if projected > self.budget.cumulative_token_budget:
            raise BudgetExhausted(
                f"cumulative ceiling would be exceeded: "
                f"{self._cumulative_used} + "
                f"{self.budget.per_conflict_token_budget} > "
                f"{self.budget.cumulative_token_budget}",
                used=self._cumulative_used,
                ceiling=self.budget.cumulative_token_budget,
            )

    def _classify(
        self,
        *,
        path: str,
        canonical_text: str,
        workspace_text: str,
    ) -> ClassifierVerdict:
        prompt = build_classifier_prompt(
            path=path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
        )
        try:
            verdict, tokens = self.llm_client.invoke(
                prompt, ClassifierVerdict
            )
        except ResolverFailure:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ResolverFailure(
                f"classifier call failed for {path}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        if not isinstance(verdict, ClassifierVerdict):
            raise ResolverFailure(
                f"classifier returned wrong type for {path}: "
                f"{type(verdict).__name__}"
            )
        self._cumulative_used += int(tokens)
        return verdict

    def _verify(
        self,
        *,
        path: str,
        strategy: str,
        canonical_text: str,
        workspace_text: str,
        merged_text: str,
    ) -> VerifierVerdict:
        prompt = build_verifier_prompt(
            path=path,
            strategy=strategy,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
            merged_text=merged_text,
        )
        try:
            verdict, tokens = self.llm_client.invoke(
                prompt, VerifierVerdict
            )
        except ResolverFailure:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ResolverFailure(
                f"verifier call failed for {path}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        if not isinstance(verdict, VerifierVerdict):
            raise ResolverFailure(
                f"verifier returned wrong type for {path}: "
                f"{type(verdict).__name__}"
            )
        self._cumulative_used += int(tokens)
        return verdict

    def _resolve_with_generator(
        self,
        *,
        path: str,
        canonical_text: str,
        workspace_text: str,
        prior_text: str | None,
    ) -> MergeVerdict:
        """AC.LMV.5 — preserved pre-A.2 LLM-as-generator path.

        Used when (a) classifier says non-mergeable, (b) the
        deterministic primitive bails, (c) the verifier rejects
        the deterministic output, or (d) any LLM call in the A.2
        flow fails outright.
        """
        prompt = build_prompt(
            path=path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
            prior_text=prior_text,
        )
        try:
            verdict, tokens = self.llm_client.invoke(prompt, MergeVerdict)
        except ResolverFailure:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ResolverFailure(
                f"resolver call failed for {path}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(verdict, MergeVerdict):
            raise ResolverFailure(
                f"resolver returned wrong type for {path}: "
                f"{type(verdict).__name__}"
            )

        self._cumulative_used += int(tokens)
        self._call_count += 1
        return verdict
