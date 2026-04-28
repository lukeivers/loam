"""AC.α.4 — ≥ 3 seed Class B docs covering owner-articulated patterns.

Per plan §4 AC.α.4, at least three files exist under
``docs/rebuild/capability-corpus/best-practice/``, each satisfying
the Class B schema from AC.α.2:

  - Pattern
  - Conditions
  - Failure modes
  - Cross-references  (≥ 1 [primitive: <class>:<name>] entry)
  - Trust marker  (with sources_count integer ≥ 1, validation_count
    integer ≥ 0, supersession_chain string, owner_acked boolean)
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CLASS_B_DIR = (
    REPO_ROOT
    / "docs" / "rebuild" / "capability-corpus" / "best-practice"
)


def _class_b_docs() -> list[Path]:
    return sorted(CLASS_B_DIR.glob("*.md")) if CLASS_B_DIR.is_dir() else []


def test_AC_alpha_4_class_b_seed_count_at_least_three():
    docs = _class_b_docs()
    assert len(docs) >= 3, (
        f"AC.α.4 requires ≥ 3 seed Class B docs under "
        f"best-practice/; found {len(docs)}: "
        f"{[d.name for d in docs]}"
    )


def test_AC_alpha_4_each_class_b_doc_has_required_sections():
    """Every Class B doc carries the named structural sections."""
    docs = _class_b_docs()
    required_markers = (
        "## Pattern",
        "## Conditions",
        "## Failure modes",
        "## Cross-references",
        "## Trust marker",
    )
    for doc in docs:
        body = doc.read_text()
        for marker in required_markers:
            assert marker in body, (
                f"{doc.name}: Class B schema marker {marker!r} missing"
            )


def test_AC_alpha_4_each_class_b_doc_has_at_least_one_primitive_xref():
    """Each Cross-references section carries ≥ 1
    ``[primitive: <class>:<name>]`` entry."""
    pattern = re.compile(r"\[primitive:\s*[\w-]+:[\w-]+\]")
    docs = _class_b_docs()
    for doc in docs:
        body = doc.read_text()
        matches = pattern.findall(body)
        assert len(matches) >= 1, (
            f"{doc.name}: Cross-references must include ≥ 1 "
            f"[primitive: <class>:<name>] entry"
        )


def test_AC_alpha_4_each_class_b_doc_has_populated_trust_marker():
    """Each Trust marker block carries the four required fields with
    populated values matching their schema types."""
    docs = _class_b_docs()
    for doc in docs:
        body = doc.read_text()
        idx = body.index("## Trust marker")
        # Read until next ## heading or EOF.
        next_idx = body.find("\n## ", idx + 5)
        if next_idx < 0:
            next_idx = len(body)
        tm = body[idx:next_idx]
        # sources_count must be an integer ≥ 1.
        sc = re.search(r"sources_count:\s*(\d+)", tm)
        assert sc is not None, (
            f"{doc.name}: sources_count field missing from Trust marker"
        )
        assert int(sc.group(1)) >= 1, (
            f"{doc.name}: sources_count must be ≥ 1 (was {sc.group(1)})"
        )
        # validation_count must be an integer ≥ 0.
        vc = re.search(r"validation_count:\s*(\d+)", tm)
        assert vc is not None, (
            f"{doc.name}: validation_count field missing from Trust marker"
        )
        assert int(vc.group(1)) >= 0, (
            f"{doc.name}: validation_count must be ≥ 0"
        )
        # supersession_chain must be present (string, may be empty).
        assert re.search(
            r"supersession_chain:\s*\S?", tm
        ), f"{doc.name}: supersession_chain field missing from Trust marker"
        # owner_acked must be a boolean (true / false).
        oa = re.search(
            r"owner_acked:\s*(true|false)", tm, flags=re.IGNORECASE
        )
        assert oa is not None, (
            f"{doc.name}: owner_acked must be true/false"
        )
