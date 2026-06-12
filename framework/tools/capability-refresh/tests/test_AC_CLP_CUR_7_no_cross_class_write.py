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

"""AC.CLP-CUR.7 — the refresh never writes outside Class A / A-prime
paths; ``best-practice/`` (Class B) is untouched by any refresh run,
including a run whose upstream fixture / source manifest tries to
induce it (the locked no-cross-class-write invariant)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from capability_refresh.corpus import CrossClassWriteError, resolve_entry_path
from capability_refresh.refresh import run_refresh
from tests.conftest import UPSTREAM_V2


def _tree_digest(root: Path) -> dict:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_AC_CLP_CUR_7_class_b_untouched_by_normal_run(fixture_repo):
    """Path-audit: a full refresh run (including a delta cycle) leaves
    Class B byte-identical."""
    before = _tree_digest(fixture_repo["corpus"] / "best-practice")
    run_refresh(fixture_repo["sources"])
    fixture_repo["upstream"].write_text(UPSTREAM_V2, encoding="utf-8")
    run_refresh(fixture_repo["sources"])
    after = _tree_digest(fixture_repo["corpus"] / "best-practice")
    assert before == after, "Class B content changed during a refresh run"


def test_AC_CLP_CUR_7_adversarial_class_b_source_refused(fixture_repo):
    """A source manifest naming a Class B entry as a projection target is
    REFUSED — the write never happens."""
    before = _tree_digest(fixture_repo["corpus"] / "best-practice")
    fixture_repo["sources"].write_text(
        "schema_version: 1\n"
        "sources:\n"
        "  - id: hostile\n"
        "    kind: entry\n"
        "    entry: best-practice/widget-pattern.md\n"
        f"    url: file://{fixture_repo['upstream']}\n"
        "    cadence: high-velocity\n",
        encoding="utf-8",
    )
    report = run_refresh(fixture_repo["sources"])
    rec = report["sources"][0]
    assert rec["status"] == "refused-cross-class-write", rec
    assert _tree_digest(fixture_repo["corpus"] / "best-practice") == before
    # and the refusal is loud at the production CLI (exit code 3) —
    # covered structurally: cli.main returns 3 on any refusal record.


@pytest.mark.parametrize("hostile_entry", [
    "best-practice/widget-pattern.md",
    "../outside.md",
    "../../CLAUDE.md",
    "/etc/hosts",
    "unknown-class/thing.md",
])
def test_AC_CLP_CUR_7_resolve_entry_path_guards(fixture_repo, hostile_entry):
    with pytest.raises(CrossClassWriteError):
        resolve_entry_path(fixture_repo["corpus"], hostile_entry)


def test_AC_CLP_CUR_7_class_a_paths_resolve(fixture_repo):
    p = resolve_entry_path(fixture_repo["corpus"], "claude-code/widget.md")
    assert p == fixture_repo["entry"].resolve()
    # A-prime is equally in-class
    (fixture_repo["corpus"] / "harness").mkdir(exist_ok=True)
    resolve_entry_path(fixture_repo["corpus"], "harness/anything.md")
