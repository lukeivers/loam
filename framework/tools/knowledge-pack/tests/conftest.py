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

"""Fixture corpus for the knowledge-pack render AC tests.

Mirrors the real corpus shape (AUTHORING.md): a Class A entry under
``claude-code/`` with the four required sections + a ``## Source`` block,
a Class A-prime entry under ``harness/``, and a Class B entry under
``best-practice/`` with ``## Cross-references`` + ``## Trust marker``. One
entry is marked STALE so the RENDER.5 passthrough is exercised.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


CLASS_A_BODY = """\
# `/goal` — drive-to-checkable-outcome

## Surface

The `/goal` slash command drives work to a checkable predicate.

## Inputs/outputs

Takes a goal condition; iterates until it passes, then halts.

## Composition notes

Sibling of `/loop`.

## Invocation phrasings

- "keep working until the build is green"
- "drive this to a passing acceptance"
- "don't come back until it's done"

## Source

```
source_url: https://code.claude.com/docs/en/commands
source_fetch_ts: 2026-06-14T00:00:00Z
source_status: current
```
"""

# A STALE Class A entry — exercises the RENDER.5 stale passthrough.
CLASS_A_STALE_BODY = """\
# `/loop` — recurring interval driver

## Surface

The `/loop` slash command runs a prompt on a recurring interval.

## Inputs/outputs

Takes an interval + a prompt.

## Composition notes

Sibling of `/goal`.

## Invocation phrasings

- "check the deploy every 5 minutes"
- "keep running this on a loop"
- "poll for status"

## Source

```
source_url: https://code.claude.com/docs/en/commands
source_fetch_ts: 2026-05-01T00:00:00Z
source_status: stale (fetch failed: 503; marked 2026-06-10T00:00:00Z)
```
"""

CLASS_APRIME_BODY = """\
# Scope of work — the harness work-unit

## Surface

A scope-of-work is loam's unit of fenced, accepted work.

## Inputs/outputs

Objective + constraints + acceptance.

## Composition notes

Projected by the scope-of-work component.

## Invocation phrasings

- "define the work"
- "what is the acceptance"
- "fence this work"

## Source

```
source_url: internal:framework/scope-of-work/docs/contract.md
source_fetch_ts: 2026-06-14T00:00:00Z
source_status: current
```
"""

CLASS_B_BODY = """\
# Scope-only dispatch

## Pattern

Dispatch prompts carry scope, not method.

## Conditions

When dispatching a build agent with a plan-before-code obligation.

## Failure modes

Plan-as-paperwork; loss of the agent's own design judgement.

## Cross-references

[primitive: claude-code:goal]

## Trust marker

```
sources_count: 1
validation_count: 5
supersession_chain: ""
owner_acked: true
```
"""


@pytest.fixture
def fixture_corpus(tmp_path):
    """A minimal corpus: one Class A (current), one Class A (stale), one
    Class A-prime, one Class B entry — the real directory layout."""
    corpus = tmp_path / "docs" / "capability-corpus"
    (corpus / "claude-code").mkdir(parents=True)
    (corpus / "harness").mkdir(parents=True)
    (corpus / "best-practice").mkdir(parents=True)

    (corpus / "claude-code" / "goal.md").write_text(CLASS_A_BODY, encoding="utf-8")
    (corpus / "claude-code" / "loop.md").write_text(CLASS_A_STALE_BODY, encoding="utf-8")
    (corpus / "harness" / "scope-of-work.md").write_text(CLASS_APRIME_BODY, encoding="utf-8")
    (corpus / "best-practice" / "scope-only-dispatch.md").write_text(CLASS_B_BODY, encoding="utf-8")

    # State dirs that must be IGNORED by the loader.
    (corpus / ".refresh").mkdir()
    (corpus / ".refresh" / "last-run.json").write_text("{}", encoding="utf-8")
    (corpus / "AUTHORING.md").write_text("# Authoring\n", encoding="utf-8")

    return {
        "corpus_root": corpus,
        "repo_root": tmp_path,
    }
