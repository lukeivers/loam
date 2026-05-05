# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.13 — Install docs at quality-bar feel-intentional level.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.13: extends
``docs/getting-started.md`` + authors NEW
``docs/dev-mode-getting-started.md``; required headings + minimum
length + link sanity.
"""

from __future__ import annotations

import re
from pathlib import Path


# Test runs from the workspace-bootstrap component dir (cwd-aware
# pytest); compute the canonical pos-v2 root from this file's location.
COMPONENT_ROOT = Path(__file__).parent.parent  # framework/workspace-bootstrap/
REPO_ROOT = COMPONENT_ROOT.parent.parent  # canonical repo root


GETTING_STARTED = REPO_ROOT / "docs" / "getting-started.md"
DEV_MODE_GETTING_STARTED = REPO_ROOT / "docs" / "dev-mode-getting-started.md"


def test_getting_started_exists() -> None:
    assert GETTING_STARTED.exists(), f"{GETTING_STARTED!s} must exist"


def test_dev_mode_getting_started_exists() -> None:
    """NEW file authored by Cycle 1 per Halt #1 resolution."""
    assert DEV_MODE_GETTING_STARTED.exists(), (
        f"{DEV_MODE_GETTING_STARTED!s} must exist (Halt #1 resolution)"
    )


def test_getting_started_has_onboarding_walkthrough_section() -> None:
    """Cycle 1 extends getting-started with a six-question walkthrough."""
    text = GETTING_STARTED.read_text(encoding="utf-8")
    # Substring match on heading or section text the walkthrough adds.
    assert (
        "onboarding" in text.lower() or "loam onboard" in text
    ), "getting-started.md must reference the onboarding walkthrough"


def test_dev_mode_getting_started_minimum_length() -> None:
    """Plan-doc §6.1: minimum 80 lines per Halt #1 resolution."""
    line_count = len(
        DEV_MODE_GETTING_STARTED.read_text(encoding="utf-8").splitlines()
    )
    assert line_count >= 80, f"dev-mode getting-started has {line_count} lines (need ≥80)"


def test_getting_started_minimum_length() -> None:
    """getting-started.md is at least 150 lines (existing 211 + walkthrough additions)."""
    line_count = len(GETTING_STARTED.read_text(encoding="utf-8").splitlines())
    assert line_count >= 150, f"getting-started has {line_count} lines (need ≥150)"


def test_dev_mode_required_headings() -> None:
    """The dev-mode doc covers prerequisites + enable + walkthrough."""
    text = DEV_MODE_GETTING_STARTED.read_text(encoding="utf-8").lower()
    for heading_substr in ("dev-mode", "prerequisites", "walkthrough"):
        assert heading_substr in text, f"missing required heading: {heading_substr}"


def test_install_docs_no_broken_relative_links() -> None:
    """Markdown relative links to other docs files resolve."""
    for doc in (GETTING_STARTED, DEV_MODE_GETTING_STARTED):
        text = doc.read_text(encoding="utf-8")
        # Match [text](relative.md) or [text](relative.md#anchor)
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]*)?\)")
        for match in link_pattern.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (doc.parent / target).resolve()
            assert resolved.exists(), (
                f"broken link in {doc.name!s}: {target!r} (resolved: {resolved!s})"
            )
