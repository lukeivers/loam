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

"""Fixture corpus + fixture upstreams for the capability-refresh AC tests.

The fixture mirrors the real corpus shape (AUTHORING.md): a Class A
entry under ``claude-code/`` with the four required sections + Source
block, a Class B entry under ``best-practice/`` (the no-cross-class-write
target), and a ``sources.yaml`` manifest pointing at file:// upstreams.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# Upstream v1 — the statements the entry body projects.
UPSTREAM_V1 = """\
The widget tool accepts three inputs and returns one output.
The widget tool runs locally with no network access.
The widget tool keeps a log of every invocation.
The widget tool is licensed for workspace use.
"""

# Upstream v2 — one same-statement update (three -> four inputs: high-sim
# replace -> AUTO-LAND), one removal (the log statement: delete -> REVIEW),
# one new claim (SSH: insert -> REVIEW).
UPSTREAM_V2 = """\
The widget tool accepts four inputs and returns one output.
The widget tool runs locally with no network access.
The widget tool is licensed for workspace use.
The widget tool now supports remote execution over SSH.
"""

ENTRY_BODY = """\
# Widget tool

## Surface

The widget tool accepts three inputs and returns one output.
The widget tool runs locally with no network access.

## Inputs/outputs

The widget tool keeps a log of every invocation.
The widget tool is licensed for workspace use.

## Composition notes

Composes with the fixture harness.

## [user-intent phrasings]

- "use the widget"
- "run the widget tool"
- "widget it"

## Source

```
source_url: internal:seed-label:2026-01-01
source_fetch_ts: 2026-01-01T00:00:00Z
```
"""

CLASS_B_BODY = """\
# Widget best practice

## Pattern

Always widget before you gadget.

## Conditions

Whenever a widget exists.

## Failure modes

Gadgeting first.

## Cross-references

[primitive: claude-code:widget]

## Trust marker

sources_count: 1
validation_count: 1
supersession_chain:
owner_acked: true
"""


@pytest.fixture
def fixture_repo(tmp_path):
    """A minimal repo: docs/capability-corpus/{claude-code,best-practice}
    + an upstream file served over file://."""
    repo = tmp_path / "repo"
    corpus = repo / "docs" / "capability-corpus"
    (corpus / "claude-code").mkdir(parents=True)
    (corpus / "best-practice").mkdir(parents=True)

    entry = corpus / "claude-code" / "widget.md"
    entry.write_text(ENTRY_BODY, encoding="utf-8")
    class_b = corpus / "best-practice" / "widget-pattern.md"
    class_b.write_text(CLASS_B_BODY, encoding="utf-8")

    upstream = tmp_path / "upstream-widget.md"
    upstream.write_text(UPSTREAM_V1, encoding="utf-8")

    sources = corpus / "sources.yaml"
    sources.write_text(
        "schema_version: 1\n"
        "sources:\n"
        "  - id: widget\n"
        "    kind: entry\n"
        "    entry: claude-code/widget.md\n"
        f"    url: file://{upstream}\n"
        "    cadence: high-velocity\n",
        encoding="utf-8",
    )
    return {
        "repo": repo,
        "corpus": corpus,
        "entry": entry,
        "class_b": class_b,
        "upstream": upstream,
        "sources": sources,
    }
