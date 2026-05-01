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

"""B22 — no imports from current-gen Ruby pOS rules-file machinery.

Scan workspace-bootstrap sources for forbidden imports: Ruby-style
paths, references to `.claude/rules`, `ops/orchestrator` (the v1
pOS), etc. Any match is a halt-signal — the rebuild is greenfield.
"""

from __future__ import annotations

from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent / "src"


FORBIDDEN_FRAGMENTS = (
    "ops/orchestrator",
    ".claude/rules",
    "ops/events/event_log",
    "ops/tools/task-monitor",
    "ivers-corp/",  # current-gen pOS paths
    # Ruby-specific imports — greenfield Python should never need
    # `require 'foo'` patterns or `lib/` paths from the v1 harness.
    "require '",
    "require \"",
    "ops/orchestrator/lib",
)


def test_B22_no_legacy_fragments() -> None:
    offending: list[tuple[Path, str]] = []
    for py_file in SRC_ROOT.rglob("*.py"):
        contents = py_file.read_text()
        for frag in FORBIDDEN_FRAGMENTS:
            if frag in contents:
                offending.append((py_file, frag))
    assert offending == [], (
        f"legacy/Ruby-pOS fragments found: {offending}"
    )


def test_B22_no_legacy_package_imports() -> None:
    """No import lines reference v1 module names."""
    forbidden_modules = (
        "ops_orchestrator",  # from v1 Ruby/Python mix
        "pos_v1",
    )
    offending: list[tuple[Path, str]] = []
    for py_file in SRC_ROOT.rglob("*.py"):
        contents = py_file.read_text()
        for mod in forbidden_modules:
            if f"import {mod}" in contents or f"from {mod} " in contents:
                offending.append((py_file, mod))
    assert offending == []
