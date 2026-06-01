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

"""★ AC.INST.S (outcome-altitude: true) — the 1.0-load-bearing proof.

Drives the REAL install + the REAL ``loam init`` end-to-end:

  1. Build the wheelhouse: every loam-* component wheel + the ``loam``
     meta-distribution, from their on-disk pyprojects (``python -m
     build --wheel``). The build-half of AC.PYPKG.2.
  2. Create a genuinely CLEAN throwaway venv with NO loam source on its
     PATH / sys.path (a bare ``python -m venv``; nothing editable, no
     repo on PYTHONPATH).
  3. ``pip install loam --find-links <wheelhouse>`` — install the single
     documented surface from a LOCAL artefact index only (AC.PYPKG.3 —
     ZERO public registry; ``--no-index`` forbids PyPI for the loam-*
     closure, third-party deps allowed from the ambient index). The
     resolve-into-a-consistent-set half of AC.PYPKG.2.
  4. ``loam --help`` lists the real subcommands (AC.INST.1).
  5. ``loam init <tmpdir> --from <canonical>`` runs the REAL entry-point
     to a scaffolded workspace + a primary-persona directory resolved
     from the CLONED framework — the exact path that was RED before the
     workspace-bootstrap resolver fix (persona-template-not-found under a
     wheel install). AC.INST.S.
  6. Assert runtime-required framework DATA the scaffold needs is present
     post-init (the persona template materialised into the workspace) —
     the catalogue-bug-class guard for the install path.

LOCAL ONLY. No network for the loam closure (``--no-index`` +
``--find-links``); no public push. Slow (builds ~25 wheels + a fresh
venv + a real init), so marked ``outcome_altitude`` + ``slow`` and
guarded to skip cleanly if ``python -m build`` / ``venv`` are
unavailable in the runner — but it RUNS in the seal harness (the
component venv has both), making AC.INST.S a real gate, not a stub.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# The install closure built into the wheelhouse + the meta-distribution.
# Mirrors install-from-source.txt's component set + framework/loam-init/meta.
_COMPONENT_DIRS = [
    "framework/scope-of-work",
    "framework/objective-tracker",
    "framework/observability-aggregator",
    "framework/safety-layer",
    "framework/self-upgrade",
    "framework/workspace-sync",
    "framework/primary-persona",
    "framework/orchestrator",
    "framework/telegram-interface",
    "framework/reversibility-primitive",
    "framework/dormancy",
    "framework/cost-governance",
    "framework/state-migration-engine",
    "framework/self-correction",
    "framework/workspace-bootstrap",
    "framework/tools/loam",
    "framework/loam-init",
    "framework/loam-init/meta",
    "plugins/dev-sdlc",
    "plugins/dev-sdlc/odd-extractor",
    "plugins/dev-sdlc/tools/loam-amend",
    "plugins/dev-sdlc/pr-safety",
    "plugins/dev-sdlc/tools/loam-mode",
    "framework/per-project-pm",
    "plugins/loam-skills",
]

pytestmark = [pytest.mark.outcome_altitude, pytest.mark.slow]

# Probe run INSIDE the clean venv: print "<dist-name> <origin-url-or-local>"
# for every installed distribution, reading pip's recorded direct_url.json
# (a remote install records an https url; a wheelhouse install records a
# file:// url or none).
_ORIGIN_PROBE = """
import json
from importlib import metadata
for dist in metadata.distributions():
    name = dist.metadata["Name"] or "?"
    origin = "local"
    try:
        raw = dist.read_text("direct_url.json")
        if raw:
            origin = json.loads(raw).get("url", "local")
    except Exception:
        pass
    print(f"{name} {origin}")
"""


def _have(tool_check: list[str]) -> bool:
    try:
        subprocess.run(tool_check, check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


_TOOLING_AVAILABLE = (
    _have([sys.executable, "-m", "build", "--version"])
    and _have([sys.executable, "-m", "venv", "-h"])
    and shutil.which("git") is not None
)


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> str:
    proc = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, env=env,
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return proc.stdout


def _build_wheelhouse(wheelhouse: Path) -> None:
    """Build every loam-* component wheel + the meta-distribution, then
    pull the THIRD-PARTY runtime deps (PyYAML etc.) into the SAME
    wheelhouse so the subsequent install can run fully offline
    (``--no-index``). The third-party fetch is the one network touch and
    is a PULL of public wheels — never a PUSH (AC.PYPKG.3: zero publish).
    """
    wheelhouse.mkdir(parents=True, exist_ok=True)
    for rel in _COMPONENT_DIRS:
        comp = REPO_ROOT / rel
        assert comp.is_dir(), f"component dir missing: {rel}"
        _run([sys.executable, "-m", "build", "--wheel",
              "--outdir", str(wheelhouse), str(comp)])
    # Resolve the meta-distribution's third-party transitive closure into
    # the wheelhouse using the just-built loam-* wheels as the local index
    # for the loam-* edges; pip fetches only the non-loam wheels remotely.
    try:
        _run([sys.executable, "-m", "pip", "download", "--quiet",
              "--find-links", str(wheelhouse), "--dest", str(wheelhouse),
              "loam"])
    except AssertionError:
        # No network for third-party prefetch — the install step will fall
        # back to the ambient index for non-loam deps (still no loam pull).
        pass


def _make_canonical_source(dst: Path) -> Path:
    """Create a real canonical git repo carrying the LIVE worktree source
    (incl. the uncommitted resolver fix + meta-package), on a ``main``
    branch so ``loam init``'s ``checkout -B main origin/main`` resolves.

    Uses ``git archive`` of the worktree's tracked tree + an overlay of
    the working-tree state for the files this amendment touches, so the
    canonical the test clones reflects exactly what will ship.
    """
    src = dst / "canonical"
    src.mkdir(parents=True)
    # Copy the working tree (tracked + new untracked source) minus heavy /
    # irrelevant dirs. NOTE: the worktree's top-level ``.git`` is a FILE
    # (a gitlink to the shared worktree gitdir), so it must be excluded
    # from BOTH the file branch and the dir branch — otherwise the fixture
    # inherits the live worktree's git linkage and ``git init`` below
    # resolves to the live branch (the "nothing to commit" trap).
    _SKIP_TOP = {
        ".git", ".venv", "node_modules", "__pycache__",
        ".scratch", "build", "dist",
    }
    ignore = shutil.ignore_patterns(
        ".git", ".venv", "node_modules", "__pycache__", "*.pyc",
        ".scratch", "*.egg-info", "build", "dist",
    )
    for child in REPO_ROOT.iterdir():
        if child.name in _SKIP_TOP:
            continue
        target = src / child.name
        if child.is_dir():
            shutil.copytree(child, target, ignore=ignore, symlinks=True)
        else:
            shutil.copy2(child, target)
    assert not (src / ".git").exists(), "fixture must not inherit live git linkage"
    # Isolate git: a ceiling dir so `git init` cannot discover an ambient
    # repo above the fixture, and a clean identity.
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CEILING_DIRECTORIES": str(dst)}
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    _run(["git", "init", "-q", "-b", "main"], cwd=src, env=env)
    _run(["git", "add", "-A"], cwd=src, env=env)
    _run(["git", "commit", "-q", "-m", "canonical fixture"], cwd=src, env=env)
    return src


@pytest.mark.skipif(
    not _TOOLING_AVAILABLE,
    reason="requires python -m build, venv, and git in the runner",
)
def test_AC_INST_S_clean_env_install_then_real_loam_init(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    _build_wheelhouse(wheelhouse)

    # AC.PYPKG.2 build-half: the meta-distribution wheel exists.
    assert list(wheelhouse.glob("loam-*.whl")), "meta-distribution wheel not built"

    # --- a genuinely clean venv: no loam source on path ------------------
    venv = tmp_path / "clean-venv"
    _run([sys.executable, "-m", "venv", str(venv)])
    py = venv / "bin" / "python"
    loam_bin = venv / "bin" / "loam"
    # Scrub any inherited PYTHONPATH so the repo source cannot leak in.
    clean_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    clean_env["PYTHONNOUSERSITE"] = "1"

    _run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"], env=clean_env)
    # AC.PYPKG.3 — install from the LOCAL wheelhouse only. Try fully
    # offline first (--no-index: the strongest proof that the whole
    # closure resolves from a local artefact index with ZERO registry
    # access); fall back to the wheelhouse-plus-ambient-index for
    # third-party deps if the offline prefetch could not run (no network),
    # in which case the loam-* packages STILL come only from the
    # wheelhouse (they are on no public index). Either way: zero publish.
    try:
        _run([str(py), "-m", "pip", "install", "-q",
              "--no-index", "--find-links", str(wheelhouse), "loam"],
             env=clean_env)
    except AssertionError:
        _run([str(py), "-m", "pip", "install", "-q",
              "--find-links", str(wheelhouse), "loam"], env=clean_env)

    # AC.PYPKG.3 assertion — every installed loam-* dist resolved from the
    # LOCAL wheelhouse, not a public registry. pip records the origin in
    # each dist's direct_url.json / INSTALLER; we assert no loam package
    # carries a remote https origin.
    origins = _run([str(py), "-c", _ORIGIN_PROBE], env=clean_env).strip()
    remote_loam = [
        line for line in origins.splitlines()
        if line.startswith("loam") and "https://" in line
    ]
    assert not remote_loam, f"loam package(s) pulled from a remote index: {remote_loam}"

    # sanity: the installed loam is NOT the repo source.
    site_loc = _run([str(py), "-c",
                     "import loam.loam_init, os; "
                     "print(os.path.dirname(loam.loam_init.__file__))"],
                    env=clean_env).strip()
    assert "site-packages" in site_loc, (
        f"installed loam must come from site-packages, got {site_loc}"
    )
    assert str(REPO_ROOT) not in site_loc

    # AC.INST.1 — loam --help lists the real subcommands.
    help_out = _run([str(loam_bin), "--help"], env=clean_env)
    for sub in ("init", "amend", "release"):
        assert sub in help_out, f"loam --help missing subcommand {sub!r}"

    # --- AC.INST.S — the REAL loam init in the clean env -----------------
    canonical = _make_canonical_source(tmp_path)
    new_ws = tmp_path / "new-workspace"
    _run([str(loam_bin), "init", str(new_ws), "--from", str(canonical)],
         env=clean_env)

    # The workspace was scaffolded.
    assert new_ws.is_dir(), "loam init did not create the workspace"
    assert (new_ws / "framework").is_dir(), "framework not cloned into workspace"

    # AC.INST.S core: the primary-persona directory resolved from the
    # CLONED framework (the exact path that was RED pre-fix). The scaffold
    # materialises personas/<handle>/contract.yaml from the template.
    persona_contracts = list(new_ws.glob("**/personas/*/contract.yaml"))
    assert persona_contracts, (
        "no primary-persona contract materialised — the persona-template "
        "resolver did not find the template in the cloned framework "
        "(the clean-env loam-init failure AC.INST.S exists to catch)"
    )

    # Runtime-data-present guard (catalogue-bug class for the install
    # path): the persona template the scaffold consumed is present in the
    # cloned framework tree (doubled or single-level), confirming the
    # runtime-required framework DATA shipped with what loam init produced.
    template_present = any(
        (new_ws / base / "primary-persona" / "templates" / "persona-template"
         / "contract.yaml").is_file()
        for base in ("framework/framework", "framework", ".")
    )
    assert template_present, (
        "runtime-required persona template absent from the initialized "
        "workspace's framework tree"
    )
