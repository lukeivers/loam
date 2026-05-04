"""AC.JSTS.5 — Confidence band rules per JS/TS/Playwright idiom.

Verifies the band/idiom mapping table:

| Idiom                    | Band       |
|--------------------------|------------|
| Express routes           | PLAUSIBLE  |
| TypeScript types         | PLAUSIBLE  |
| Zod schemas              | PLAUSIBLE  |
| class-validator          | PLAUSIBLE  |
| Playwright page objects  | PLAUSIBLE  |
| Plain HTML/JS            | PLAUSIBLE  |
| Playwright tests         | VERIFIED (with repo_sha) / PLAUSIBLE (without) |
| Jest/Mocha/Vitest tests  | VERIFIED (with repo_sha) / PLAUSIBLE (without) |
| Heuristic inference      | HYPOTHESISED |

And:

- Each band/evidence pair is validated by Cycle 2's
  :class:`BandedAC` model_validator at construction time
  (malformed pairs raise pydantic.ValidationError).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence
from loam_odd_extractor.lang.jsts.heuristic_inferences import (
    infer_domain_rules,
)
from loam_odd_extractor.lang.jsts.parser import parse_source
from loam_odd_extractor.lang.jsts.recognizers import (
    recognize_class_validator,
    recognize_express_routes,
    recognize_plain_html_js,
    recognize_playwright_page_objects,
    recognize_playwright_tests,
    recognize_test_runners,
    recognize_ts_types,
    recognize_zod_schemas,
)


def test_express_routes_band_plausible() -> None:
    src = b"const r = require('express').Router(); r.get('/', () => {});"
    tree = parse_source(src, "javascript")
    out = recognize_express_routes(
        tree, src, Path("r.js"), Path("/"), "deadbeef"
    )
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)
    assert all(ac.evidence.kind == "source" for ac in out)


def test_ts_types_band_plausible() -> None:
    src = b"interface X {y: string}\ntype Z = number"
    tree = parse_source(src, "typescript")
    out = recognize_ts_types(
        tree, src, Path("x.ts"), Path("/"), "deadbeef"
    )
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_zod_band_plausible() -> None:
    src = b"import {z} from 'zod';\nconst s = z.object({a: z.string()})"
    tree = parse_source(src, "typescript")
    out = recognize_zod_schemas(
        tree, src, Path("s.ts"), Path("/"), "deadbeef"
    )
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_class_validator_band_plausible() -> None:
    src = b"class X { @IsEmail() email!: string; }"
    tree = parse_source(src, "typescript")
    out = recognize_class_validator(
        tree, src, Path("x.ts"), Path("/"), "deadbeef"
    )
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_playwright_page_object_band_plausible() -> None:
    src = b"""
import { Page } from '@playwright/test';
export class LoginPage {
  constructor(private page: Page) {}
  async login(): Promise<void> {
    await this.page.goto('/login');
  }
}
"""
    tree = parse_source(src, "typescript")
    out = recognize_playwright_page_objects(
        tree, src, Path("src/playwright/login-page.ts"),
        Path("/"), "deadbeef",
    )
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_plain_html_js_band_plausible(tmp_path: Path) -> None:
    p = tmp_path / "x.html"
    p.write_bytes(b"<html><script>x</script></html>")
    out = recognize_plain_html_js(p, tmp_path, "deadbeef")
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_playwright_tests_band_verified_with_repo_sha() -> None:
    src = b"""
import { test } from '@playwright/test';
test('a', () => {});
"""
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, Path("tests/playwright/x.spec.ts"),
        Path("/"), "deadbeef" * 5,
    )
    assert all(ac.confidence is ConfidenceBand.VERIFIED for ac in out)
    assert all(ac.evidence.kind == "test" for ac in out)


def test_playwright_tests_downgrade_without_repo_sha() -> None:
    src = b"""
import { test } from '@playwright/test';
test('a', () => {});
"""
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, Path("tests/playwright/x.spec.ts"),
        Path("/"), None,
    )
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)
    assert all(ac.evidence.kind == "source" for ac in out)


def test_test_runners_band_verified_with_repo_sha() -> None:
    src = b"""
import { describe, it } from 'vitest';
describe('s', () => { it('t', () => {}); });
"""
    tree = parse_source(src, "typescript")
    out = recognize_test_runners(
        tree, src, Path("tests/unit/x.test.ts"),
        Path("/"), "deadbeef" * 5,
    )
    assert all(ac.confidence is ConfidenceBand.VERIFIED for ac in out)


def test_heuristic_inferences_band_hypothesised() -> None:
    src_acs = [
        BandedAC(
            ac_id="AC.JSTS.zod.userschema.email",
            text="Zod userSchema.email: z.string().email()",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x.ts:1"]),
        )
    ]
    out = infer_domain_rules(src_acs)
    assert len(out) >= 1
    assert all(
        ac.confidence is ConfidenceBand.HYPOTHESISED for ac in out
    )
    assert all(ac.evidence.kind == "inference" for ac in out)
    assert all(ac.evidence.rationale for ac in out)


# ---- malformed band/evidence pairs raise --------------------------


def test_verified_without_repo_sha_raises() -> None:
    """VERIFIED requires non-null repo_sha (Cycle 2 BANDS.2)."""
    with pytest.raises(ValidationError):
        BandedAC(
            ac_id="x",
            text="x",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="test",
                citations=["x.ts:1"],
                # repo_sha=None → invalid for VERIFIED
            ),
        )


def test_plausible_with_test_kind_raises() -> None:
    with pytest.raises(ValidationError):
        BandedAC(
            ac_id="x",
            text="x",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="test",  # PLAUSIBLE requires kind=source
                citations=["x.ts:1"],
                repo_sha="deadbeef" * 5,
            ),
        )


def test_hypothesised_without_rationale_raises() -> None:
    with pytest.raises(ValidationError):
        BandedAC(
            ac_id="x",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                citations=[],
                # rationale=None → invalid for HYPOTHESISED
            ),
        )
