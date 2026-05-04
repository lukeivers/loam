"""AC.JSTS.2 — JS/TS/Playwright idiom recognizers (8 modules).

Per the AC.JSTS.2 mapping table (plan-doc §4):

| Idiom                    | Module                     | Band       |
|--------------------------|----------------------------|------------|
| Express routes           | ``express_routes``         | PLAUSIBLE  |
| Playwright tests         | ``playwright_tests``       | VERIFIED   |
| Playwright page objects  | ``playwright_page_objects``| PLAUSIBLE  |
| TypeScript types         | ``ts_types``               | PLAUSIBLE  |
| Zod schemas              | ``zod_schemas``            | PLAUSIBLE  |
| class-validator          | ``class_validator``        | PLAUSIBLE  |
| Jest/Mocha/Vitest tests  | ``test_runners``           | VERIFIED   |
| Plain HTML/JS            | ``plain_html_js``          | PLAUSIBLE  |

This test file verifies each recognizer fires on the
jsts-playwright-app fixture (positive case) without false positives
on a clean source file (negative case).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
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


def test_express_routes_recognized_in_cjs(
    jsts_playwright_app_repo: Path,
) -> None:
    """Express routes recognized in CommonJS JS file."""
    fp = jsts_playwright_app_repo / "src/routes/users.js"
    src = fp.read_bytes()
    tree = parse_source(src, "javascript")
    out = recognize_express_routes(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # users.js declares 5 routes (GET / POST / DELETE / PUT / GET-by-id).
    assert len(out) >= 5
    methods = {ac.text for ac in out}
    assert any("GET" in t for t in methods)
    assert any("POST" in t for t in methods)
    assert any("DELETE" in t for t in methods)
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_express_routes_recognized_in_esm(
    jsts_playwright_app_repo: Path,
) -> None:
    """Express routes recognized in ESM .mjs file."""
    fp = jsts_playwright_app_repo / "src/routes/sessions.mjs"
    src = fp.read_bytes()
    tree = parse_source(src, "javascript")
    out = recognize_express_routes(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # sessions.mjs declares 3 routes (login / logout / refresh).
    assert len(out) >= 3


def test_express_routes_no_false_positive_on_clean_js() -> None:
    """Plain JS without Express routes → 0 ACs."""
    src = b"const x = 1;\nfunction foo() { return x; }\nmodule.exports = { foo };"
    tree = parse_source(src, "javascript")
    out = recognize_express_routes(
        tree, src, Path("clean.js"), Path("/"), "deadbeef"
    )
    assert out == []


def test_playwright_tests_verified(
    jsts_playwright_app_repo: Path,
) -> None:
    """Playwright tests in spec files emit VERIFIED ACs."""
    fp = jsts_playwright_app_repo / "tests/playwright/login.spec.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_playwright_tests(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # login.spec.ts has 3 test() blocks.
    assert len(out) == 3
    assert all(ac.confidence is ConfidenceBand.VERIFIED for ac in out)
    assert all(ac.evidence.kind == "test" for ac in out)
    assert all(ac.evidence.repo_sha == "deadbeef" for ac in out)


def test_playwright_tests_skipped_in_non_playwright_file() -> None:
    """A file without @playwright/test imports → no Playwright ACs."""
    src = b"function foo() { return 1; }"
    tree = parse_source(src, "javascript")
    out = recognize_playwright_tests(
        tree, src, Path("src/util.js"), Path("/"), "deadbeef"
    )
    assert out == []


def test_playwright_page_objects_recognized(
    jsts_playwright_app_repo: Path,
) -> None:
    """Page object class + each navigable method emits PLAUSIBLE."""
    fp = jsts_playwright_app_repo / "src/playwright/login-page.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_playwright_page_objects(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # LoginPage class + 3 methods (goto, login, signUp) = 4 ACs.
    assert len(out) >= 4
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)
    texts = " ".join(ac.text for ac in out)
    assert "LoginPage" in texts
    assert "login" in texts


def test_playwright_page_objects_skipped_outside_playwright_dir() -> None:
    """A class outside src/playwright/ is not a page object."""
    src = b"export class Foo { bar() { return 1 } }"
    tree = parse_source(src, "typescript")
    out = recognize_playwright_page_objects(
        tree, src, Path("src/util.ts"), Path("/"), "deadbeef"
    )
    assert out == []


def test_ts_types_recognized(jsts_playwright_app_repo: Path) -> None:
    """TS interfaces + type aliases emit PLAUSIBLE ACs."""
    fp = jsts_playwright_app_repo / "src/schemas/user.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_ts_types(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # user.ts has interface User + type UserId + type UserInput.
    assert len(out) >= 3
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_ts_types_skipped_in_js() -> None:
    """ts_types recognizer returns [] for .js files (no TS types)."""
    src = b"const x = 1;"
    tree = parse_source(src, "javascript")
    out = recognize_ts_types(
        tree, src, Path("x.js"), Path("/"), "deadbeef"
    )
    assert out == []


def test_zod_schemas_recognized(
    jsts_playwright_app_repo: Path,
) -> None:
    """Zod schemas + each field emit PLAUSIBLE ACs."""
    fp = jsts_playwright_app_repo / "src/schemas/user.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_zod_schemas(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # userSchema (1) + fields (email/name/age = 3) + userArraySchema (1).
    assert len(out) >= 4
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_class_validator_recognized(
    jsts_playwright_app_repo: Path,
) -> None:
    """class-validator decorators emit PLAUSIBLE ACs per field."""
    fp = (
        jsts_playwright_app_repo
        / "src/schemas/session-class-validator.ts"
    )
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_class_validator(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # SessionLoginDto has @IsEmail/@IsNotEmpty/@MinLength/@MaxLength/@IsOptional
    # SessionMetadataDto has 2x @IsOptional.
    assert len(out) >= 7
    assert all(ac.confidence is ConfidenceBand.PLAUSIBLE for ac in out)


def test_class_validator_skipped_in_js() -> None:
    src = b"class Foo {}"
    tree = parse_source(src, "javascript")
    out = recognize_class_validator(
        tree, src, Path("x.js"), Path("/"), "deadbeef"
    )
    assert out == []


def test_test_runners_vitest_verified(
    jsts_playwright_app_repo: Path,
) -> None:
    """Vitest tests emit VERIFIED ACs."""
    fp = jsts_playwright_app_repo / "tests/unit/users.test.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_test_runners(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # users.test.ts has 4 test calls (3 it + 1 test).
    assert len(out) >= 4
    assert all(ac.confidence is ConfidenceBand.VERIFIED for ac in out)
    assert all("vitest" in c for ac in out for c in ac.evidence.citations)


def test_test_runners_jest_style(
    jsts_playwright_app_repo: Path,
) -> None:
    """Jest-style tests (no explicit import) emit VERIFIED ACs.
    Runner identity is "unknown" without explicit import.
    """
    fp = jsts_playwright_app_repo / "tests/unit/server.test.js"
    src = fp.read_bytes()
    tree = parse_source(src, "javascript")
    out = recognize_test_runners(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    # server.test.js has 3 it blocks.
    assert len(out) >= 3
    assert all(ac.confidence is ConfidenceBand.VERIFIED for ac in out)


def test_test_runners_skipped_in_playwright_file(
    jsts_playwright_app_repo: Path,
) -> None:
    """Playwright spec files (importing @playwright/test) are NOT
    handled by the test_runners recognizer (avoiding double-counting).
    """
    fp = jsts_playwright_app_repo / "tests/playwright/login.spec.ts"
    src = fp.read_bytes()
    tree = parse_source(src, "typescript")
    out = recognize_test_runners(
        tree, src, fp, jsts_playwright_app_repo, "deadbeef"
    )
    assert out == []


def test_plain_html_js_recognized(
    jsts_playwright_app_repo: Path,
) -> None:
    """HTML files with <script> tags emit one PLAUSIBLE AC each."""
    fp = jsts_playwright_app_repo / "public/index.html"
    out = recognize_plain_html_js(
        fp, jsts_playwright_app_repo, "deadbeef"
    )
    assert len(out) == 1
    assert out[0].confidence is ConfidenceBand.PLAUSIBLE


def test_plain_html_js_no_script_returns_empty(tmp_path: Path) -> None:
    """HTML files without <script> tags → 0 ACs."""
    fp = tmp_path / "noscript.html"
    fp.write_bytes(b"<html><body>plain</body></html>")
    out = recognize_plain_html_js(fp, tmp_path, "deadbeef")
    assert out == []


def test_plain_html_js_non_html_returns_empty(tmp_path: Path) -> None:
    """Non-HTML files → 0 ACs."""
    fp = tmp_path / "x.js"
    fp.write_bytes(b"console.log('not html')")
    out = recognize_plain_html_js(fp, tmp_path, "deadbeef")
    assert out == []
