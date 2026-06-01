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

"""AC.UPGR.3 — plain-language, non-tech-safe surface.

After an auto-upgrade the user is told in PLAIN language what was migrated —
NO SHAs, NO cursor internals (version strings / slugs), NO AC-IDs. On a
migration FAILURE the inherited rollback fires and the user is told the state
was RESTORED, not left half-migrated (the protection-floor recoverability +
the four-step-loop surfacing).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ORCH_SCRIPTS = REPO_ROOT / "framework" / "orchestrator" / "scripts"
if str(ORCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ORCH_SCRIPTS))

from auto_upgrade import AutoUpgradeResult, render_surface  # noqa: E402


# Internal-vocabulary tokens that must NEVER reach the user-facing surface.
_FORBIDDEN_TOKENS = (
    "cursor",
    "migration",
    "slug",
    "replay",
    "envelope",
    "rollback",
    "AC.",
    "SHA",
    "commit",
    ".loam",
    "applied_version",
    "structural-only",
    "no-op",
)

# A bare version-string pattern (v0.2.0, 0.14.0) — a cursor internal.
_VERSION_RE = re.compile(r"\bv?\d+\.\d+(\.\d+)?\b")

# A 7+ hex-char run — a commit SHA leak.
_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")


def _assert_plain(text: str) -> None:
    lowered = text.lower()
    for tok in _FORBIDDEN_TOKENS:
        assert tok.lower() not in lowered, f"internal token {tok!r} leaked into surface: {text!r}"
    assert not _VERSION_RE.search(text), f"a version string leaked into surface: {text!r}"
    assert not _SHA_RE.search(lowered), f"a SHA-like token leaked into surface: {text!r}"


def test_AC_UPGR_3_success_surface_is_plain_and_names_count() -> None:
    """A successful upgrade surface uses plain words, carries the count of
    updates, says work was preserved, and leaks no internal vocabulary."""
    res = AutoUpgradeResult(detected=True, applied=["m2", "m3"])
    surface = render_surface(res)
    assert surface is not None
    _assert_plain(surface)
    assert "2 updates" in surface
    assert "preserved" in surface.lower()


def test_AC_UPGR_3_singular_grammar_for_one_update() -> None:
    """One applied migration reads '1 update' (singular), not '1 updates'."""
    res = AutoUpgradeResult(detected=True, applied=["m2"])
    surface = render_surface(res)
    assert surface is not None
    assert "1 update " in surface and "1 updates" not in surface
    _assert_plain(surface)


def test_AC_UPGR_3_failure_surface_says_restored_not_half_migrated() -> None:
    """A rolled-back upgrade tells the user their state was put back exactly as
    it was — NOT left half-changed — in plain language."""
    res = AutoUpgradeResult(detected=True, applied=[], rolled_back=True, failure="boom")
    surface = render_surface(res)
    assert surface is not None
    _assert_plain(surface)
    low = surface.lower()
    assert "put back" in low or "restored" in low or "back exactly" in low
    assert "half" in low  # "nothing was left half-changed"


def test_AC_UPGR_3_degraded_import_failure_surfaces_as_restored() -> None:
    """A fail-soft degrade (a failure with nothing applied) surfaces the safe
    'state was put back' message — never a raw stack-trace or internal error."""
    res = AutoUpgradeResult(detected=True, applied=[], failure="replay: ImportError(...)")
    surface = render_surface(res)
    assert surface is not None
    _assert_plain(surface)
    assert "ImportError" not in surface  # no raw internal error text


def test_AC_UPGR_3_quiet_when_nothing_detected() -> None:
    """No detection → no surface (a silent session-start; the user is not
    bothered when there is nothing to report)."""
    res = AutoUpgradeResult(detected=False)
    assert render_surface(res) is None
