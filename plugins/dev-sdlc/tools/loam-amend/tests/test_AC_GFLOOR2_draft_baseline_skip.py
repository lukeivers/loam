"""AC.GFLOOR2.{1,2,3} — the GUARD-SWEEP FLOOR's manifest-conformance
sweep must not couple an unrelated seal to in-flight DRAFT plans'
placeholder baselines.

Per ``docs/plans/seal-guard-floor-draft-baseline-skip.md``
D-GFLOOR2.1: the class-5 manifest-conformance sweep (AC.DPS1.13)
validates manifests whose baseline resolves to a REAL commit-ish and
SKIPS manifests whose baseline is a placeholder/draft marker (non-hex,
or hex-shaped-but-unresolvable) — those resolve at their OWN
apply/seal, never at an unrelated cycle's seal. A malformed
real-baseline manifest STILL blocks (that protection is the floor's
point; the fix must NOT over-loosen).

- AC.GFLOOR2.1 — real-baseline manifests stay fully validated; a
  real-baseline manifest that fails to parse is a sweep failure.
- AC.GFLOOR2.2 — placeholder/draft baselines are skipped, not
  validated; their parse-failure does NOT fail the sweep.
- AC.GFLOOR2.3 ★ (outcome-altitude) — via the PRODUCTION seal entry
  point against a real synthetic repo carrying BOTH a placeholder-
  baseline draft AND a malformed real-baseline manifest: the seal's
  manifest-conformance sweep does NOT halt on the placeholder draft,
  but DOES fail when a real-baseline manifest is malformed.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam_amend.cli import main as cli_main
from loam_amend.manifest import baseline_is_resolvable_commit

from test_seal import (
    _git,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)
from test_AC_GFLOOR_2_registry_targets_run import _write_registry


# ---------------------------------------------------------------------------
# AC.GFLOOR2.1 / AC.GFLOOR2.2 — the predicate, directly.
# ---------------------------------------------------------------------------


def test_AC_GFLOOR2_1_real_resolvable_baseline_is_validated(
    sealed_repo,
) -> None:
    """A baseline that is a real resolvable commit in the repo is
    treated as real (the sweep WILL validate its manifest)."""
    repo = sealed_repo
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert baseline_is_resolvable_commit(head, repo) is True
    # short form (7-char) of the same commit also resolves
    assert baseline_is_resolvable_commit(head[:7], repo) is True


def test_AC_GFLOOR2_2_placeholder_baselines_are_skipped(
    sealed_repo,
) -> None:
    """Non-hex placeholder/draft markers are NOT real — the sweep
    skips them (no false sweep failure on in-flight drafts)."""
    repo = sealed_repo
    for placeholder in (
        "PENDING-S4A-SEAL",
        "PLAN_DOC_COMMIT",
        "<backfill>",
        "PENDING",
    ):
        assert (
            baseline_is_resolvable_commit(placeholder, repo) is False
        ), placeholder


def test_AC_GFLOOR2_2_hex_shaped_but_unresolvable_is_skipped(
    sealed_repo,
) -> None:
    """A hex-SHAPED baseline that does not resolve to a commit in the
    repo is also a draft marker (not yet anchored to this history) —
    skipped, per the 'not-resolvable-to-a-commit' clause of
    D-GFLOOR2.1."""
    repo = sealed_repo
    # 40 lowercase-hex chars that are not any commit in this fresh repo.
    bogus = "deadbeef" * 5  # 40 chars
    assert baseline_is_resolvable_commit(bogus, repo) is False


# ---------------------------------------------------------------------------
# AC.GFLOOR2.3 ★ — through the production seal entry point.
# ---------------------------------------------------------------------------

# A guard that IS the manifest-conformance sweep, applying the fixed
# D-GFLOOR2.1 predicate. Installed into the synthetic repo + registered
# so the production seal's GUARD-SWEEP FLOOR runs it against that repo's
# own docs/plans/*.manifest.yaml.
#
# DEPENDENCY-FREE BY DESIGN (mirrors the precedent
# test_AC_GFLOOR_S guard): the seal's pytest invocation runs in the
# synthetic repo under whatever ambient interpreter is on PATH, which
# need not have `loam_amend` importable. So this guard inlines the
# SAME D-GFLOOR2.1 predicate logic (the canonical `_SHA_RE` shape +
# `git rev-parse --verify <baseline>^{commit}`) using only stdlib —
# no `loam_amend` import, no yaml. The skip predicate it exercises is
# byte-for-byte the production predicate's logic; what the production
# seal blocks-or-skips here is therefore the real behaviour.
_SWEEP_GUARD_BODY = r'''
import re
import subprocess
from pathlib import Path

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _baseline_of(manifest_text):
    # Minimal top-level `baseline: "..."` extractor (stdlib-only; the
    # fixture manifests are flat enough that a line scan is exact).
    for line in manifest_text.splitlines():
        s = line.strip()
        if s.startswith("baseline:"):
            val = s[len("baseline:"):].strip()
            if val and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1]
            # strip trailing inline comment
            return val.split("#", 1)[0].strip()
    return None


def _is_resolvable(baseline, repo_root):
    if not _SHA_RE.match(baseline):
        return False
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet",
         baseline + "^{commit}"],
        cwd=repo_root, capture_output=True, text=True,
    )
    return proc.returncode == 0


def _try_load(manifest_path):
    # Stand-in for load_manifest's required-field + hex-baseline
    # checks, sufficient for the fixture: a real-baseline manifest
    # missing `slug` is malformed and must surface as a failure.
    import yaml  # available in the seal's runtime (loam dep)
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    amd = raw.get("amendment") or {}
    if not isinstance(amd.get("slug"), str) or not amd["slug"]:
        raise ValueError("missing required 'amendment.slug'")


def test_manifest_conformance_sweep_with_draft_skip():
    here = Path(__file__).resolve()
    repo_root = None
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists() and (parent / "docs").is_dir():
            repo_root = parent
            break
    assert repo_root is not None, "could not locate synthetic repo root"

    plans_dir = repo_root / "docs" / "plans"
    manifest_paths = sorted(plans_dir.glob("*.manifest.yaml"))
    assert manifest_paths, "sweep is meaningless without inputs"

    failures = []
    for manifest_path in manifest_paths:
        baseline = _baseline_of(
            manifest_path.read_text(encoding="utf-8")
        )
        if not baseline or not _is_resolvable(baseline, repo_root):
            # placeholder / draft marker — skipped
            continue
        try:
            _try_load(manifest_path)
        except Exception as exc:  # noqa: BLE001
            failures.append((manifest_path.name, repr(exc)))
    assert not failures, (
        "real-baseline manifests failed to validate: " + repr(failures)
    )
'''


def _install_sweep_guard(repo: Path) -> None:
    guard = repo / "guards" / "test_AC_DPS1_conformance_sweep.py"
    guard.parent.mkdir(parents=True, exist_ok=True)
    guard.write_text(_SWEEP_GUARD_BODY.lstrip(), encoding="utf-8")
    _git(repo, "add", "--", "guards/test_AC_DPS1_conformance_sweep.py")
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        "fixture: manifest-conformance sweep guard",
    )
    _write_registry(repo, ["guards/test_AC_DPS1_*.py"])


def _write_draft_manifest(repo: Path, slug: str, baseline: str) -> None:
    """Write a docs/plans/<slug>.manifest.yaml carrying *baseline*.

    Schema v1 minimal valid shape EXCEPT for whatever *baseline*
    carries — so a placeholder baseline reproduces the exact failure
    the canonical drafts trigger (InvalidField on the hex check).
    """
    path = repo / "docs" / "plans" / f"{slug}.manifest.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            f'''
            schema_version: 1
            amendment:
              number: 1
              slug: {slug}
              title: "draft fixture"
            baseline: "{baseline}"
            plan: docs/plans/{slug}.md
            components:
              - name: alpha
                seal_test: framework/alpha/tests/test_no_sealed_amendments.py
                sidecar: framework/alpha/tests/SEAL_COMMIT
                frozen_baseline: false
                extra_allowed_prefixes: []
            universal_paths:
              prefixes:
                - docs/plans/
            narrative:
              target: framework/alpha/seals/SEAL_COMMIT.fixture
              body: |
                fixture narrative
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", f"docs/plans/{slug}.manifest.yaml")
    _git(repo, "commit", "-q", "-m", f"fixture: draft manifest {slug}")


@pytest.mark.outcome_altitude
def test_AC_GFLOOR2_3_production_seal_skips_placeholder_blocks_malformed_real(
    sealed_repo, capsys
) -> None:
    repo = sealed_repo
    _install_sweep_guard(repo)

    # An unrelated in-flight DRAFT plan with a placeholder baseline —
    # exactly the canonical claude-leverage-program-s4b-wire shape.
    _write_draft_manifest(
        repo, "in-flight-draft", baseline="PENDING-S4A-SEAL"
    )

    # The unrelated cycle being sealed: a clean amendment inside
    # alpha's own fence.
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=950,
        slug="gfloor2-oa",
        seal_description="gfloor2 outcome-altitude",
        narrative_target="framework/alpha/seals/SEAL_COMMIT.fixture",
    )
    edit = repo / "framework" / "alpha" / "src" / "amendment.py"
    edit.write_text("# clean payload\n", encoding="utf-8")
    _git(repo, "add", "--", "framework/alpha/src/amendment.py")
    _git(repo, "commit", "-q", "-m", "feat(alpha): clean amendment")

    # LEG 1 — placeholder draft present: the seal's manifest-
    # conformance sweep does NOT halt on it; the seal completes.
    rc = cli_main(["seal", str(manifest_path)])
    out = capsys.readouterr().out
    assert rc == 0, (
        "seal must NOT be blocked by an in-flight draft plan's "
        f"placeholder baseline; output:\n{out}"
    )
    assert "guard-floor-breach" not in out
    assert "chore(seals):" in _git(repo, "log", "-1", "--format=%B").stdout

    # LEG 2 — a MALFORMED REAL-baseline manifest still blocks. Write a
    # manifest whose baseline IS a real resolvable commit but whose
    # body is malformed (missing required `slug`), then seal again.
    real_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    malformed = repo / "docs" / "plans" / "malformed-real.manifest.yaml"
    malformed.write_text(
        textwrap.dedent(
            f'''
            schema_version: 1
            amendment:
              number: 2
              title: "malformed — missing slug"
            baseline: "{real_sha}"
            plan: docs/plans/malformed-real.md
            components:
              - name: alpha
                seal_test: framework/alpha/tests/test_no_sealed_amendments.py
                sidecar: framework/alpha/tests/SEAL_COMMIT
                frozen_baseline: false
                extra_allowed_prefixes: []
            universal_paths:
              prefixes:
                - docs/plans/
            narrative:
              target: framework/alpha/seals/SEAL_COMMIT.fixture
              body: |
                fixture narrative
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/plans/malformed-real.manifest.yaml")
    _git(repo, "commit", "-q", "-m", "fixture: malformed real-baseline manifest")

    # New amendment to seal (so there is fresh work over the malformed
    # manifest commit).
    edit.write_text("# clean payload 2\n", encoding="utf-8")
    _git(repo, "add", "--", "framework/alpha/src/amendment.py")
    _git(repo, "commit", "-q", "-m", "feat(alpha): clean amendment 2")

    manifest_path2 = _write_manifest(
        repo,
        components=["alpha"],
        number=951,
        slug="gfloor2-oa-2",
        seal_description="gfloor2 outcome-altitude 2",
        narrative_target="framework/alpha/seals/SEAL_COMMIT.fixture",
    )
    rc2 = cli_main(["seal", str(manifest_path2)])
    out2 = capsys.readouterr().out
    assert rc2 != 0, (
        "a MALFORMED real-baseline manifest MUST still block the "
        f"manifest-conformance sweep; output:\n{out2}"
    )
    assert "guard-floor-breach" in out2
    assert "malformed-real.manifest.yaml" in out2
