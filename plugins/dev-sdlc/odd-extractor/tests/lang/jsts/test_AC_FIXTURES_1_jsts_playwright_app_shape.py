"""AC.FIXTURES.1 — jsts-playwright-app fixture shape verification.

Per the cycle plan-doc §4 AC.FIXTURES.1:

- TypeScript Playwright tests + page objects under
  ``src/playwright/`` and ``tests/playwright/``.
- JavaScript/Node Express backend under ``src/`` (mix of
  CommonJS and ESM module shapes).
- Plain HTML/JS in ``public/``.
- ≥10 tests across runners.
- README, package.json, tsconfig.json present.
- Both ESM (.mjs / TS module) AND CommonJS (.js with require) module
  shapes exercised.
- Both Zod AND class-validator schemas present (per Surface #5).
"""

from __future__ import annotations

import json
import re
from pathlib import Path



_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "fixtures"
    / "jsts-playwright-app"
)


def test_fixture_exists() -> None:
    assert _FIXTURE.is_dir()


def test_package_json_present_and_valid() -> None:
    p = _FIXTURE / "package.json"
    assert p.is_file()
    data = json.loads(p.read_text())
    deps = set(data.get("dependencies", {})) | set(
        data.get("devDependencies", {})
    )
    assert "express" in deps
    assert "@playwright/test" in deps
    assert "zod" in deps
    assert "vitest" in deps
    assert "class-validator" in deps


def test_tsconfig_json_present_and_valid() -> None:
    p = _FIXTURE / "tsconfig.json"
    assert p.is_file()
    data = json.loads(p.read_text())
    assert "compilerOptions" in data
    assert data["compilerOptions"].get("strict") is True


def test_playwright_config_present() -> None:
    assert (_FIXTURE / "playwright.config.ts").is_file()


def test_readme_present_and_clearly_synthetic() -> None:
    p = _FIXTURE / "README.md"
    assert p.is_file()
    text = p.read_text()
    # README banner labels SYNTHETIC.
    assert "SYNTHETIC" in text or "synthetic" in text


def test_src_playwright_dir_with_page_objects() -> None:
    pw = _FIXTURE / "src/playwright"
    assert pw.is_dir()
    # At least 2 page-object files.
    pages = list(pw.glob("*.ts"))
    assert len(pages) >= 2


def test_src_routes_with_cjs_and_esm() -> None:
    """Both CommonJS (.js) AND ESM (.mjs) module shapes present."""
    routes = _FIXTURE / "src/routes"
    assert routes.is_dir()
    js_files = list(routes.glob("*.js"))
    mjs_files = list(routes.glob("*.mjs"))
    assert len(js_files) >= 1, "expected at least one .js (CJS) routes file"
    assert len(mjs_files) >= 1, "expected at least one .mjs (ESM) routes file"

    # Verify CJS shape via content inspection.
    cjs_text = (routes / "users.js").read_text()
    assert "module.exports" in cjs_text or "exports." in cjs_text
    assert "require(" in cjs_text

    # Verify ESM shape.
    esm_text = (routes / "sessions.mjs").read_text()
    assert "export default" in esm_text or "export {" in esm_text
    assert "import " in esm_text


def test_src_middleware_present() -> None:
    assert (_FIXTURE / "src/middleware/auth.js").is_file()


def test_src_schemas_zod_and_class_validator() -> None:
    """Per Surface #5 — Zod AND class-validator schemas present."""
    schemas = _FIXTURE / "src/schemas"
    assert schemas.is_dir()
    zod_text = (schemas / "user.ts").read_text()
    assert "z.object(" in zod_text
    assert "z.string()" in zod_text
    cv_text = (schemas / "session-class-validator.ts").read_text()
    assert "@IsEmail" in cv_text


def test_tests_playwright_dir_with_specs() -> None:
    pw = _FIXTURE / "tests/playwright"
    assert pw.is_dir()
    specs = list(pw.glob("*.spec.ts"))
    assert len(specs) >= 2


def test_tests_unit_with_vitest_and_jest_style() -> None:
    unit = _FIXTURE / "tests/unit"
    assert unit.is_dir()
    # Vitest TS test.
    v = unit / "users.test.ts"
    assert v.is_file()
    assert "from 'vitest'" in v.read_text()
    # Jest-style JS (no explicit import — Jest globals).
    j = unit / "server.test.js"
    assert j.is_file()


def test_public_html_files_present() -> None:
    pub = _FIXTURE / "public"
    assert pub.is_dir()
    htmls = list(pub.glob("*.html"))
    assert len(htmls) >= 2
    # Each contains a <script> tag.
    for h in htmls:
        text = h.read_text()
        assert "<script" in text.lower()


def _count_test_calls(file_text: str) -> int:
    """Crude heuristic: count occurrences of ``test('``,
    ``it('`` or ``test('`` patterns at line-start. Used for the
    minimum-test-count check.
    """
    return len(re.findall(
        r"^\s*(test|it)\s*\(\s*['\"]",
        file_text,
        re.MULTILINE,
    ))


def test_total_tests_at_least_ten() -> None:
    """Per AC.FIXTURES.1 — ≥10 tests across runners."""
    total = 0
    for spec in (_FIXTURE / "tests/playwright").glob("*.spec.ts"):
        total += _count_test_calls(spec.read_text())
    for unit in (_FIXTURE / "tests/unit").iterdir():
        if unit.is_file():
            total += _count_test_calls(unit.read_text())
    assert total >= 10, f"expected ≥10 tests; got {total}"
