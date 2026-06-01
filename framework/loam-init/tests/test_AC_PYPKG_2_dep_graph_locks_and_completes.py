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

"""AC.PYPKG.2 — the inter-component dependency graph LOCKS + is complete.

Two halves, both verifiable from the static tree (no network):

  (a) Every inter-component ``loam-*`` dependency declared by any
      component resolves to a real on-disk package — the graph has no
      dangling edges (a dangling edge would be an unresolvable install).

  (b) Every on-disk component that is a RUNTIME dependency of the install
      closure is present in ``install-from-source.txt`` — closing the
      install-graph hole the prior EXAMINE pass found
      (``loam-state-migration-engine`` was missing; self-correction →
      state-migration-engine, self-correction pulled by
      workspace-bootstrap). A stranger following install-from-source.txt
      must install the whole runtime closure.

The buildable-wheel half (every component's ``python -m build --wheel``
succeeds) + the resolve-into-a-consistent-set half are proven by the
clean-env outcome-altitude test
(``test_AC_INST_S_clean_env_install_and_init.py``), which builds the real
wheelhouse and installs the closure with pip's resolver; this file pins
the static graph-completeness invariants that the build proves at
runtime.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_components() -> tuple[dict[str, Path], dict[str, set[str]]]:
    """Return ({pkg_name: dir}, {pkg_name: {loam_dep, ...}}) over every
    pyproject under framework/ and plugins/."""
    pkg_to_dir: dict[str, Path] = {}
    pkg_deps: dict[str, set[str]] = {}
    for pat in ("framework/**/pyproject.toml", "plugins/**/pyproject.toml"):
        for p in REPO_ROOT.glob(pat):
            with p.open("rb") as f:
                data = tomllib.load(f)
            name = data.get("project", {}).get("name")
            if not name:
                continue
            pkg_to_dir[name] = p.parent
            loam_deps = set()
            for dep in data.get("project", {}).get("dependencies", []):
                m = re.match(r"^(loam-[a-z0-9-]+)", dep.strip())
                if m:
                    loam_deps.add(m.group(1))
            pkg_deps[name] = loam_deps
    return pkg_to_dir, pkg_deps


def test_no_dangling_inter_component_edges() -> None:
    """AC.PYPKG.2(a) — every ``loam-*`` dep resolves to a real on-disk
    package. The meta-distribution ``loam`` is excluded as a target (it is
    the surface, not a component dependency of any component)."""
    pkg_to_dir, pkg_deps = _load_components()
    known = set(pkg_to_dir)
    dangling: dict[str, set[str]] = {}
    for name, deps in pkg_deps.items():
        missing = {d for d in deps if d not in known and d != "loam"}
        if missing:
            dangling[name] = missing
    assert not dangling, f"dangling inter-component dep edges: {dangling}"


def test_state_migration_engine_in_install_from_source() -> None:
    """AC.PYPKG.2(b) — the specific install-graph hole the prior pass
    found is CLOSED: loam-state-migration-engine is listed in
    install-from-source.txt."""
    ifs = (REPO_ROOT / "install-from-source.txt").read_text()
    listed = set(re.findall(r"-e \./([^\s]+)", ifs))
    assert "framework/state-migration-engine" in listed, (
        "loam-state-migration-engine (a runtime dep of the closure via "
        "self-correction) must be listed in install-from-source.txt"
    )


def test_install_from_source_covers_self_correction_runtime_closure() -> None:
    """AC.PYPKG.2(b) — every loam-* package reachable as a RUNTIME dep
    from the documented CLI roots is present in install-from-source.txt.
    This is the general form of the state-migration-engine fix: no
    runtime closure member is missing from the documented install path.
    """
    pkg_to_dir, pkg_deps = _load_components()
    ifs = (REPO_ROOT / "install-from-source.txt").read_text()
    listed_dirs = set(re.findall(r"-e \./([^\s]+)", ifs))

    # Roots = the documented CLI verbs / console-script the install path
    # exists to deliver.
    roots = [
        "loam-cli", "loam-init", "loam-amend", "loam-pr-safety", "loam-mode",
        "loam-plugin-dev-sdlc", "loam-odd-extractor", "loam-per-project-pm",
        "loam-plugin-loam-skills", "loam-workspace-sync", "loam-self-upgrade",
    ]
    seen: set[str] = set()
    stack = [r for r in roots if r in pkg_to_dir]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for d in pkg_deps.get(n, ()):
            if d in pkg_to_dir and d not in seen:
                stack.append(d)

    missing_from_ifs = sorted(
        n for n in seen
        if str(pkg_to_dir[n].relative_to(REPO_ROOT)) not in listed_dirs
    )
    assert not missing_from_ifs, (
        "runtime-closure packages missing from install-from-source.txt: "
        f"{missing_from_ifs}"
    )
