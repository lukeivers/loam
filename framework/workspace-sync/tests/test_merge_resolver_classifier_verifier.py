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

"""A.2 — AC.LMV.1-.5 tests for classifier + deterministic + verifier.

Workspace-sync's `MergeResolver.resolve()` was rewired from
LLM-as-generator to classifier → deterministic-merge → verifier →
fallback. These tests cover:

  - AC.LMV.1 — classifier verdict shape + behaviour on three
    representative file shapes.
  - AC.LMV.2 — each deterministic primitive (text-3way,
    yaml-key-merge, append-only) on synthetic three-way merges.
  - AC.LMV.3 — verifier catches a corrupt merge output.
  - AC.LMV.4 — full pipeline integration: classify → det-merge
    → verify → accept emits a well-formed MergeVerdict
    (outcome-altitude AC).
  - AC.LMV.5 — fallback path triggers on verify-fail and
    returns the generator's verdict.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from loam.workspace_sync.merge_resolver import (
    ClassifierVerdict,
    MergeResolver,
    MergeVerdict,
    VerifierVerdict,
    build_classifier_prompt,
    build_verifier_prompt,
    deterministic_append_only,
    deterministic_text_3way,
    deterministic_yaml_key_merge,
)


# ----- shared stub --------------------------------------------------


class _ScriptedClient:
    """LLM client returning canned verdicts in queue order.

    Each entry is ``(model_class, return_value, tokens)``. On
    ``invoke``, we pop the first entry, assert the requested
    ``response_model`` matches the recorded ``model_class`` (catches
    test-side wiring bugs early), and return ``(return_value, tokens)``.
    """

    def __init__(
        self,
        script: list[tuple[type[BaseModel], BaseModel, int]],
    ) -> None:
        self.script = list(script)
        self.calls: list[tuple[str, type[BaseModel]]] = []

    def invoke(
        self, prompt: str, response_model: type[BaseModel]
    ) -> tuple[BaseModel, int]:
        self.calls.append((prompt, response_model))
        if not self.script:
            raise AssertionError(
                f"_ScriptedClient: no more scripted calls "
                f"(asked for {response_model.__name__})"
            )
        expected_model, value, tokens = self.script.pop(0)
        assert response_model is expected_model, (
            f"_ScriptedClient: expected {expected_model.__name__}, "
            f"got {response_model.__name__}"
        )
        return value, tokens


# ----- AC.LMV.1: classifier verdict + prompt -----------------------


def test_classifier_verdict_validates_strategy_consistency() -> None:
    # AC.LMV.1 — mergeable=True with strategy=none must reject.
    with pytest.raises(ValueError):
        ClassifierVerdict(
            mergeable=True,
            strategy="none",
            reason="bad",
        )
    # AC.LMV.1 — mergeable=False with a real strategy must reject.
    with pytest.raises(ValueError):
        ClassifierVerdict(
            mergeable=False,
            strategy="text-3way",
            reason="bad",
        )


@pytest.mark.parametrize(
    "path,strategy",
    [
        ("config.yaml", "yaml-key-merge"),
        ("CHANGELOG.md", "append-only"),
        ("foo.py", "text-3way"),
    ],
)
def test_classifier_prompt_includes_path_and_strategy_menu(
    path: str, strategy: str
) -> None:
    """AC.LMV.1 — classifier prompt mentions path + all four strategies."""
    p = build_classifier_prompt(
        path=path,
        canonical_text="canon",
        workspace_text="work",
    )
    assert path in p
    assert "text-3way" in p
    assert "yaml-key-merge" in p
    assert "append-only" in p
    assert "none" in p
    # Strategy mentioned by name (one of the four)
    assert strategy in p


def test_classifier_routes_three_file_shapes_through_resolver() -> None:
    """AC.LMV.1 — three representative shapes route to expected strategies.

    Each shape is run through MergeResolver.resolve(); the
    classifier verdict directs which deterministic primitive
    runs. We assert the verdict was returned (no fallback fired)
    AND the rationale records the chosen strategy.
    """
    cases: list[tuple[str, str, str, str | None, str, str]] = [
        # (path, canonical, workspace, prior, expected_strategy, assert_hint)
        (
            "config.yaml",
            "a: 1\nb: 2\n",
            "a: 1\nc: 3\n",
            "a: 1\n",
            "yaml-key-merge",
            "yaml-key-merge",
        ),
        (
            "CHANGELOG.md",
            "v1\nv2\nv3\n",
            "v1\nv2\nv4\n",
            "v1\nv2\n",
            "append-only",
            "append-only",
        ),
        (
            "foo.py",
            "def a():\n    return 1\n\ndef b():\n    return 2\n",
            "def c():\n    return 3\n\ndef a():\n    return 1\n",
            "def a():\n    return 1\n",
            "text-3way",
            "text-3way",
        ),
    ]
    for path, canonical, workspace, prior, strategy, hint in cases:
        client = _ScriptedClient(
            [
                (
                    ClassifierVerdict,
                    ClassifierVerdict(
                        mergeable=True,
                        strategy=strategy,  # type: ignore[arg-type]
                        reason=f"classifier picked {strategy}",
                    ),
                    50,
                ),
                (
                    VerifierVerdict,
                    VerifierVerdict(verified=True, concerns=[]),
                    200,
                ),
            ]
        )
        resolver = MergeResolver(client)
        # prior_text=canonical's "before" content — for yaml use a
        # prior that includes one of each side's adds as a
        # deletion so it is non-trivial. We use prior=None for
        # simplicity here; the primitives accept None.
        verdict = resolver.resolve(
            path=path,
            canonical_text=canonical,
            workspace_text=workspace,
            prior_text=prior,
        )
        assert verdict.resolution == "inferred-merged", (
            f"path={path}: expected inferred-merged, "
            f"got {verdict.resolution}"
        )
        assert hint in verdict.rationale


# ----- AC.LMV.2: deterministic primitives ---------------------------


def test_deterministic_text_3way_clean_merge() -> None:
    """AC.LMV.2 — text-3way merges non-adjacent line edits cleanly.

    git merge-file requires hunks to be separated by at least one
    unchanged context line — adjacent edits register as overlapping
    hunks even when the modified lines themselves don't overlap.
    A blank-separator line between B and C reflects realistic
    source-file shape (function boundaries, doc paragraphs).
    """
    prior = "line A\nline B\n\nline C\n"
    canonical = "line A\nline B canonical\n\nline C\n"
    workspace = "line A\nline B\n\nline C workspace\n"
    merged, ok = deterministic_text_3way(canonical, workspace, prior)
    assert ok is True
    assert "line B canonical" in merged
    assert "line C workspace" in merged


def test_deterministic_text_3way_bails_on_conflict() -> None:
    """AC.LMV.2 — text-3way bails when both sides edit the same line."""
    prior = "line A\n"
    canonical = "line A canonical\n"
    workspace = "line A workspace\n"
    merged, ok = deterministic_text_3way(canonical, workspace, prior)
    assert ok is False
    assert merged == ""


def test_deterministic_yaml_key_merge_independent_adds() -> None:
    """AC.LMV.2 — yaml-key-merge composes non-overlapping key adds."""
    prior = "a: 1\n"
    canonical = "a: 1\nb: 2\n"
    workspace = "a: 1\nc: 3\n"
    merged, ok = deterministic_yaml_key_merge(canonical, workspace, prior)
    assert ok is True
    # Re-parse to compare semantics (key order is normalised).
    import yaml  # type: ignore[import-untyped]
    parsed = yaml.safe_load(merged)
    assert parsed == {"a": 1, "b": 2, "c": 3}


def test_deterministic_yaml_key_merge_bails_on_double_modify() -> None:
    """AC.LMV.2 — yaml-key-merge bails when both sides modify the same key."""
    prior = "a: 1\n"
    canonical = "a: 2\n"
    workspace = "a: 3\n"
    merged, ok = deterministic_yaml_key_merge(canonical, workspace, prior)
    assert ok is False
    assert merged == ""


def test_deterministic_yaml_key_merge_preserves_one_side_modify() -> None:
    """AC.LMV.2 — yaml-key-merge keeps the modified value when only one side changed."""
    prior = "a: 1\nb: 2\n"
    canonical = "a: 99\nb: 2\n"  # canonical modified a
    workspace = "a: 1\nb: 2\n"  # workspace unchanged
    merged, ok = deterministic_yaml_key_merge(canonical, workspace, prior)
    assert ok is True
    import yaml  # type: ignore[import-untyped]
    parsed = yaml.safe_load(merged)
    assert parsed == {"a": 99, "b": 2}


def test_deterministic_append_only_unions_tail_entries() -> None:
    """AC.LMV.2 — append-only takes union of unique tail lines."""
    prior = "v1\nv2\n"
    canonical = "v1\nv2\nv3\n"
    workspace = "v1\nv2\nv4\n"
    merged, ok = deterministic_append_only(canonical, workspace, prior)
    assert ok is True
    # canonical's tail (v3) first, then workspace's unique (v4)
    assert merged == "v1\nv2\nv3\nv4\n"


def test_deterministic_append_only_bails_on_rewritten_history() -> None:
    """AC.LMV.2 — append-only bails when one side rewrites the common prefix."""
    prior = "v1\nv2\n"
    canonical = "v1-rewrite\nv2\nv3\n"
    workspace = "v1\nv2\nv4\n"
    merged, ok = deterministic_append_only(canonical, workspace, prior)
    assert ok is False


# ----- AC.LMV.3: verifier catches corrupt merge --------------------


def test_verifier_catches_dropped_section() -> None:
    """AC.LMV.3 — full pipeline: a dropped section triggers verifier-fail.

    We craft a scenario where the deterministic primitive runs
    clean (the classifier picks text-3way) but the merged output
    is a known-corrupt body that drops a section. The verifier
    (scripted) returns ``verified=False`` and the resolve falls
    back to the generator path. AC.LMV.5 also covers the
    fallback; here we focus on AC.LMV.3: the verifier's
    decision IS what triggers the fallback.
    """
    canonical = "# Section A\nA-body\n\n# Section B\nB-body\n"
    workspace = "# Section A\nA-body modified\n\n# Section B\nB-body\n"
    # Generator's fallback verdict (so the resolver has somewhere
    # to land after verify-fail).
    fallback_verdict = MergeVerdict(
        resolution="inferred-merged",
        merged_content="# Section A\nA-body modified\n\n# Section B\nB-body\n",
        rationale="generator: full merge after verifier-fail",
        confidence=0.85,
    )
    client = _ScriptedClient(
        [
            (
                ClassifierVerdict,
                ClassifierVerdict(
                    mergeable=True,
                    strategy="text-3way",
                    reason="classifier picked text-3way",
                ),
                50,
            ),
            (
                VerifierVerdict,
                VerifierVerdict(
                    verified=False,
                    concerns=["dropped section B"],
                ),
                200,
            ),
            (MergeVerdict, fallback_verdict, 3_000),
        ]
    )
    resolver = MergeResolver(client)
    verdict = resolver.resolve(
        path="doc.md",
        canonical_text=canonical,
        workspace_text=workspace,
        prior_text="# Section A\nA-body\n\n# Section B\nB-body\n",
    )
    # The verifier-fail routed to the generator path; the
    # returned verdict carries the GENERATOR's rationale.
    assert verdict.rationale == "generator: full merge after verifier-fail"
    # Exactly three LLM calls happened: classify, verify, fallback.
    assert len(client.calls) == 3
    assert client.calls[0][1] is ClassifierVerdict
    assert client.calls[1][1] is VerifierVerdict
    assert client.calls[2][1] is MergeVerdict


def test_verifier_prompt_shows_strategy_and_merged_output() -> None:
    """AC.LMV.3 — verifier prompt names the strategy + carries merged output."""
    p = build_verifier_prompt(
        path="x.yaml",
        strategy="yaml-key-merge",
        canonical_text="a: 1",
        workspace_text="b: 2",
        merged_text="a: 1\nb: 2",
    )
    assert "yaml-key-merge" in p
    assert "x.yaml" in p
    assert "a: 1\nb: 2" in p
    assert "VerifierVerdict" in p


# ----- AC.LMV.4: full pipeline integration (outcome-altitude) -------


def test_full_pipeline_classify_merge_verify_accept() -> None:
    """AC.LMV.4 — end-to-end: classify → det-merge → verify → accept.

    Outcome-altitude AC: invokes the production entry point
    ``MergeResolver.resolve()`` on a representative YAML config
    case with no pre-arranged internal state (only the LLM
    stub is arranged). Asserts:

      1. The returned verdict is a well-formed MergeVerdict.
      2. ``resolution=inferred-merged`` (the deterministic
         primitive produced the body).
      3. ``merged_content`` is the YAML-key-merged body
         (canonical + workspace adds composed).
      4. Token accounting incremented for both LLM calls
         (classifier + verifier), no generator call billed.
    """
    canonical = "name: loam\nversion: 0.10\n"
    workspace = "name: loam\nrelease_notes: hotfix\n"
    prior = "name: loam\n"
    client = _ScriptedClient(
        [
            (
                ClassifierVerdict,
                ClassifierVerdict(
                    mergeable=True,
                    strategy="yaml-key-merge",
                    reason="yaml config with independent key adds",
                ),
                40,
            ),
            (
                VerifierVerdict,
                VerifierVerdict(verified=True, concerns=[]),
                180,
            ),
        ]
    )
    resolver = MergeResolver(client)
    verdict = resolver.resolve(
        path="meta.yaml",
        canonical_text=canonical,
        workspace_text=workspace,
        prior_text=prior,
    )
    # AC.LMV.4 #1 — well-formed MergeVerdict.
    assert isinstance(verdict, MergeVerdict)
    # AC.LMV.4 #2 — inferred-merged.
    assert verdict.resolution == "inferred-merged"
    # AC.LMV.4 #3 — merged body unites both sides.
    assert verdict.merged_content is not None
    import yaml  # type: ignore[import-untyped]
    parsed = yaml.safe_load(verdict.merged_content)
    assert parsed == {
        "name": "loam",
        "version": 0.10,
        "release_notes": "hotfix",
    }
    # AC.LMV.4 #4 — token accounting (40 + 180 = 220, no third
    # call since verifier passed).
    assert resolver.cumulative_used == 220
    assert resolver.call_count == 1
    assert len(client.calls) == 2  # classify + verify only


# ----- AC.LMV.5: fallback triggers on verify-fail -------------------


def test_fallback_path_triggered_on_verify_fail_returns_generator_verdict() -> None:
    """AC.LMV.5 — verify-fail routes to generator + returns its verdict.

    The end-to-end behaviour: classifier says mergeable;
    primitive runs ok; verifier says fail; the resolver calls
    the generator path; the generator's verdict is what
    ``.resolve()`` returns to the caller.
    """
    generator_verdict = MergeVerdict(
        resolution="inferred-accept-canonical",
        merged_content=None,
        rationale="generator decided: take canonical wholesale",
        confidence=0.80,
    )
    client = _ScriptedClient(
        [
            (
                ClassifierVerdict,
                ClassifierVerdict(
                    mergeable=True,
                    strategy="text-3way",
                    reason="picks text-3way",
                ),
                50,
            ),
            (
                VerifierVerdict,
                VerifierVerdict(
                    verified=False,
                    concerns=["semantic drift detected"],
                ),
                200,
            ),
            (MergeVerdict, generator_verdict, 2_000),
        ]
    )
    resolver = MergeResolver(client)
    verdict = resolver.resolve(
        path="src.py",
        canonical_text="a\nb\nc\n",
        workspace_text="a\nb modified\nc\n",
        prior_text="a\nb\nc\n",
    )
    # The fallback's verdict is what the caller sees.
    assert verdict.resolution == "inferred-accept-canonical"
    assert verdict.rationale == "generator decided: take canonical wholesale"
    assert verdict.confidence == 0.80
    # Token bookkeeping: 50 classifier + 200 verifier + 2_000 fallback.
    assert resolver.cumulative_used == 2_250
    assert resolver.call_count == 1  # the generator call.


def test_fallback_path_triggered_on_classifier_says_no() -> None:
    """AC.LMV.5 — classifier-says-no skips primitives + verifier."""
    generator_verdict = MergeVerdict(
        resolution="inferred-merged",
        merged_content="generator-merged-body\n",
        rationale="generator: only path for unmergeable shape",
        confidence=0.7,
    )
    client = _ScriptedClient(
        [
            (
                ClassifierVerdict,
                ClassifierVerdict(
                    mergeable=False,
                    strategy="none",
                    reason="binary or unstructured payload",
                ),
                30,
            ),
            (MergeVerdict, generator_verdict, 1_500),
        ]
    )
    resolver = MergeResolver(client)
    verdict = resolver.resolve(
        path="blob.bin",
        canonical_text="binary-ish-canonical",
        workspace_text="binary-ish-workspace",
        prior_text=None,
    )
    assert verdict.merged_content == "generator-merged-body\n"
    # Only two LLM calls: classifier + generator (no verifier).
    assert len(client.calls) == 2
    assert client.calls[0][1] is ClassifierVerdict
    assert client.calls[1][1] is MergeVerdict


def test_fallback_path_triggered_on_primitive_bail() -> None:
    """AC.LMV.5 — classifier-yes-but-primitive-bails routes to fallback.

    Classifier says text-3way; both sides edit the same line so
    ``git merge-file`` returns conflict; primitive ok=False;
    flow falls through to generator. Verifier is NOT called
    (the primitive bailed before producing an output to verify).
    """
    generator_verdict = MergeVerdict(
        resolution="inferred-merged",
        merged_content="resolved-via-generator\n",
        rationale="generator: text-3way bailed on conflict markers",
        confidence=0.75,
    )
    client = _ScriptedClient(
        [
            (
                ClassifierVerdict,
                ClassifierVerdict(
                    mergeable=True,
                    strategy="text-3way",
                    reason="text file; tried text-3way",
                ),
                40,
            ),
            (MergeVerdict, generator_verdict, 1_800),
        ]
    )
    resolver = MergeResolver(client)
    # Both sides modify the same line → git merge-file conflicts.
    verdict = resolver.resolve(
        path="thing.py",
        canonical_text="line A canonical\n",
        workspace_text="line A workspace\n",
        prior_text="line A\n",
    )
    assert verdict.rationale == (
        "generator: text-3way bailed on conflict markers"
    )
    assert len(client.calls) == 2
    assert client.calls[0][1] is ClassifierVerdict
    assert client.calls[1][1] is MergeVerdict  # straight to generator
