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

"""AC.PCVR.{3,4} — Per-component pyproject version lockstep regression.

Per ``docs/plans/per-component-pyproject-version-lockstep-regression-closure.md``:

- AC.PCVR.3: enumerate every in-scope component ``pyproject.toml``, assert each
  ``[project].version`` field equals the value in ``docs/ACTIVE_MINOR``. Fail
  with a clear corrective message on drift.
- AC.PCVR.4: outcome-altitude mutation-detection — invoke the assertion helper
  against a deliberately-drifted fixture pyproject in ``tmp_path``, assert the
  helper raises with the corrective-message shape, revert, assert it passes.

The in-scope allowlist EXCLUDES two measurement / experimental harness
pyprojects with deliberate ``version = "0.0.0"`` semantics (handsoff-loop,
loam-spawn-isolation) per plan-doc §16 finding #1 ruling. The exclusion is documented in
``docs/release-versioning-policy.md`` ("Per-component pyproject version
anchor" section).

Per D-NFCLEAN.4 (v0.8.1) + D-SDPD (v0.8.2): per-component-version discipline
advances with MINORs only; PATCHes ride predecessor MINOR. The anchor file
``docs/ACTIVE_MINOR`` carries the current shipped MINOR (e.g., ``0.12.0``).
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import pytest

# In-scope component pyprojects — Tier-0 enumerated at plan-time
# (2026-05-23). Single source-of-truth shared between AC.PCVR.1's sweep
# and AC.PCVR.3's regression assertion. Adding a new shipped component
# pyproject requires adding it here AND running the sweep at the
# next MINOR.
#
# v1.0.0 release cut (2026-06-01): state-migration-engine + protection-
# matrix FOLDED INTO lockstep. Both are shipped runtime components (the
# `loam migrate` + `loam guards` entry-point verbs), sealed (own
# SEAL_COMMIT sidecars), and in the install graph — so by the policy's
# own "shipped runtime components" criterion they belong in-scope. They
# were tree-added after the 2026-05-23 enumeration and rode off-lockstep
# (0.13.0 / 0.1.0) through v0.14.0 as documented intentional outliers;
# the pre-1.0 documentation health check flagged the fold-in "at the
# next release-cut" — this cut. Bumped 0.13.0/0.1.0 -> 1.0.0.
#
# v1.1.0 release cut (2026-06-03): egress-consent + usage-window-guard
# FOLDED INTO lockstep. Both are NEW shipped runtime components introduced
# in this MINOR (the egress-consent privacy gate + the usage-window-guard
# OAuth usage probe), sealed and in the install graph, so by the policy's
# "shipped runtime components" criterion they belong in-scope. They were
# tree-added at 1.0.0 and join the lockstep at this cut. Bumped 1.0.0 ->
# 1.1.0 alongside the existing cohort.
#
# v1.13.0 release cut (operational-backplane integration): the five NEW
# backplane runtime components (file-lease-registry, fleet-collector,
# fleet-page, weekly-cap-alert, weekly-cost-rollup) + adversarial-review
# FOLDED INTO lockstep. The five ship for the first time in this MINOR and
# adversarial-review (a pre-existing 0.1.0 straggler, never previously in
# the lockstep) is now a registered install-graph runtime component
# (added to install-from-source.txt this cut) — so by the policy's
# "shipped runtime components" criterion all six belong in-scope. The five
# were tree-added at 0.0.0 and adversarial-review at 0.1.0; all bumped to
# 1.13.0 alongside the existing cohort. Same precedent as the v1.0.0 /
# v1.1.0 fold-ins above (plain release-commit edit; the dev-sdlc seal-test
# stays GREEN because the version field / allowlist edit lands outside
# every BASELINE..SEAL_COMMIT fence window).
IN_SCOPE_PYPROJECTS: tuple[str, ...] = (
    "framework/cost-governance/pyproject.toml",
    "framework/dormancy/pyproject.toml",
    "framework/egress-consent/pyproject.toml",
    "framework/loam-init/pyproject.toml",
    "framework/objective-tracker/pyproject.toml",
    "framework/observability-aggregator/pyproject.toml",
    "framework/orchestrator/pyproject.toml",
    "framework/per-project-pm/pyproject.toml",
    "framework/primary-persona/pyproject.toml",
    "framework/protection-matrix/pyproject.toml",
    "framework/reversibility-primitive/pyproject.toml",
    "framework/safety-layer/pyproject.toml",
    "framework/scope-of-work/pyproject.toml",
    "framework/self-correction/pyproject.toml",
    "framework/self-upgrade/pyproject.toml",
    "framework/state-migration-engine/pyproject.toml",
    "framework/telegram-interface/pyproject.toml",
    "framework/tools/heavy-b-migrate/pyproject.toml",
    "framework/tools/loam-memory-inspect/pyproject.toml",
    "framework/tools/loam/pyproject.toml",
    "framework/tools/subloam-driver/pyproject.toml",
    "framework/tools/upgrade-merge-resolver/pyproject.toml",
    "framework/usage-window-guard/pyproject.toml",
    "framework/workspace-bootstrap/pyproject.toml",
    "framework/workspace-sync/pyproject.toml",
    "plugins/dev-sdlc/odd-extractor/pyproject.toml",
    "plugins/dev-sdlc/pr-safety/pyproject.toml",
    "plugins/dev-sdlc/pyproject.toml",
    "plugins/dev-sdlc/tools/loam-amend/pyproject.toml",
    "plugins/dev-sdlc/tools/loam-mode/pyproject.toml",
    "plugins/loam-skills/pyproject.toml",
    # v1.13.0 operational-backplane fold-in (five new components +
    # adversarial-review) — see the cut note above IN_SCOPE_PYPROJECTS.
    "framework/file-lease-registry/pyproject.toml",
    "framework/fleet-collector/pyproject.toml",
    "framework/fleet-page/pyproject.toml",
    "framework/weekly-cap-alert/pyproject.toml",
    "framework/weekly-cost-rollup/pyproject.toml",
    "framework/adversarial-review/pyproject.toml",
)

# Excluded pyprojects — measurement / experimental harnesses with
# deliberate ``version = "0.0.0"`` semantics. Documented in
# ``docs/release-versioning-policy.md`` ("Per-component pyproject
# version anchor" section). Out of scope for the discipline; bumping
# them would falsely imply they are versioned runtime components on
# the same release cadence as e.g. primary-persona or workspace-bootstrap.
EXCLUDED_PYPROJECTS: tuple[str, ...] = (
    "framework/tools/handsoff-loop/pyproject.toml",
    "framework/tools/loam-spawn-isolation/pyproject.toml",
)


def _find_repo_root() -> Path:
    """Walk up from ``__file__`` until ``docs/ACTIVE_MINOR`` is found."""

    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        candidate = ancestor / "docs" / "ACTIVE_MINOR"
        if candidate.is_file():
            return ancestor
    msg = (
        "Repo root not found — walked from "
        f"{here} upward looking for docs/ACTIVE_MINOR."
    )
    raise FileNotFoundError(msg)


def _read_pyproject_version(pyproject_path: Path) -> str:
    """Return the ``[project].version`` string from a pyproject.toml."""

    with pyproject_path.open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["version"]


def assert_pyproject_version_lockstep(
    *,
    repo_root: Path,
    expected_version: str,
    in_scope_relpaths: tuple[str, ...],
) -> None:
    """Assert every in-scope pyproject's version equals ``expected_version``.

    Raises ``AssertionError`` with a corrective-message body naming each
    drifted file, the expected version, and the corrective command shape.
    Used by AC.PCVR.3 (real-tree assertion) and AC.PCVR.4 (fixture-tree
    mutation-detection); the helper is parameterized on ``repo_root`` so
    the AC.PCVR.4 test can invoke it against a ``tmp_path`` fixture tree.
    """

    drifted: list[tuple[str, str]] = []
    missing: list[str] = []
    for relpath in in_scope_relpaths:
        path = repo_root / relpath
        if not path.is_file():
            missing.append(relpath)
            continue
        try:
            actual = _read_pyproject_version(path)
        except (KeyError, tomllib.TOMLDecodeError) as exc:
            drifted.append((relpath, f"<unreadable: {exc}>"))
            continue
        if actual != expected_version:
            drifted.append((relpath, actual))

    if missing:
        missing_lines = "\n".join(f"  - {rel}" for rel in missing)
        msg = (
            f"In-scope pyproject(s) missing from repo at {repo_root}:\n"
            f"{missing_lines}\n"
            "Update the IN_SCOPE_PYPROJECTS allowlist in "
            "plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py "
            "if the component was retired."
        )
        raise AssertionError(msg)

    if drifted:
        header = (
            f"Pyproject version drift: {len(drifted)} file(s) out of "
            f"lockstep with docs/ACTIVE_MINOR (expected "
            f'"{expected_version}").'
        )
        body = "\n".join(
            f'  - {rel} is at "{actual}"; expected "{expected_version}". '
            f'Fix: bump the file\'s `version = "..."` line to '
            f'"{expected_version}".'
            for rel, actual in drifted
        )
        footer = (
            "Per-component-version discipline established at v0.8.0 "
            "(AC.HONEST.1) advances with MINORs only; PATCHes ride "
            "predecessor MINOR (D-NFCLEAN.4 v0.8.1 + D-SDPD v0.8.2). "
            "Anchor file: docs/ACTIVE_MINOR."
        )
        raise AssertionError(f"{header}\n{body}\n{footer}")


def test_AC_PCVR_3_pyproject_version_lockstep_against_active_minor() -> None:
    """AC.PCVR.3 — every in-scope pyproject's version matches docs/ACTIVE_MINOR."""

    repo_root = _find_repo_root()
    anchor_path = repo_root / "docs" / "ACTIVE_MINOR"
    expected_version = anchor_path.read_text().strip()

    # Sanity-check the anchor shape — must be a MINOR boundary (X.Y.0).
    assert re.match(r"^\d+\.\d+\.0$", expected_version), (
        f"docs/ACTIVE_MINOR content {expected_version!r} is not a "
        "MINOR-boundary version (expected shape X.Y.0)."
    )

    assert_pyproject_version_lockstep(
        repo_root=repo_root,
        expected_version=expected_version,
        in_scope_relpaths=IN_SCOPE_PYPROJECTS,
    )


def test_AC_PCVR_3_excluded_pyprojects_are_present_and_unbumped() -> None:
    """AC.PCVR.3 (negative) — the excluded set exists and stays at 0.0.0.

    Guards against a future MINOR sweeper accidentally including the
    measurement/experimental harnesses in the lockstep set: if their
    version drifts off ``0.0.0``, surface the discrepancy here so the
    builder can rule (either INCLUDE them now or restore the 0.0.0).
    """

    repo_root = _find_repo_root()
    for relpath in EXCLUDED_PYPROJECTS:
        path = repo_root / relpath
        assert path.is_file(), (
            f"Excluded pyproject {relpath} is missing from the repo; "
            "update EXCLUDED_PYPROJECTS in "
            "plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py "
            "if the component was retired."
        )
        actual = _read_pyproject_version(path)
        assert actual == "0.0.0", (
            f"Excluded pyproject {relpath} is at {actual!r}, expected "
            '"0.0.0" (deliberate version-unset semantics for '
            "measurement/experimental harnesses). If the component is "
            "now a shipped runtime component, move it from "
            "EXCLUDED_PYPROJECTS to IN_SCOPE_PYPROJECTS in "
            "plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py "
            "AND bump the version to match docs/ACTIVE_MINOR. See "
            "docs/release-versioning-policy.md "
            '("Per-component pyproject version anchor") for the rationale.'
        )


# --- AC.PCVR.4 — outcome-altitude mutation detection -------------------------


_MINIMAL_FIXTURE_PYPROJECT_TEMPLATE = """\
[project]
name = "pcvr-fixture-{slug}"
version = "{version}"
description = "AC.PCVR.4 fixture — never shipped; lives only in tmp_path."
requires-python = ">=3.13"
"""


def _write_fixture_tree(
    *,
    base: Path,
    relpath: str,
    version: str,
    slug: str = "alpha",
) -> Path:
    """Write a minimal fixture pyproject under ``base / relpath``."""

    target = base / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        _MINIMAL_FIXTURE_PYPROJECT_TEMPLATE.format(slug=slug, version=version)
    )
    return target


def test_AC_PCVR_4_mutation_detection_proves_assertion_fires(
    tmp_path: Path,
) -> None:
    """AC.PCVR.4 — outcome-altitude proof.

    Mutates a fixture pyproject to a deliberately-stale value; invokes the
    AC.PCVR.3 assertion helper against the fixture tree with
    ``expected_version="0.12.0"``; asserts the helper raises with the
    corrective-message shape; reverts the mutation; asserts the helper
    now passes.

    Mutation is against a fixture file under ``tmp_path`` — NEVER against
    a real component pyproject. The mutation is invisible to any other
    test or commit.

    Per ``feedback_test_outcome_altitude_required``: without this proof,
    AC.PCVR.3 could pass vacuously (empty in-scope set, broken helper,
    silently-swallowed exception). This test invokes the real assertion
    helper end-to-end against a real failure case.
    """

    fixture_relpath = "framework/pcvr-fixture-component/pyproject.toml"

    # --- Phase 1: stale fixture → helper must RAISE ---
    stale_target = _write_fixture_tree(
        base=tmp_path, relpath=fixture_relpath, version="0.10.0"
    )
    assert stale_target.is_file()

    with pytest.raises(AssertionError) as raised:
        assert_pyproject_version_lockstep(
            repo_root=tmp_path,
            expected_version="0.12.0",
            in_scope_relpaths=(fixture_relpath,),
        )

    body = str(raised.value)
    assert "Pyproject version drift" in body, (
        f"Helper raised but corrective-message header missing: {body!r}"
    )
    assert fixture_relpath in body, (
        f"Helper raised but drifted file path missing from message: {body!r}"
    )
    assert '"0.10.0"' in body, (
        f"Helper raised but stale-version not surfaced: {body!r}"
    )
    assert '"0.12.0"' in body, (
        f"Helper raised but expected-version not surfaced: {body!r}"
    )

    # --- Phase 2: revert to in-lockstep → helper must PASS ---
    _write_fixture_tree(
        base=tmp_path,
        relpath=fixture_relpath,
        version="0.12.0",
        slug="alpha",  # same slug; same name → idempotent overwrite
    )

    # No exception means the helper passes — pytest reports green.
    assert_pyproject_version_lockstep(
        repo_root=tmp_path,
        expected_version="0.12.0",
        in_scope_relpaths=(fixture_relpath,),
    )


def test_AC_PCVR_4_mutation_detection_missing_file_surfaces(
    tmp_path: Path,
) -> None:
    """AC.PCVR.4 (companion) — missing in-scope pyproject also fails.

    Guards against the silent-skip failure mode the parent defect proved:
    a pyproject named in the allowlist that doesn't exist on disk must
    surface as a failure, not be silently skipped.
    """

    fixture_relpath = "framework/pcvr-fixture-missing/pyproject.toml"

    # Do NOT write the file — assertion must raise on missing.
    with pytest.raises(AssertionError) as raised:
        assert_pyproject_version_lockstep(
            repo_root=tmp_path,
            expected_version="0.12.0",
            in_scope_relpaths=(fixture_relpath,),
        )

    assert "missing from repo" in str(raised.value), (
        "Helper must surface missing in-scope files explicitly; got: "
        f"{raised.value!r}"
    )
    assert fixture_relpath in str(raised.value)


def test_AC_PCVR_4_anchor_file_resolution_works_from_test_dir() -> None:
    """AC.PCVR.4 (helper) — repo-root resolver finds docs/ACTIVE_MINOR."""

    repo_root = _find_repo_root()
    assert (repo_root / "docs" / "ACTIVE_MINOR").is_file()
    content = (repo_root / "docs" / "ACTIVE_MINOR").read_text().strip()
    assert re.match(r"^\d+\.\d+\.0$", content), (
        f"docs/ACTIVE_MINOR content {content!r} not a MINOR-boundary version."
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation
    sys.exit(pytest.main([__file__, "-v"]))
