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

"""AC.α.5 — Schema discipline: every seed doc satisfies its class's schema.

Per plan §4 AC.α.5, this is the cross-cutting structural check
verifying that AC.α.3 + AC.α.4 are not satisfied by minimum-viable
token content. For every file under
``docs/rebuild/capability-corpus/{claude-code,harness,best-practice}/``:

  - Determine class from parent directory.
  - Load the class schema markers from AC.α.2's authoring guide
    (Class A required markers; Class B required markers).
  - Assert every required marker is present.
  - Assert every required field is non-empty (non-whitespace).
  - Assert no field carries the literal placeholder prose from
    ``AUTHORING.md`` (the "describe X" anti-pattern from L's AC.O.6).

ODD §8.2.14 byte-content discipline: this test reads each seed
doc's actual bytes and asserts the named-section schema, not just
file existence — the cross-cutting structural check that backs the
state-mutating diff.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS_ROOT = REPO_ROOT / "docs" / "rebuild" / "capability-corpus"

CLASS_A_REQUIRED = (
    "## Surface",
    "## Inputs/outputs",
    "## Composition notes",
    "## [user-intent phrasings]",
    "## Source",
)
CLASS_B_REQUIRED = (
    "## Pattern",
    "## Conditions",
    "## Failure modes",
    "## Cross-references",
    "## Trust marker",
)

# Phrases lifted from the AUTHORING.md placeholder-prose patterns
# that must NOT appear verbatim in any seed doc body. These are the
# anti-patterns AC.α.5 guards against (the "describe in one
# sentence" L AC.O.6 shape).
PLACEHOLDER_FRAGMENTS = (
    "one to three sentences naming the primitive.",
    "one to three sentences naming the pattern.",
    "<deferred-to-",
)


def _all_seed_docs() -> list[tuple[str, Path]]:
    """Return [(class_label, path), ...] for every seed doc."""
    out: list[tuple[str, Path]] = []
    for sub, label in (
        ("claude-code", "A"),
        ("harness", "A-prime"),
        ("best-practice", "B"),
    ):
        d = CORPUS_ROOT / sub
        if d.is_dir():
            for p in sorted(d.glob("*.md")):
                out.append((label, p))
    return out


def test_AC_alpha_5_corpus_root_exists():
    assert CORPUS_ROOT.is_dir(), (
        f"capability-corpus root missing at {CORPUS_ROOT}"
    )


def test_AC_alpha_5_every_seed_doc_satisfies_its_class_schema():
    """Read every seed doc; check class-required markers present
    and every required field non-empty."""
    docs = _all_seed_docs()
    assert docs, "no seed docs found under capability-corpus/"
    for label, doc in docs:
        body = doc.read_text()
        if label in ("A", "A-prime"):
            required = CLASS_A_REQUIRED
        else:
            required = CLASS_B_REQUIRED
        for marker in required:
            assert marker in body, (
                f"{doc.relative_to(REPO_ROOT)} (class {label}): "
                f"required marker {marker!r} missing"
            )


def test_AC_alpha_5_no_seed_doc_carries_placeholder_prose():
    """Byte-content check: no seed doc body contains the
    AUTHORING.md placeholder-prose fragments verbatim. This is the
    structural guard against minimum-viable schema-cheat content."""
    docs = _all_seed_docs()
    for _label, doc in docs:
        body = doc.read_text()
        for placeholder in PLACEHOLDER_FRAGMENTS:
            assert placeholder not in body, (
                f"{doc.relative_to(REPO_ROOT)}: contains placeholder "
                f"prose fragment {placeholder!r} from AUTHORING.md"
            )


def test_AC_alpha_5_every_required_section_is_non_empty():
    """For each required section in each doc, assert there is at
    least one non-whitespace line of body content between the
    section heading and the next heading (or EOF)."""
    docs = _all_seed_docs()
    for label, doc in docs:
        body = doc.read_text()
        required = (
            CLASS_A_REQUIRED if label in ("A", "A-prime")
            else CLASS_B_REQUIRED
        )
        for marker in required:
            idx = body.index(marker)
            # Find the next heading at the same or higher level.
            # markers are level-2 (##); any new ## following counts
            # as the next section.
            next_idx = body.find("\n## ", idx + len(marker))
            if next_idx < 0:
                next_idx = len(body)
            section = body[idx + len(marker):next_idx]
            content_lines = [
                ln for ln in section.splitlines() if ln.strip()
            ]
            assert content_lines, (
                f"{doc.relative_to(REPO_ROOT)} (class {label}): "
                f"section {marker!r} has no body content"
            )


def test_AC_alpha_5_sample_class_a_doc_byte_content_matches_schema():
    """ODD §8.2.14 byte-content verification: read a specific
    sample Class A doc end-to-end and assert its named-section
    schema (not just marker presence). This is the byte-content
    check on a state-mutating diff target."""
    sample = CORPUS_ROOT / "claude-code" / "schedule.md"
    assert sample.is_file(), f"sample doc {sample} missing"
    body = sample.read_text()

    # Each Class A required marker present + immediately followed
    # by body content (no two markers back-to-back with empty body).
    section_bodies: dict[str, str] = {}
    for i, marker in enumerate(CLASS_A_REQUIRED):
        start = body.index(marker)
        # next marker in this doc
        if i + 1 < len(CLASS_A_REQUIRED):
            end = body.index(CLASS_A_REQUIRED[i + 1])
        else:
            end = len(body)
        section_bodies[marker] = body[start + len(marker):end]

    # The Source section carries source_url + source_fetch_ts as
    # populated fields (D-OWNER.3 (a) — non-placeholder).
    src = section_bodies["## Source"]
    url_match = re.search(r"source_url:\s*(\S.*?)(?:\n|$)", src)
    ts_match = re.search(r"source_fetch_ts:\s*(\S.*?)(?:\n|$)", src)
    assert url_match, "schedule.md Source: source_url missing"
    assert ts_match, "schedule.md Source: source_fetch_ts missing"
    assert "<deferred-to-" not in url_match.group(1), (
        "schedule.md Source: source_url is a placeholder"
    )
    assert "<deferred-to-" not in ts_match.group(1), (
        "schedule.md Source: source_fetch_ts is a placeholder"
    )

    # The [user-intent phrasings] section carries ≥ 3 bullet entries.
    phrasings = section_bodies["## [user-intent phrasings]"]
    bullets = [
        ln for ln in phrasings.splitlines() if ln.strip().startswith("- ")
    ]
    assert len(bullets) >= 3, (
        f"schedule.md [user-intent phrasings] should have ≥ 3 "
        f"bullets; found {len(bullets)}"
    )
