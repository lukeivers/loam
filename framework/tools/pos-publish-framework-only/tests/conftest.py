"""Shared test fixtures for pos-publish-framework-only.

Per amendment #83 — M2 (publish-mode partition manifest +
synthesis tool extension): ``make_fixture_canonical`` writes a
fixture publish-mode-manifest.yaml into the fixture canonical at
the canonical path
``framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``.
The fixture manifest classifies the fixture's known path set into
``dev_and_public`` (default) so the synthesis-pipeline tests
(``test_AC_SFR_2_synthesis_pipeline.py``) continue passing without
test-side changes — they call ``synthesise_framework_only(canonical)``
and the fixture canonical's manifest covers every fixture path.

Tests that exercise dev_only / excluded_from_publish behaviour
build their own bespoke fixture manifest (see
``test_AC_OSS_3_synthesis_drops_dev_only.py``).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from typing import Callable

import pytest


# Default fixture manifest classifying the fixture's known path set
# (every framework/ entry → dev_and_public; every top-level doc →
# dev_and_public; every transient state → excluded_from_publish).
# Tests that need a different shape pass a custom ``manifest_yaml``
# argument to ``make_fixture_canonical`` (see signature below).
DEFAULT_FIXTURE_MANIFEST_YAML = textwrap.dedent(
    """\
    schema_version: 1
    audit_roots:
      - framework/
      - docs/
      - CLAUDE.md
      - CLAUDE.dev.md
      - README.md
    audit_excludes:
      - "**/.git/**"
    public_only: []
    dev_and_public:
      - glob: "framework/**"
      - path: CLAUDE.md
      - path: CLAUDE.dev.md
      - path: README.md
      - glob: "docs/**"
    dev_only: []
    excluded_from_publish: []
    """
)

FIXTURE_MANIFEST_REL = (
    "framework/tools/pos-publish-framework-only/"
    "publish-mode-manifest.yaml"
)


def _git(args: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {cwd!s}: "
            f"{(completed.stderr or '').strip()!r}"
        )
    return completed.stdout.rstrip("\n")


def _make_fixture_canonical(
    root: Path,
    *,
    files: dict[str, str] | None = None,
    branch: str = "pos-v2",
    manifest_yaml: str | None = None,
) -> Path:
    """Construct a fixture canonical with framework/ + top-level docs.

    Per amendment #83, also writes a fixture publish-mode-manifest.yaml
    into the fixture canonical at the canonical path. Tests that
    exercise dev_only / excluded behaviour pass a custom
    ``manifest_yaml`` covering the fixture's path set.

    ``manifest_yaml=None`` (the default) installs
    ``DEFAULT_FIXTURE_MANIFEST_YAML`` which classifies every framework
    leaf + every top-level doc as ``dev_and_public`` (no dev_only /
    excluded behaviour). This keeps the existing AC.SFR.2 tests green.

    ``manifest_yaml=""`` (explicit empty string) installs NO manifest;
    callers that want to test the "manifest missing" error path use
    this and pass an explicit manifest_path to
    ``synthesise_framework_only`` pointing somewhere else.
    """
    if files is None:
        files = {
            "framework/cost-governance/__init__.py": (
                '"""fixture cost-governance"""\n'
            ),
            "framework/workspace-bootstrap/src/__init__.py": (
                '"""fixture workspace-bootstrap"""\n'
            ),
            "framework/tools/loam-mode/__init__.py": (
                '"""fixture loam-mode"""\n'
            ),
            "CLAUDE.md": "# fixture CLAUDE.md\n",
            "CLAUDE.dev.md": "# fixture CLAUDE.dev.md\n",
            "README.md": "# fixture README.md\n",
            "docs/odd-methodology.md": "# fixture odd-methodology\n",
            "docs/rebuild/STATE.md": "# fixture STATE.md\n",
        }
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", f"--initial-branch={branch}"], cwd=root)
    _git(["config", "user.email", "fixture@local"], cwd=root)
    _git(["config", "user.name", "fixture"], cwd=root)
    # Install the fixture manifest first (callers may pass custom YAML
    # or ``""`` to skip).
    if manifest_yaml is None:
        manifest_yaml = DEFAULT_FIXTURE_MANIFEST_YAML
    if manifest_yaml:
        manifest_target = root / FIXTURE_MANIFEST_REL
        manifest_target.parent.mkdir(parents=True, exist_ok=True)
        manifest_target.write_text(manifest_yaml)
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    _git(["add", "-A"], cwd=root)
    _git(["commit", "-m", "fixture canonical initial commit"], cwd=root)
    return root


def _fixture_manifest_path(canonical: Path) -> Path:
    """Return the canonical-relative path to the fixture manifest."""
    return canonical / FIXTURE_MANIFEST_REL


@pytest.fixture
def make_fixture_canonical() -> Callable[..., Path]:
    return _make_fixture_canonical


@pytest.fixture
def fixture_manifest_path() -> Callable[[Path], Path]:
    """Helper: return the fixture manifest path under a canonical."""
    return _fixture_manifest_path


@pytest.fixture
def git_run() -> Callable[..., str]:
    return _git
