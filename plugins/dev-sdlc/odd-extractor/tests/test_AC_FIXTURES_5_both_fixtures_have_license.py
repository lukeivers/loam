"""AC.FIXTURES.5 (v0.1.8 Cycle 4b) — both canonical fixtures
committed real repos with permissive LICENSE.

Verifies BOTH ``ruby-rails-payment/`` AND ``jsts-playwright-app/``
have a non-empty Apache-2.0 LICENSE file at their root.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_FIXTURES_ROOT = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "fixture_name",
    ["ruby-rails-payment", "jsts-playwright-app"],
)
def test_fixture_has_license_file(fixture_name: str) -> None:
    """LICENSE file exists at the fixture's root."""
    license_path = _FIXTURES_ROOT / fixture_name / "LICENSE"
    assert license_path.is_file(), (
        f"Fixture '{fixture_name}' missing LICENSE at {license_path}"
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["ruby-rails-payment", "jsts-playwright-app"],
)
def test_fixture_license_is_non_empty(fixture_name: str) -> None:
    license_text = (_FIXTURES_ROOT / fixture_name / "LICENSE").read_text()
    assert license_text.strip(), (
        f"Fixture '{fixture_name}' LICENSE is empty"
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["ruby-rails-payment", "jsts-playwright-app"],
)
def test_fixture_license_is_recognisable_permissive(
    fixture_name: str,
) -> None:
    """Recognisable Apache-2.0 OR MIT header pattern."""
    license_text = (_FIXTURES_ROOT / fixture_name / "LICENSE").read_text()

    apache_match = (
        "Apache License" in license_text and "Version 2.0" in license_text
    )
    mit_match = (
        "Permission is hereby granted, free of charge" in license_text
    )

    assert apache_match or mit_match, (
        f"Fixture '{fixture_name}' LICENSE is not recognisable as "
        f"Apache-2.0 or MIT"
    )


def test_both_fixtures_are_real_committed_directories() -> None:
    """Both fixtures are real committed file trees (not git submodules
    or generated-by-script).
    """
    for fixture_name in ("ruby-rails-payment", "jsts-playwright-app"):
        fixture_dir = _FIXTURES_ROOT / fixture_name
        assert fixture_dir.is_dir(), (
            f"Fixture '{fixture_name}' is not a directory"
        )
        # No .gitmodules / no submodule sentinel file at the fixture root.
        assert not (fixture_dir / ".gitmodules").exists(), (
            f"Fixture '{fixture_name}' has .gitmodules — should be a "
            f"real committed directory, not a submodule"
        )
        # Real directory has files (not just a placeholder).
        files = [p for p in fixture_dir.rglob("*") if p.is_file()]
        assert len(files) >= 5, (
            f"Fixture '{fixture_name}' has only {len(files)} files; "
            f"appears to be a stub or missing content"
        )
