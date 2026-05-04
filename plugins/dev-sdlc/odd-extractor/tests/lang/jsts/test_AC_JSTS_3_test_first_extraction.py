"""AC.JSTS.3 — Test-first extraction
(Playwright + Jest + Mocha + Vitest → VERIFIED).

Verifies:

- Playwright tests → VERIFIED with ``evidence.kind="test"``,
  ``repo_sha`` non-null, ``citations=[<file>:<line>:playwright:...]``.
- Vitest tests → VERIFIED with runner identity in citation.
- Jest-style tests (Jest globals, no explicit import) → VERIFIED
  with ``runner="unknown"`` in citation (we don't pretend to know).
- Without ``repo_sha`` (non-git repo) → downgrade to PLAUSIBLE
  with ``evidence.kind="source"``.
- Round-trip via :meth:`BandedAC.model_validate`.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import BandedAC, ConfidenceBand
from loam_odd_extractor.lang.jsts.parser import parse_source
from loam_odd_extractor.lang.jsts.recognizers import (
    recognize_playwright_tests,
    recognize_test_runners,
)


def test_playwright_verified_with_repo_sha(
    jsts_playwright_app_repo: Path,
) -> None:
    fp = jsts_playwright_app_repo / "tests/playwright/login.spec.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef" * 5
    )
    assert len(out) == 3
    for ac in out:
        assert ac.confidence is ConfidenceBand.VERIFIED
        assert ac.evidence.kind == "test"
        assert ac.evidence.repo_sha == "deadbeef" * 5
        assert any(":playwright:" in c for c in ac.evidence.citations)
        # Citation contains describe + test name.
        assert any(
            "login flow" in c and "#" in c for c in ac.evidence.citations
        )


def test_playwright_downgrades_without_repo_sha(
    jsts_playwright_app_repo: Path,
) -> None:
    fp = jsts_playwright_app_repo / "tests/playwright/login.spec.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, fp, jsts_playwright_app_repo, None
    )
    assert len(out) == 3
    for ac in out:
        # Downgraded → PLAUSIBLE with kind=source.
        assert ac.confidence is ConfidenceBand.PLAUSIBLE
        assert ac.evidence.kind == "source"
        assert ac.evidence.repo_sha is None


def test_vitest_runner_identity(
    jsts_playwright_app_repo: Path,
) -> None:
    fp = jsts_playwright_app_repo / "tests/unit/users.test.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_test_runners(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef" * 5
    )
    assert len(out) >= 3
    for ac in out:
        assert ac.confidence is ConfidenceBand.VERIFIED
        # Citation marks runner=vitest (per Surface #6).
        assert any(":vitest:" in c for c in ac.evidence.citations)


def test_jest_style_unknown_runner_identity(
    jsts_playwright_app_repo: Path,
) -> None:
    fp = jsts_playwright_app_repo / "tests/unit/server.test.js"
    src = fp.read_bytes()
    tree = parse_source(src, "javascript")
    out = recognize_test_runners(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef" * 5
    )
    # No explicit import → recorded as unknown runner.
    assert len(out) >= 1
    for ac in out:
        # Citation marks runner=unknown.
        assert any(":unknown:" in c for c in ac.evidence.citations)


def test_test_runner_downgrades_without_repo_sha(
    jsts_playwright_app_repo: Path,
) -> None:
    fp = jsts_playwright_app_repo / "tests/unit/users.test.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_test_runners(
        tree, src, fp, jsts_playwright_app_repo, None
    )
    for ac in out:
        assert ac.confidence is ConfidenceBand.PLAUSIBLE
        assert ac.evidence.kind == "source"
        assert ac.evidence.repo_sha is None


def test_test_first_round_trip(
    jsts_playwright_app_repo: Path,
) -> None:
    """Every emitted BandedAC round-trips through model_validate."""
    fp = jsts_playwright_app_repo / "tests/playwright/login.spec.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef" * 5
    )
    for ac in out:
        # Round trip via dict.
        as_dict = ac.model_dump(mode="json")
        reconstructed = BandedAC.model_validate(as_dict)
        assert reconstructed.ac_id == ac.ac_id
        assert reconstructed.confidence == ac.confidence


def test_describe_context_captured() -> None:
    """test() inside test.describe() captures the describe text in
    the AC text + citation.
    """
    src = b"""
import { test, expect } from '@playwright/test';
test.describe('checkout flow', () => {
  test('user can pay', async ({page}) => {
    expect(page).toBeTruthy();
  });
});
"""
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, Path("tests/playwright/checkout.spec.ts"),
        Path("/"), "deadbeef" * 5,
    )
    assert len(out) == 1
    assert "checkout flow" in out[0].text
    assert "user can pay" in out[0].text
