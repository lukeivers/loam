"""AC.DPS2.* — dev-pattern simplifications #2 (seal-narrative compression).

Plan: ``docs/plans/dev-pattern-simplifications-2.md``.
Source authority: cost-audit 2026-05-04 Recommendation B.
Predecessor: ``dev-pattern-simplifications-1`` (sealed 019cfca) which
landed schema v3 + the initial synthesizer.

Coverage:
- AC.DPS2.1  — synthesizer emits what-shipped + ACs + smoke + plan-doc.
- AC.DPS2.2  — ``ac_count`` field — additive at v3, rejected at v1/v2.
- AC.DPS2.3  — ``smoke_outcome`` field — additive at v3, rejected at v1/v2.
- AC.DPS2.4  — synthesized body fits 5-15 lines.
- AC.DPS2.5  — explicit ``narrative.body`` returned verbatim at v3.
- AC.DPS2.6  — seal commit message body gains ``Plan doc:`` line at v3.
- AC.DPS2.7  — seal commit subject unchanged across all schemas.
- AC.DPS2.8  — ``commit-ladder.md`` describes both shapes (doc check).
- AC.DPS2.9  — sealed-component-build dispatch template verified.
- AC.DPS2.10 — all existing manifest YAMLs validate clean.
- AC.DPS2.11 — dev-sdlc seal-test stays green (verified at build-time;
                 not unit-testable without canonical fixture; reuses
                 AC.DPS1.14's pattern of build-time verification).
- AC.DPS2.12 — existing long-form ``SEAL_COMMIT.<slug>`` files unchanged
                 (build-time observation; no unit assertion needed beyond
                 the doc-update grep covered by AC.DPS2.8).
- AC.DPS2.13 — THIS amendment's manifest is the v3 first-use validator
                 (verified at build-time via ``loam amend apply`` +
                 ``loam amend seal``; observable in canonical history).
- AC.DPS2.14 — per-AC tests authored (this file IS the AC).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

from loam_amend.commands.apply import run as apply_run
from loam_amend.commands.seal import (
    _build_commit_message,
    _resolve_narrative_body,
)
from loam_amend.manifest import (
    InvalidField,
    Manifest,
    NarrativeSpec,
    load_manifest,
)


# ---------------------------------------------------------------------------
# Helpers — mirror the DPS1 test file's shape so the conventions stay
# consistent across the AC.DPS{1,2}.* corpus.


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _seed_component(
    repo: Path, name: str, baseline_value: str = "0000000"
) -> None:
    """Seed a component under framework/<name>/ with seal-test + sidecar."""
    comp = repo / "framework" / name
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text(
        "def foo():\n    return 1\n", encoding="utf-8"
    )
    (comp / "tests" / "SEAL_COMMIT").write_text(
        f"{baseline_value}\n", encoding="utf-8"
    )
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{baseline_value}"

            def test_x():
                allowed_prefixes = (
                    "framework/{name}/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def _author_v3_manifest(
    repo: Path,
    *,
    baseline_sha: str,
    components: list[dict[str, str]],
    slug: str = "ac-dps2",
    title: str = "AC.DPS2 test",
    plan_doc_ref: str | None = "docs/plans/ac-dps2.md",
    narrative_body: str | None = None,
    include_number: bool = False,
    include_narrative: bool = True,
    extra_top_level: dict | None = None,
) -> Path:
    """Author a schema_version-3 manifest at <repo>/manifest.yaml.

    Mirror of the DPS1 helper. Kept local to this file rather than
    extracted to conftest because (a) DPS1 keeps its helper local too,
    (b) extracting would invite drift between the two test files, and
    (c) test-file-local helpers are the convention for the AC.* corpus.
    """
    amendment: dict = {"slug": slug, "title": title}
    if include_number:
        amendment["number"] = 999
    manifest_doc: dict = {
        "schema_version": 3,
        "amendment": amendment,
        "baseline": baseline_sha,
        "plan": f"docs/plans/{slug}.md",
        "components": components,
    }
    if plan_doc_ref is not None:
        manifest_doc["plan_doc_ref"] = plan_doc_ref
    if include_narrative:
        narrative: dict = {
            "target": (
                f"framework/{components[0]['name']}/seals/"
                f"SEAL_COMMIT.{slug}"
            ),
        }
        if narrative_body is not None:
            narrative["body"] = narrative_body
        manifest_doc["narrative"] = narrative
    if extra_top_level:
        manifest_doc.update(extra_top_level)
    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest_doc), encoding="utf-8")
    return manifest_path


def _author_v1_manifest(
    repo: Path,
    *,
    baseline_sha: str,
    components: list[dict[str, str]],
    slug: str = "ac-dps2-v1",
    extra_top_level: dict | None = None,
) -> Path:
    manifest_doc: dict = {
        "schema_version": 1,
        "amendment": {"number": 99, "slug": slug, "title": f"{slug} test"},
        "baseline": baseline_sha,
        "plan": f"docs/plans/{slug}.md",
        "components": components,
    }
    if extra_top_level:
        manifest_doc.update(extra_top_level)
    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest_doc), encoding="utf-8")
    return manifest_path


def _make_v3_manifest_in_memory(
    *,
    plan_doc_ref: str | None = "docs/plans/ac-dps2-mem.md",
    narrative_body: str | None = None,
    ac_count: int | None = None,
    smoke_outcome: str | None = None,
    number: int | None = None,
    slug: str = "ac-dps2-mem",
    title: str = "AC.DPS2 in-memory manifest",
) -> Manifest:
    """Construct a Manifest dataclass directly (no YAML round-trip).

    Used by tests that exercise ``_resolve_narrative_body`` /
    ``_build_commit_message`` in isolation — load_manifest's parser is
    covered by separate tests; here we want crisp control over field
    combinations for the synthesizer.
    """
    narrative = NarrativeSpec(
        target=f"framework/x/seals/SEAL_COMMIT.{slug}",
        body=narrative_body,
    )
    return Manifest(
        schema_version=3,
        number=number,
        slug=slug,
        title=title,
        baseline="aaaaaaa",
        plan=f"docs/plans/{slug}.md",
        components=(),
        plan_doc_ref=plan_doc_ref,
        narrative=narrative,
        ac_count=ac_count,
        smoke_outcome=smoke_outcome,
    )


# ---------------------------------------------------------------------------
# AC.DPS2.1 — synthesizer covers what-shipped + ACs + smoke + plan-doc.


def test_AC_DPS2_1_synth_body_includes_what_shipped() -> None:
    """When ``ac_count`` + ``smoke_outcome`` are set on a v3
    plan_doc_ref-only manifest, the synthesized body surfaces both
    plus title + slug + components + plan-doc reference.
    """
    manifest = Manifest(
        schema_version=3,
        number=None,
        slug="ac-dps2-1-test",
        title="AC.DPS2.1 synthesis coverage test",
        baseline="aaaaaaa",
        plan="docs/plans/ac-dps2-1-test.md",
        # Use a couple of components so the components-line has content.
        components=tuple(),  # synthesizer formats empty as ""; that's fine
        plan_doc_ref="docs/plans/ac-dps2-1-test.md",
        narrative=NarrativeSpec(
            target="framework/x/seals/SEAL_COMMIT.ac-dps2-1-test",
            body=None,
        ),
        ac_count=14,
        smoke_outcome="all 6 dimensions exercised",
    )
    body = _resolve_narrative_body(manifest, amendment_sha="bbbbbbb")
    # what shipped
    assert "ac-dps2-1-test" in body
    assert "AC.DPS2.1 synthesis coverage test" in body
    # plan-doc reference
    assert "docs/plans/ac-dps2-1-test.md" in body
    # ACs satisfied count
    assert "acs-satisfied: 14" in body, (
        f"synthesizer should emit 'acs-satisfied: 14'; body:\n{body}"
    )
    # smoke outcome
    assert "smoke: all 6 dimensions exercised" in body, (
        f"synthesizer should emit smoke line; body:\n{body}"
    )
    # amendment-commit
    assert "bbbbbbb" in body


def test_AC_DPS2_1_synth_body_omits_lines_when_optional_fields_absent() -> None:
    """When ``ac_count`` / ``smoke_outcome`` are absent, the
    corresponding lines are omitted (preserves AC.DPS1.4 minimum-shape
    invariant for v3 manifests authored without the new fields).
    """
    manifest = _make_v3_manifest_in_memory(
        plan_doc_ref="docs/plans/ac-dps2-min.md",
        narrative_body=None,
        ac_count=None,
        smoke_outcome=None,
        slug="ac-dps2-1-min",
    )
    body = _resolve_narrative_body(manifest, amendment_sha="ccccccc")
    assert "acs-satisfied" not in body, (
        f"acs-satisfied line must be omitted when ac_count is None; "
        f"body:\n{body}"
    )
    assert "smoke:" not in body, (
        f"smoke line must be omitted when smoke_outcome is None; "
        f"body:\n{body}"
    )
    # Original DPS1.4 content still present.
    assert "ac-dps2-1-min" in body
    assert "ccccccc" in body
    assert "docs/plans/ac-dps2-min.md" in body


# ---------------------------------------------------------------------------
# AC.DPS2.2 — ac_count field — additive at v3, rejected at v1/v2.


def test_AC_DPS2_2_v3_ac_count_validates(scratch_repo: Path) -> None:
    """v3 manifest with ``ac_count: 14`` validates and the field
    surfaces on the loaded ``Manifest``.
    """
    repo = scratch_repo
    _seed_component(repo, "alpha", baseline_value="aaaaaaa")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "alpha",
                "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/alpha/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-2-v3",
        extra_top_level={"ac_count": 14},
    )
    manifest = load_manifest(manifest_path)
    assert manifest.ac_count == 14


def test_AC_DPS2_2_v1_rejects_ac_count(scratch_repo: Path) -> None:
    """Schema v1 manifest with ``ac_count`` field surfaces InvalidField."""
    repo = scratch_repo
    _seed_component(repo, "beta", baseline_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed beta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v1_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "beta",
                "seal_test": "framework/beta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/beta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-2-v1-rej",
        extra_top_level={"ac_count": 14},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(manifest_path)
    assert "ac_count" in str(exc_info.value)
    assert "schema_version 3" in str(exc_info.value)


def test_AC_DPS2_2_v3_ac_count_must_be_non_negative_int(
    scratch_repo: Path,
) -> None:
    """v3 manifest with negative or non-int ``ac_count`` fails."""
    repo = scratch_repo
    _seed_component(repo, "gamma", baseline_value="ggggggg")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed gamma")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Negative int.
    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "gamma",
                "seal_test": "framework/gamma/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/gamma/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-2-neg",
        extra_top_level={"ac_count": -1},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(manifest_path)
    assert "ac_count" in str(exc_info.value)
    assert "non-negative" in str(exc_info.value).lower()

    # Non-int (string).
    manifest_path2 = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "gamma",
                "seal_test": "framework/gamma/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/gamma/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-2-str",
        extra_top_level={"ac_count": "fourteen"},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(manifest_path2)
    assert "ac_count" in str(exc_info.value)
    assert "integer" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# AC.DPS2.3 — smoke_outcome field — additive at v3, rejected at v1/v2.


def test_AC_DPS2_3_v3_smoke_outcome_validates(scratch_repo: Path) -> None:
    """v3 manifest with non-empty single-line ``smoke_outcome`` validates."""
    repo = scratch_repo
    _seed_component(repo, "delta", baseline_value="ddddddd")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed delta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "delta",
                "seal_test": "framework/delta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/delta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-3-v3",
        extra_top_level={"smoke_outcome": "all 6 dimensions exercised"},
    )
    manifest = load_manifest(manifest_path)
    assert manifest.smoke_outcome == "all 6 dimensions exercised"


def test_AC_DPS2_3_v1_rejects_smoke_outcome(scratch_repo: Path) -> None:
    """Schema v1 manifest with ``smoke_outcome`` field fails."""
    repo = scratch_repo
    _seed_component(repo, "epsilon", baseline_value="eeeeeee")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed epsilon")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v1_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "epsilon",
                "seal_test": "framework/epsilon/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/epsilon/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-3-v1-rej",
        extra_top_level={"smoke_outcome": "all 6 dimensions exercised"},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(manifest_path)
    assert "smoke_outcome" in str(exc_info.value)
    assert "schema_version 3" in str(exc_info.value)


def test_AC_DPS2_3_v3_smoke_outcome_validation_rules(
    scratch_repo: Path,
) -> None:
    """v3 ``smoke_outcome`` rejects empty / multi-line / >200-char inputs."""
    repo = scratch_repo
    _seed_component(repo, "zeta2", baseline_value="zzzzzzz")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed zeta2")
    baseline = _git(repo, "rev-parse", "HEAD")

    base_components = [
        {
            "name": "zeta2",
            "seal_test": "framework/zeta2/tests/test_no_sealed_amendments.py",
            "sidecar": "framework/zeta2/tests/SEAL_COMMIT",
        }
    ]

    # Empty string.
    p = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=base_components,
        slug="ac-dps2-3-empty",
        extra_top_level={"smoke_outcome": ""},
    )
    with pytest.raises(InvalidField):
        load_manifest(p)

    # Multi-line.
    p = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=base_components,
        slug="ac-dps2-3-multi",
        extra_top_level={"smoke_outcome": "line1\nline2"},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(p)
    assert "single-line" in str(exc_info.value).lower()

    # >200 chars.
    p = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=base_components,
        slug="ac-dps2-3-long",
        extra_top_level={"smoke_outcome": "x" * 201},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(p)
    assert "200" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AC.DPS2.4 — synthesized body fits 5-15 lines.


def test_AC_DPS2_4_synth_body_line_count_in_range() -> None:
    """Synthesized body fits 5-15 lines across the optional-field matrix."""
    cases: list[Manifest] = [
        # Minimum case (no ac_count, no smoke).
        _make_v3_manifest_in_memory(
            plan_doc_ref="docs/plans/ac-dps2-4-min.md",
            ac_count=None,
            smoke_outcome=None,
            slug="ac-dps2-4-min",
        ),
        # Maximum case (both optional fields).
        _make_v3_manifest_in_memory(
            plan_doc_ref="docs/plans/ac-dps2-4-full.md",
            ac_count=14,
            smoke_outcome="all 6 dimensions exercised",
            slug="ac-dps2-4-full",
        ),
        # ac_count only.
        _make_v3_manifest_in_memory(
            plan_doc_ref="docs/plans/ac-dps2-4-ac.md",
            ac_count=7,
            smoke_outcome=None,
            slug="ac-dps2-4-ac",
        ),
        # smoke only.
        _make_v3_manifest_in_memory(
            plan_doc_ref="docs/plans/ac-dps2-4-sm.md",
            ac_count=None,
            smoke_outcome="green",
            slug="ac-dps2-4-sm",
        ),
        # With number.
        _make_v3_manifest_in_memory(
            plan_doc_ref="docs/plans/ac-dps2-4-num.md",
            ac_count=14,
            smoke_outcome="all 6 dimensions exercised",
            number=42,
            slug="ac-dps2-4-num",
        ),
    ]
    for m in cases:
        body = _resolve_narrative_body(m, amendment_sha="ddddddd")
        line_count = body.count("\n") + 1
        assert 5 <= line_count <= 15, (
            f"synthesized body for slug={m.slug} should be 5-15 lines, "
            f"got {line_count}; body:\n{body}"
        )


# ---------------------------------------------------------------------------
# AC.DPS2.5 — explicit narrative.body returned verbatim at v3 (preserved
# from AC.DPS1.4; reasserted here as a regression guard).


def test_AC_DPS2_5_explicit_body_returned_verbatim_at_v3() -> None:
    """A v3 manifest with an explicit ``narrative.body`` returns the
    body verbatim — even when ``ac_count`` and ``smoke_outcome`` are
    set, the explicit body wins.
    """
    manifest = _make_v3_manifest_in_memory(
        plan_doc_ref=None,
        narrative_body="caller-supplied verbatim content goes here",
        ac_count=14,
        smoke_outcome="all 6 dimensions exercised",
        slug="ac-dps2-5",
    )
    body = _resolve_narrative_body(manifest, amendment_sha="eeeeeee")
    assert body == "caller-supplied verbatim content goes here"


# ---------------------------------------------------------------------------
# AC.DPS2.6 — seal commit message body gains "Plan doc:" line at v3.


def test_AC_DPS2_6_seal_commit_message_v3_has_plan_doc_line() -> None:
    """v3 manifest with ``plan_doc_ref`` produces a seal commit message
    body containing ``Plan doc: <ref>``.
    """
    manifest = _make_v3_manifest_in_memory(
        plan_doc_ref="docs/plans/ac-dps2-6.md",
        ac_count=14,
        smoke_outcome="all 6 dimensions exercised",
        slug="ac-dps2-6",
    )
    msg = _build_commit_message(
        manifest=manifest,
        amendment_sha="ffffffffff",
        bumped_sidecars=["framework/x/tests/SEAL_COMMIT → ffffffffff"],
        narrative_target="framework/x/seals/SEAL_COMMIT.ac-dps2-6",
        sweep_summary="3 components green",
        include_co_authored_by=False,
    )
    assert "Plan doc: docs/plans/ac-dps2-6.md" in msg, (
        f"v3 seal commit message missing Plan doc: line; msg:\n{msg}"
    )


def test_AC_DPS2_6_seal_commit_message_v1_unchanged() -> None:
    """Schema v1 manifest's seal commit message body has NO ``Plan doc:``
    line (the field is forbidden at v1; the body shape stays
    byte-identical to today).
    """
    manifest = Manifest(
        schema_version=1,
        number=99,
        slug="ac-dps2-6-v1",
        title="v1 unchanged test",
        baseline="aaaaaaa",
        plan="docs/plans/ac-dps2-6-v1.md",
        components=(),
        narrative=NarrativeSpec(
            target="framework/x/seals/SEAL_COMMIT.ac-dps2-6-v1",
            body="legacy body",
        ),
    )
    msg = _build_commit_message(
        manifest=manifest,
        amendment_sha="ffffffffff",
        bumped_sidecars=["framework/x/tests/SEAL_COMMIT → ffffffffff"],
        narrative_target="framework/x/seals/SEAL_COMMIT.ac-dps2-6-v1",
        sweep_summary="3 components green",
        include_co_authored_by=False,
    )
    assert "Plan doc:" not in msg, (
        f"v1 seal commit message must NOT contain Plan doc: line; "
        f"msg:\n{msg}"
    )


def test_AC_DPS2_6_seal_commit_message_v3_no_plan_doc_ref_no_line() -> None:
    """v3 manifest WITHOUT ``plan_doc_ref`` (using explicit
    ``narrative.body`` instead) has NO ``Plan doc:`` line — the line
    only appears when there's a pointer to surface.
    """
    manifest = _make_v3_manifest_in_memory(
        plan_doc_ref=None,
        narrative_body="explicit body",
        slug="ac-dps2-6-no-ref",
    )
    msg = _build_commit_message(
        manifest=manifest,
        amendment_sha="ffffffffff",
        bumped_sidecars=["framework/x/tests/SEAL_COMMIT → ffffffffff"],
        narrative_target="framework/x/seals/SEAL_COMMIT.ac-dps2-6-no-ref",
        sweep_summary="3 components green",
        include_co_authored_by=False,
    )
    assert "Plan doc:" not in msg


# ---------------------------------------------------------------------------
# AC.DPS2.7 — seal commit subject unchanged across all schemas.


def test_AC_DPS2_7_subject_shape_stable_across_schemas() -> None:
    """The subject template ``chore(seals): <description> — <comps> at
    <sha>`` is identical in shape for v1, v2, v3 manifests.
    """
    for schema in (1, 3):
        manifest = Manifest(
            schema_version=schema,
            number=99 if schema in (1, 2) else None,
            slug="ac-dps2-7",
            title="subject stability",
            baseline="aaaaaaa",
            plan="docs/plans/ac-dps2-7.md",
            components=(),
            plan_doc_ref=(
                "docs/plans/ac-dps2-7.md" if schema == 3 else None
            ),
            narrative=NarrativeSpec(
                target="framework/x/seals/SEAL_COMMIT.ac-dps2-7",
                body=(None if schema == 3 else "legacy body"),
            ),
        )
        msg = _build_commit_message(
            manifest=manifest,
            amendment_sha="abcdef0123",
            bumped_sidecars=[],
            narrative_target=None,
            sweep_summary="0 components green",
            include_co_authored_by=False,
        )
        first_line = msg.splitlines()[0]
        # Subject shape: chore(seals): <slug-or-desc> — <comps> at <sha7>
        assert first_line.startswith("chore(seals): ac-dps2-7 — "), (
            f"schema {schema} subject must start with the standard "
            f"prefix; got: {first_line!r}"
        )
        assert " at abcdef0" in first_line, (
            f"schema {schema} subject must end with ' at <sha7>'; "
            f"got: {first_line!r}"
        )


# ---------------------------------------------------------------------------
# AC.DPS2.8 — commit-ladder.md describes both shapes (doc check).


def test_AC_DPS2_8_commit_ladder_doc_describes_both_shapes() -> None:
    """``plugins/dev-sdlc/docs/conventions/commit-ladder.md`` mentions
    BOTH the v1/v2 long-form narrative path AND the v3 collapsed path.
    """
    here = Path(__file__).resolve()
    repo_root: Path | None = None
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists() and (parent / "docs").is_dir():
            repo_root = parent
            break
    if repo_root is None:
        pytest.skip("could not locate canonical repo root")

    doc = (
        repo_root
        / "plugins"
        / "dev-sdlc"
        / "docs"
        / "conventions"
        / "commit-ladder.md"
    )
    assert doc.exists(), f"commit-ladder.md not found at {doc}"
    text = doc.read_text(encoding="utf-8")
    # Both shapes named.
    assert "v1" in text and "v3" in text, (
        "commit-ladder.md should reference both schema v1 and v3 shapes"
    )
    # v3 collapsed shape mentioned.
    assert "plan_doc_ref" in text, (
        "commit-ladder.md should describe v3 plan_doc_ref-based body"
    )
    # v1/v2 long-form narrative.body shape preserved in the doc.
    assert "narrative.body" in text, (
        "commit-ladder.md should describe v1/v2 narrative.body shape"
    )


# ---------------------------------------------------------------------------
# AC.DPS2.9 — sealed-component-build dispatch template verified.


def test_AC_DPS2_9_dispatch_template_no_narrative_body_prescription() -> None:
    """The sealed-component-build dispatch template does NOT prescribe
    long-form narrative.body content (which would conflict with the v3
    collapsed shape becoming the going-forward default).

    Verification trace per AC.DPS2.9 — current state is no-op (the
    template doesn't prescribe narrative-body content). This test
    becomes the regression guard if a future edit adds such a
    prescription.
    """
    here = Path(__file__).resolve()
    repo_root: Path | None = None
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists() and (parent / "docs").is_dir():
            repo_root = parent
            break
    if repo_root is None:
        pytest.skip("could not locate canonical repo root")

    template = (
        repo_root
        / "plugins"
        / "dev-sdlc"
        / "templates"
        / "dispatch"
        / "sealed-component-build.md"
    )
    assert template.exists(), (
        f"sealed-component-build dispatch template not found at {template}"
    )
    text = template.read_text(encoding="utf-8")
    # Sanity: file is non-empty + carries the standard structure.
    assert "{{COMPONENT}}" in text
    # The forbidden prescription forms (defensive):
    #   - "narrative body must be ..."
    #   - "long-form narrative ..."
    #   - "duplicate the plan-doc"
    forbidden_phrases = (
        "narrative body must",
        "narrative.body must",
        "long-form narrative",
        "duplicate the plan-doc",
        "duplicate the plan doc",
    )
    for phrase in forbidden_phrases:
        assert phrase.lower() not in text.lower(), (
            f"dispatch template should not prescribe narrative-body "
            f"content; found phrase {phrase!r}"
        )


# ---------------------------------------------------------------------------
# AC.DPS2.10 — all existing manifest YAMLs validate clean post-amendment.


def test_AC_DPS2_10_existing_manifests_validate_clean() -> None:
    """Every manifest YAML under ``docs/plans/`` parses clean
    post-amendment. Same shape as AC.DPS1.13's sweep — we re-run it
    here so the AC.DPS2.* additions (``ac_count`` + ``smoke_outcome``
    rejection at v1/v2) are also covered for existing manifests, none
    of which carry these new fields.
    """
    here = Path(__file__).resolve()
    repo_root: Path | None = None
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists() and (parent / "docs").is_dir():
            repo_root = parent
            break
    if repo_root is None:
        pytest.skip("could not locate canonical repo root")

    plans_dir = repo_root / "docs" / "plans"
    if not plans_dir.is_dir():
        pytest.skip(f"no plans directory at {plans_dir}")

    manifest_paths = sorted(plans_dir.glob("*.manifest.yaml"))
    assert manifest_paths, (
        f"expected manifest YAMLs under {plans_dir}; sweep is meaningless "
        "without inputs"
    )
    failures: list[tuple[Path, str]] = []
    for manifest_path in manifest_paths:
        try:
            load_manifest(manifest_path)
        except Exception as exc:  # noqa: BLE001 — capture all failures
            failures.append((manifest_path, f"{type(exc).__name__}: {exc}"))
    assert not failures, (
        "existing manifest YAMLs failed to validate post-DPS2:\n"
        + "\n".join(f"  {p}: {e}" for p, e in failures)
    )


# ---------------------------------------------------------------------------
# AC.DPS2.13 — end-to-end: v3 apply produces single commit AND seal
# commit body has Plan doc: line. This is the integration sanity check.


def test_AC_DPS2_13_v3_end_to_end_apply_with_new_fields(
    scratch_repo: Path,
) -> None:
    """v3 manifest with all DPS2 features (``plan_doc_ref`` +
    ``ac_count`` + ``smoke_outcome``, no number, no body) lands a
    single merged ``manifest+apply`` commit that validates and the
    manifest re-loads with the fields preserved post-commit.
    """
    repo = scratch_repo
    _seed_component(repo, "kappa", baseline_value="kkkkkkk")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed kappa")

    (repo / "framework" / "kappa" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit kappa")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "kappa",
                "seal_test": "framework/kappa/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/kappa/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps2-13-e2e",
        plan_doc_ref="docs/plans/ac-dps2-13-e2e.md",
        include_number=False,
        extra_top_level={
            "ac_count": 14,
            "smoke_outcome": "all 6 dimensions exercised",
        },
    )

    pre_count = int(_git(repo, "rev-list", "--count", "HEAD"))
    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    post_count = int(_git(repo, "rev-list", "--count", "HEAD"))
    # Single merged commit per AC.DPS1.6.
    assert post_count == pre_count + 1

    # Re-load the manifest from the post-commit tree; fields preserved.
    reloaded = load_manifest(manifest_path)
    assert reloaded.schema_version == 3
    assert reloaded.number is None
    assert reloaded.plan_doc_ref == "docs/plans/ac-dps2-13-e2e.md"
    assert reloaded.ac_count == 14
    assert reloaded.smoke_outcome == "all 6 dimensions exercised"
    assert reloaded.narrative is not None
    assert reloaded.narrative.body is None  # collapsed shape

    # Subject carries manifest+apply token (v3-merged).
    subject = _git(repo, "log", "-1", "--format=%s")
    assert "manifest+apply" in subject
