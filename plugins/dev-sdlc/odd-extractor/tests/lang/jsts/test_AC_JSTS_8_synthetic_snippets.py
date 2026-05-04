"""AC.JSTS.8 — Adapter unit tests against hand-authored snippets.

Each recognizer exercised in isolation with hand-authored
JS/TS snippets — no full fixture required. Each test follows the
positive/negative pattern (Cycle 3 mirror).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.lang.jsts.heuristic_inferences import (
    infer_domain_rules,
)
from loam_odd_extractor.lang.jsts.parser import parse_source
from loam_odd_extractor.lang.jsts.recognizers import (
    recognize_class_validator,
    recognize_express_routes,
    recognize_playwright_page_objects,
    recognize_playwright_tests,
    recognize_test_runners,
    recognize_ts_types,
    recognize_zod_schemas,
)


def test_express_routes_positive_negative() -> None:
    pos = b"""
const app = require('express')();
app.get('/x', () => {});
app.post('/y', requireAuth, () => {});
"""
    neg = b"const x = 1;\nfunction foo(){}"
    tree = parse_source(pos, "javascript")
    assert len(recognize_express_routes(
        tree, pos, Path("a.js"), Path("/"), "deadbeef")) == 2
    tree = parse_source(neg, "javascript")
    assert recognize_express_routes(
        tree, neg, Path("a.js"), Path("/"), "deadbeef") == []


def test_ts_types_positive_negative() -> None:
    pos = b"""
interface User { x: string }
type Y = number;
"""
    neg = b"const x = 1;"
    tree = parse_source(pos, "typescript")
    out = recognize_ts_types(tree, pos, Path("a.ts"), Path("/"), "x")
    assert len(out) == 2
    tree = parse_source(neg, "typescript")
    assert recognize_ts_types(
        tree, neg, Path("a.ts"), Path("/"), "x") == []


def test_zod_schemas_positive_negative() -> None:
    pos = b"""
import {z} from 'zod';
const s = z.object({a: z.string(), b: z.number()})
"""
    neg = b"const x = {a: 1, b: 2}"
    tree = parse_source(pos, "typescript")
    out = recognize_zod_schemas(
        tree, pos, Path("a.ts"), Path("/"), "x")
    # 1 schema + 2 fields
    assert len(out) >= 1
    tree = parse_source(neg, "typescript")
    assert recognize_zod_schemas(
        tree, neg, Path("a.ts"), Path("/"), "x") == []


def test_class_validator_positive_negative() -> None:
    pos = b"""
class X {
  @IsEmail()
  e!: string;

  @MinLength(2)
  n!: string;
}
"""
    neg = b"class X { e!: string; n!: string; }"
    tree = parse_source(pos, "typescript")
    out = recognize_class_validator(
        tree, pos, Path("a.ts"), Path("/"), "x")
    assert len(out) == 2
    tree = parse_source(neg, "typescript")
    assert recognize_class_validator(
        tree, neg, Path("a.ts"), Path("/"), "x") == []


def test_playwright_tests_positive_negative() -> None:
    pos = b"""
import {test, expect} from '@playwright/test';
test.describe('grp', () => {
  test('one', async ({page}) => { expect(page).toBeTruthy(); });
});
"""
    # No @playwright/test import → skipped.
    neg = b"function foo() { return 1; }"
    tree = parse_source(pos, "typescript")
    out = recognize_playwright_tests(
        tree, pos, Path("tests/playwright/a.spec.ts"),
        Path("/"), "deadbeef" * 5)
    assert len(out) == 1
    tree = parse_source(neg, "javascript")
    assert recognize_playwright_tests(
        tree, neg, Path("a.js"), Path("/"), "x") == []


def test_playwright_page_object_positive_negative() -> None:
    pos = b"""
export class LoginPage {
  constructor(private page: any) {}
  async login() { await this.page.goto('/login'); }
}
"""
    # Same syntax but outside playwright dir → skipped.
    neg_path = Path("src/util.ts")
    pos_path = Path("src/playwright/login-page.ts")
    tree = parse_source(pos, "typescript")
    out = recognize_playwright_page_objects(
        tree, pos, pos_path, Path("/"), "x")
    assert len(out) >= 2
    tree = parse_source(pos, "typescript")
    assert recognize_playwright_page_objects(
        tree, pos, neg_path, Path("/"), "x") == []


def test_test_runners_positive_negative() -> None:
    pos = b"""
import {describe, it} from 'vitest';
describe('s', () => { it('t', () => {}); });
"""
    # Non-test file → skipped.
    neg_path = Path("src/util.ts")
    pos_path = Path("tests/unit/a.test.ts")
    tree = parse_source(pos, "typescript")
    assert len(recognize_test_runners(
        tree, pos, pos_path, Path("/"), "deadbeef" * 5)) == 1
    assert recognize_test_runners(
        tree, pos, neg_path, Path("/"), "x") == []


def test_heuristic_inference_combined_snippet() -> None:
    """Every heuristic pattern fires on a representative input."""
    from loam_odd_extractor.bands import BandedAC, Evidence

    inputs = [
        BandedAC(
            ac_id="AC.JSTS.zod.us.email.x",
            text="Zod us.email: z.string().email()",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x:1"]),
        ),
        BandedAC(
            ac_id="AC.JSTS.zod.us.name.x",
            text="Zod us.name: z.string().min(3)",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x:1"]),
        ),
        BandedAC(
            ac_id="AC.JSTS.class_validator.dto.email.isemail.x",
            text="DTO.email validated by @IsEmail()",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x:1"]),
        ),
        BandedAC(
            ac_id="AC.JSTS.express.post.users.x",
            text="Express route POST /users with middleware [requireAuth]",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x:1"]),
        ),
        BandedAC(
            ac_id="AC.JSTS.playwright_page.lp.login.x",
            text="LoginPage#login: page-interaction method",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x:1"]),
        ),
    ]
    out = infer_domain_rules(inputs)
    # Each pattern fires once.
    assert len(out) == 5
    assert all(
        ac.confidence is ConfidenceBand.HYPOTHESISED for ac in out
    )
