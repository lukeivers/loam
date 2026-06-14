"""AC.DPS1.* — dev-pattern simplifications #1.

Plan: ``docs/plans/dev-pattern-simplifications-1.md``.
Source authority: cost-audit 2026-05-04 Recommendations A, D, E.

Coverage:
- AC.DPS1.1  — ``Manifest.plan_doc_ref`` field exposed.
- AC.DPS1.2  — v3 manifest requires ``plan_doc_ref`` OR ``narrative.body``.
- AC.DPS1.3  — v1 / v2 reject ``plan_doc_ref``.
- AC.DPS1.4  — seal synthesizes summary when ``plan_doc_ref`` only.
- AC.DPS1.5  — ``narrative.target`` still required at v3.
- AC.DPS1.6  — apply produces single commit under v3 (manifest+apply merged).
- AC.DPS1.7  — v1 / v2 preserve two-commit shape.
- AC.DPS1.8  — already-committed manifest YAML produces no extra delta.
- AC.DPS1.9  — idempotent re-run skips commit (existing AC.LAE.1).
- AC.DPS1.10 — ``amendment.number`` optional at v3 (typed ``int | None``).
- AC.DPS1.11 — commit subjects degrade gracefully when ``number is None``.
- AC.DPS1.12 — ``new-plan`` does not pre-fill amendment number.
- AC.DPS1.13 — all existing manifests validate clean post-amendment.
- AC.DPS1.14 — sealed amendments stay green (verified at build-time only;
                 not unit-testable without canonical-history fixture).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

from loam_amend.commands.apply import run as apply_run
from loam_amend.commands.new_plan import run as new_plan_run
from loam_amend.commands.seal import _resolve_narrative_body
from loam_amend.manifest import (
    InvalidField,
    Manifest,
    MissingField,
    NarrativeSpec,
    baseline_is_resolvable_commit,
    load_manifest,
)


# ---------------------------------------------------------------------------
# Helpers (mirror existing tests' shape).


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
    slug: str = "ac-dps1",
    title: str = "AC.DPS1 test",
    plan_doc_ref: str | None = "docs/plans/ac-dps1.md",
    narrative_body: str | None = None,
    include_number: bool = False,
    include_narrative: bool = True,
    extra_top_level: dict | None = None,
) -> Path:
    """Author a schema_version-3 manifest at <repo>/manifest.yaml."""
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
    slug: str = "ac-dps1-v1",
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


# ---------------------------------------------------------------------------
# AC.DPS1.1 — Manifest dataclass exposes plan_doc_ref.


def test_AC_DPS1_1_plan_doc_ref_field_present() -> None:
    """Manifest dataclass carries a ``plan_doc_ref`` attribute."""
    # Build a schema-v3 manifest dataclass directly (no YAML) to confirm
    # the field exists and defaults to None.
    m = Manifest(
        schema_version=3,
        number=None,
        slug="x",
        title="x",
        baseline="abcdef0",
        plan="docs/x.md",
        components=(),
        plan_doc_ref="docs/plans/x.md",
    )
    assert m.plan_doc_ref == "docs/plans/x.md"
    # Default is None when omitted.
    m2 = Manifest(
        schema_version=1,
        number=1,
        slug="y",
        title="y",
        baseline="abcdef0",
        plan="docs/y.md",
        components=(),
    )
    assert m2.plan_doc_ref is None


# ---------------------------------------------------------------------------
# AC.DPS1.2 — v3 requires plan_doc_ref OR narrative.body.


def test_AC_DPS1_2_v3_requires_plan_doc_ref_or_narrative_body(
    scratch_repo: Path,
) -> None:
    """v3 manifest with neither plan_doc_ref nor narrative.body rejects."""
    repo = scratch_repo
    _seed_component(repo, "alpha", baseline_value="aaaaaaa")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha")
    baseline = _git(repo, "rev-parse", "HEAD")

    # No plan_doc_ref + narrative omitted → reject.
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
        slug="ac-dps1-2-empty",
        plan_doc_ref=None,
        include_narrative=False,
    )
    with pytest.raises(MissingField) as exc_info:
        load_manifest(manifest_path)
    assert "plan_doc_ref" in str(exc_info.value)


def test_AC_DPS1_2_v3_with_only_plan_doc_ref_validates(
    scratch_repo: Path,
) -> None:
    """v3 manifest with ``plan_doc_ref:`` and narrative.target (no body)
    validates clean (the new collapsed shape).
    """
    repo = scratch_repo
    _seed_component(repo, "beta", baseline_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed beta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "beta",
                "seal_test": "framework/beta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/beta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-2-collapsed",
        plan_doc_ref="docs/plans/ac-dps1-2-collapsed.md",
        narrative_body=None,
    )
    m = load_manifest(manifest_path)
    assert m.schema_version == 3
    assert m.plan_doc_ref == "docs/plans/ac-dps1-2-collapsed.md"
    assert m.narrative is not None
    assert m.narrative.body is None  # body collapsed


def test_AC_DPS1_2_v3_with_only_narrative_body_validates(
    scratch_repo: Path,
) -> None:
    """v3 manifest with explicit narrative.body (no plan_doc_ref) validates
    — transitional shape during migration.
    """
    repo = scratch_repo
    _seed_component(repo, "gamma", baseline_value="ggggggg")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed gamma")
    baseline = _git(repo, "rev-parse", "HEAD")

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
        slug="ac-dps1-2-explicit-body",
        plan_doc_ref=None,
        narrative_body="explicit body content for v3 transitional manifest.",
    )
    m = load_manifest(manifest_path)
    assert m.schema_version == 3
    assert m.plan_doc_ref is None
    assert m.narrative is not None
    assert m.narrative.body == (
        "explicit body content for v3 transitional manifest."
    )


# ---------------------------------------------------------------------------
# AC.DPS1.3 — v1 / v2 reject plan_doc_ref.


def test_AC_DPS1_3_v1_rejects_plan_doc_ref(scratch_repo: Path) -> None:
    """Schema v1 manifest with ``plan_doc_ref`` field surfaces InvalidField."""
    repo = scratch_repo
    _seed_component(repo, "delta", baseline_value="ddddddd")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed delta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v1_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "delta",
                "seal_test": "framework/delta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/delta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-3-v1-rejects",
        extra_top_level={"plan_doc_ref": "docs/plans/x.md"},
    )
    with pytest.raises(InvalidField) as exc_info:
        load_manifest(manifest_path)
    assert "plan_doc_ref" in str(exc_info.value)
    assert "schema_version 3" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AC.DPS1.4 — seal synthesizes summary when plan_doc_ref only.


def test_AC_DPS1_4_seal_synthesizes_summary_from_plan_doc_ref() -> None:
    """``_resolve_narrative_body`` returns a synthesized summary when v3
    manifest has ``plan_doc_ref`` and no ``narrative.body``.
    """
    manifest = Manifest(
        schema_version=3,
        number=None,
        slug="ac-dps1-4-test",
        title="AC.DPS1.4 synthesis test",
        baseline="aaaaaaa",
        plan="docs/plans/ac-dps1-4-test.md",
        components=(),
        plan_doc_ref="docs/plans/ac-dps1-4-test.md",
        narrative=NarrativeSpec(
            target="framework/x/seals/SEAL_COMMIT.ac-dps1-4-test",
            body=None,
        ),
    )
    body = _resolve_narrative_body(manifest, amendment_sha="bbbbbbb")
    # Sanity: body cites slug + plan-doc + amendment SHA.
    assert "ac-dps1-4-test" in body
    assert "docs/plans/ac-dps1-4-test.md" in body
    assert "bbbbbbb" in body
    assert "AC.DPS1.4 synthesis test" in body
    # Body is short (5-15 lines per AC.DPS1.4); count newlines.
    line_count = body.count("\n") + 1
    assert 5 <= line_count <= 15, (
        f"synthesized body should be 5-15 lines, got {line_count}"
    )


def test_AC_DPS1_4_seal_keeps_explicit_body_verbatim() -> None:
    """When v3 manifest sets ``narrative.body``, the body is returned
    verbatim (not replaced by synthesis).
    """
    manifest = Manifest(
        schema_version=3,
        number=None,
        slug="ac-dps1-4-explicit",
        title="explicit body test",
        baseline="aaaaaaa",
        plan="docs/plans/ac-dps1-4-explicit.md",
        components=(),
        plan_doc_ref=None,
        narrative=NarrativeSpec(
            target="framework/x/seals/SEAL_COMMIT.ac-dps1-4-explicit",
            body="caller-supplied verbatim body content",
        ),
    )
    body = _resolve_narrative_body(manifest, amendment_sha="bbbbbbb")
    assert body == "caller-supplied verbatim body content"


def test_AC_DPS1_4_v1_body_returned_verbatim() -> None:
    """Schema v1 manifests always return ``narrative.body`` verbatim."""
    manifest = Manifest(
        schema_version=1,
        number=42,
        slug="ac-dps1-4-v1",
        title="v1 verbatim test",
        baseline="aaaaaaa",
        plan="docs/plans/ac-dps1-4-v1.md",
        components=(),
        narrative=NarrativeSpec(
            target="framework/x/seals/SEAL_COMMIT.ac-dps1-4-v1",
            body="legacy v1 body content",
        ),
    )
    body = _resolve_narrative_body(manifest, amendment_sha="bbbbbbb")
    assert body == "legacy v1 body content"


# ---------------------------------------------------------------------------
# AC.DPS1.5 — narrative.target still required at v3.


def test_AC_DPS1_5_v3_narrative_target_required(scratch_repo: Path) -> None:
    """v3 manifest with ``narrative:`` but no ``target`` rejects."""
    repo = scratch_repo
    _seed_component(repo, "epsilon", baseline_value="eeeeeee")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed epsilon")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Hand-author the manifest with narrative: missing target.
    manifest_doc = {
        "schema_version": 3,
        "amendment": {"slug": "ac-dps1-5", "title": "ac-dps1-5"},
        "baseline": baseline,
        "plan": "docs/plans/ac-dps1-5.md",
        "plan_doc_ref": "docs/plans/ac-dps1-5.md",
        "components": [
            {
                "name": "epsilon",
                "seal_test": "framework/epsilon/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/epsilon/tests/SEAL_COMMIT",
            }
        ],
        "narrative": {"body": "x"},  # no target
    }
    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest_doc), encoding="utf-8")

    with pytest.raises(MissingField) as exc_info:
        load_manifest(manifest_path)
    assert "target" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AC.DPS1.6 — apply produces single commit under v3 (manifest+apply merged).


def test_AC_DPS1_6_v3_apply_produces_single_commit(scratch_repo: Path) -> None:
    """v3 manifest: ``loam amend apply`` lands ONE commit (manifest+apply
    merged), not two — manifest YAML is staged alongside BASELINE/sidecar
    bumps.
    """
    repo = scratch_repo
    _seed_component(repo, "zeta", baseline_value="zzzzzzz")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed zeta")

    # Substantive edit so apply has work to do.
    (repo / "framework" / "zeta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit zeta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "zeta",
                "seal_test": "framework/zeta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/zeta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-6-merged",
    )
    # CRUCIALLY: do NOT pre-commit the manifest YAML. Under v3, apply
    # stages it along with the BASELINE / sidecar edits in ONE commit.
    pre_apply_head = _git(repo, "rev-parse", "HEAD")
    pre_apply_count = int(_git(repo, "rev-list", "--count", "HEAD"))

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0

    post_apply_head = _git(repo, "rev-parse", "HEAD")
    post_apply_count = int(_git(repo, "rev-list", "--count", "HEAD"))
    assert post_apply_head != pre_apply_head, "apply should have committed"
    # CRITICAL ASSERTION: exactly ONE new commit, not two.
    assert post_apply_count == pre_apply_count + 1, (
        f"v3 apply must produce exactly one commit; "
        f"saw {post_apply_count - pre_apply_count} new commit(s)"
    )

    # Subject carries ``manifest+apply`` token.
    subject = _git(repo, "log", "-1", "--format=%s")
    assert "manifest+apply" in subject, (
        f"v3 subject should carry 'manifest+apply' token, got: {subject!r}"
    )

    # The commit includes the manifest YAML in its tree.
    files = _git(repo, "show", "--name-only", "--format=", "HEAD").split("\n")
    files_set = set(f for f in files if f)
    assert "manifest.yaml" in files_set, (
        f"v3 apply commit should include manifest YAML, got: {files_set!r}"
    )
    assert "framework/zeta/tests/SEAL_COMMIT" in files_set


# ---------------------------------------------------------------------------
# AC.DPS1.7 — v1 / v2 preserve two-commit shape.


def test_AC_DPS1_7_v1_preserves_two_commit_shape(scratch_repo: Path) -> None:
    """v1 manifest: apply does NOT stage the manifest YAML; legacy
    two-commit ladder preserved (manifest commit was authored + committed
    BEFORE this apply).
    """
    repo = scratch_repo
    _seed_component(repo, "eta", baseline_value="hhhhhhh")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed eta")

    (repo / "framework" / "eta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit eta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v1_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "eta",
                "seal_test": "framework/eta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/eta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-7-v1",
    )
    # Legacy ladder: manifest committed BEFORE apply.
    _git(repo, "add", "manifest.yaml")
    _git(repo, "commit", "-q", "-m", "manifest")

    pre_apply_head = _git(repo, "rev-parse", "HEAD")
    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    post_apply_head = _git(repo, "rev-parse", "HEAD")
    assert post_apply_head != pre_apply_head, (
        "v1 apply should produce a commit"
    )

    # v1 subject keeps the legacy ``apply`` token (NOT manifest+apply).
    subject = _git(repo, "log", "-1", "--format=%s")
    assert "apply" in subject and "manifest+apply" not in subject, (
        f"v1 subject should use legacy 'apply' token, got: {subject!r}"
    )


# ---------------------------------------------------------------------------
# AC.DPS1.8 — already-committed manifest YAML produces no extra delta.


def test_AC_DPS1_8_already_committed_manifest_yaml_no_extra_delta(
    scratch_repo: Path,
) -> None:
    """v3 apply when the manifest YAML is ALREADY committed: ``git add``
    produces no extra staged delta for the manifest path. The commit's
    body still contains the BASELINE / sidecar deltas.
    """
    repo = scratch_repo
    _seed_component(repo, "theta", baseline_value="ttttttt")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed theta")

    (repo / "framework" / "theta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit theta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "theta",
                "seal_test": "framework/theta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/theta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-8-pre-commit",
    )
    # Pre-commit the manifest YAML (operator-driven).
    _git(repo, "add", "manifest.yaml")
    _git(repo, "commit", "-q", "-m", "manifest pre-commit")

    pre_apply_count = int(_git(repo, "rev-list", "--count", "HEAD"))
    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    post_apply_count = int(_git(repo, "rev-list", "--count", "HEAD"))
    # Only ONE additional commit (the apply commit) — NOT two.
    assert post_apply_count == pre_apply_count + 1

    # Apply commit doesn't include manifest.yaml in its tree (it was
    # already committed; staging produced no delta for that path).
    files = _git(repo, "show", "--name-only", "--format=", "HEAD").split("\n")
    files_set = set(f for f in files if f)
    assert "manifest.yaml" not in files_set, (
        f"already-committed manifest should not appear in apply commit's "
        f"tree, got: {files_set!r}"
    )
    assert "framework/theta/tests/SEAL_COMMIT" in files_set


# ---------------------------------------------------------------------------
# AC.DPS1.9 — idempotent re-run skips commit (covered by AC.LAE.1 tests
# already; we add a v3-specific confirmation here).


def test_AC_DPS1_9_v3_idempotent_re_run_skips(scratch_repo: Path) -> None:
    repo = scratch_repo
    _seed_component(repo, "iota", baseline_value="iiiiiii")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed iota")

    (repo / "framework" / "iota" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit iota")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "iota",
                "seal_test": "framework/iota/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/iota/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-9-idem",
    )

    rc1 = apply_run(manifest_path, dry_run=False)
    assert rc1 == 0
    head1 = _git(repo, "rev-parse", "HEAD")

    # Second apply: nothing to commit.
    rc2 = apply_run(manifest_path, dry_run=False)
    assert rc2 == 0
    head2 = _git(repo, "rev-parse", "HEAD")
    assert head1 == head2, "idempotent v3 re-run must not advance HEAD"


# ---------------------------------------------------------------------------
# AC.DPS1.10 — amendment.number optional at v3.


def test_AC_DPS1_10_v3_number_optional(scratch_repo: Path) -> None:
    """v3 manifest WITHOUT ``amendment.number`` validates clean."""
    repo = scratch_repo
    _seed_component(repo, "kappa", baseline_value="kkkkkkk")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed kappa")
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
        slug="ac-dps1-10-no-number",
        include_number=False,
    )
    m = load_manifest(manifest_path)
    assert m.number is None, (
        f"v3 manifest with no number should parse with number=None, "
        f"got: {m.number!r}"
    )
    assert m.slug == "ac-dps1-10-no-number"


def test_AC_DPS1_10_v1_still_requires_number(scratch_repo: Path) -> None:
    """v1 manifest WITHOUT ``amendment.number`` rejects (backward-compat)."""
    repo = scratch_repo
    _seed_component(repo, "lambda", baseline_value="lllllll")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed lambda")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_doc = {
        "schema_version": 1,
        "amendment": {"slug": "ac-dps1-10-v1", "title": "ac-dps1-10-v1"},
        "baseline": baseline,
        "plan": "docs/plans/ac-dps1-10-v1.md",
        "components": [
            {
                "name": "lambda",
                "seal_test": "framework/lambda/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/lambda/tests/SEAL_COMMIT",
            }
        ],
    }
    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest_doc), encoding="utf-8")

    with pytest.raises(MissingField) as exc_info:
        load_manifest(manifest_path)
    assert "number" in str(exc_info.value)


def test_AC_DPS1_10_v3_number_with_value_validates(scratch_repo: Path) -> None:
    """v3 manifest WITH ``amendment.number`` validates (transitional)."""
    repo = scratch_repo
    _seed_component(repo, "mu", baseline_value="mmmmmmm")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed mu")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "mu",
                "seal_test": "framework/mu/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/mu/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-10-v3-with-number",
        include_number=True,
    )
    m = load_manifest(manifest_path)
    assert m.number == 999


# ---------------------------------------------------------------------------
# AC.DPS1.11 — commit subjects degrade gracefully when number is None.


def test_AC_DPS1_11_apply_subject_no_number(scratch_repo: Path) -> None:
    """v3 apply commit subject + body identify by slug when number=None."""
    repo = scratch_repo
    _seed_component(repo, "nu", baseline_value="nnnnnnn")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed nu")

    (repo / "framework" / "nu" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit nu")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_v3_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "nu",
                "seal_test": "framework/nu/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/nu/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-dps1-11-no-number",
        include_number=False,
    )

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B")
    # Body identifies by slug (no #N).
    assert "ac-dps1-11-no-number" in body
    # Body must NOT contain a stray "#" reference followed by digits.
    # Specifically the legacy "Apply commit for amendment #<n>" line.
    assert "Apply commit for amendment #" not in body, (
        f"body should drop '#N' reference when number is None, got: {body!r}"
    )
    # The new shape is "Apply commit for amendment <slug>."
    assert (
        "Apply commit for amendment ac-dps1-11-no-number." in body
    ), f"body missing slug-based amendment ref, got: {body!r}"


# ---------------------------------------------------------------------------
# AC.DPS1.12 — new-plan does not pre-fill amendment number.


def test_AC_DPS1_12_new_plan_does_not_prefill_number(
    scratch_repo: Path,
) -> None:
    """``loam amend new-plan`` scaffold does NOT include any
    amendment-number field in the vars-file output.
    """
    repo = scratch_repo
    rc = new_plan_run(
        slug="ac-dps1-12-test",
        title="ac-dps1-12 test",
        ac_prefix="DPS1.12",
        repo_root=repo,
    )
    assert rc == 0
    vars_file = repo / "docs" / "plans" / "ac-dps1-12-test.vars.yaml"
    assert vars_file.exists()
    content = vars_file.read_text(encoding="utf-8")
    # The scaffold must not contain any literal "amendment number" /
    # "amendment_number" / "AMENDMENT_NUMBER" / "number:" prefilling.
    # We accept the word "number" in commentary (e.g. "behaviour count")
    # but not as a YAML key.
    for forbidden in (
        "amendment_number:",
        "AMENDMENT_NUMBER:",
        "amendment.number:",
        "number: 1",
        "number: 2",
        "number: 99",
    ):
        assert forbidden not in content, (
            f"scaffolded vars-file should not pre-fill {forbidden!r}; "
            f"content head:\n{content[:500]}"
        )


# ---------------------------------------------------------------------------
# AC.DPS1.13 — all existing manifests validate clean post-amendment.
#
# This test validates EVERY existing manifest YAML under
# docs/plans/. If the schema bump broke any of them, this fails
# with the offending path.


def test_AC_DPS1_13_existing_manifests_validate_clean() -> None:
    """All manifest YAMLs in the canonical tree continue to parse clean."""
    # Locate the canonical tree by walking up from this test file to a
    # marker (CLAUDE.md). This matches how the rest of the test suite
    # finds the repo root in canonical (non-scratch) tests.
    here = Path(__file__).resolve()
    repo_root: Path | None = None
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists() and (parent / "docs").is_dir():
            repo_root = parent
            break
    if repo_root is None:
        pytest.skip(
            "could not locate canonical repo root — skipping backward-compat sweep"
        )

    plans_dir = repo_root / "docs" / "plans"
    if not plans_dir.is_dir():
        pytest.skip(f"no plans directory at {plans_dir}")

    manifest_paths = sorted(plans_dir.glob("*.manifest.yaml"))
    assert manifest_paths, (
        f"expected manifest YAMLs under {plans_dir}; sweep is meaningless "
        "without inputs"
    )
    # AC.GFLOOR2.{1,2} — D-GFLOOR2.1: validate only manifests whose
    # baseline is a REAL resolvable commit-ish; SKIP placeholder/draft
    # markers (PENDING-*, PLAN_DOC_COMMIT, any non-hex / unresolvable
    # value) whose baseline resolves at THEIR OWN apply/seal. This
    # decouples an unrelated cycle's seal from in-flight draft plans'
    # not-yet-resolved baselines while keeping the class-5 protection
    # for applied/sealed (real-baseline) manifests fully intact.
    failures: list[tuple[Path, str]] = []
    for manifest_path in manifest_paths:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        baseline = (raw or {}).get("baseline")
        if not isinstance(baseline, str) or not baseline_is_resolvable_commit(
            baseline, repo_root
        ):
            # Draft / placeholder baseline — not yet anchored to this
            # repo's history; validated at its own apply/seal, not here.
            continue
        try:
            load_manifest(manifest_path)
        except Exception as exc:  # noqa: BLE001 — capture all failures
            failures.append((manifest_path, f"{type(exc).__name__}: {exc}"))
    assert not failures, (
        "existing manifest YAMLs failed to validate post-schema bump:\n"
        + "\n".join(f"  {p}: {e}" for p, e in failures)
    )
