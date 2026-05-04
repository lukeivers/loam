"""AC.OREK.1 — component scaffold present.

The odd-extractor sub-package exists with the expected directory
shape, pyproject.toml parses, and the CLI subcommand entry-point is
declared.
"""

from __future__ import annotations

from pathlib import Path

import tomllib


_ROOT = Path(__file__).resolve().parent.parent


def test_directory_layout() -> None:
    """src/, tests/, seals/ all exist; pyproject.toml + README.md present."""
    assert (_ROOT / "pyproject.toml").exists()
    assert (_ROOT / "README.md").exists()
    assert (_ROOT / "src" / "loam_odd_extractor" / "__init__.py").exists()
    assert (_ROOT / "tests").is_dir()
    assert (_ROOT / "seals").is_dir()


def test_pyproject_parses_and_declares_required_metadata() -> None:
    """pyproject.toml parses; declares name, version, requires-python."""
    pp_path = _ROOT / "pyproject.toml"
    data = tomllib.loads(pp_path.read_text(encoding="utf-8"))
    assert data["project"]["name"] == "loam-odd-extractor"
    assert data["project"]["version"] == "0.1.0"
    assert data["project"]["requires-python"].startswith(">=3.")
    deps = data["project"]["dependencies"]
    assert "loam-cost-governance" in deps
    assert "loam-cli" in deps
    assert "PyYAML>=6" in deps or any(
        d.startswith("PyYAML") for d in deps
    )


def test_cli_subcommand_entrypoint_declared() -> None:
    """[project.entry-points."loam.cli.subcommands"] odd-extract = ... is declared."""
    pp_path = _ROOT / "pyproject.toml"
    data = tomllib.loads(pp_path.read_text(encoding="utf-8"))
    eps = (
        data.get("project", {})
        .get("entry-points", {})
        .get("loam.cli.subcommands", {})
    )
    assert "odd-extract" in eps
    target = eps["odd-extract"]
    # Form: "loam_odd_extractor.cli:build_odd_extract_subcommand"
    module, _, attr = target.partition(":")
    assert module == "loam_odd_extractor.cli"
    assert attr == "build_odd_extract_subcommand"


def test_public_api_re_exports_present() -> None:
    """Importing the package re-exports the AC-named public surface."""
    import loam_odd_extractor as m

    expected_names = {
        # Stage functions
        "init_extraction",
        "analyze_repo",
        "generate_raw_acs",
        "verify_contract",
        # Models
        "ExtractionConfig",
        "AnalysisPlan",
        "Slice",
        "RawACs",
        "ContractDraft",
        # Registry
        "LanguageAdapter",
        "register_adapter",
        "discover_adapters",
        # Budget
        "estimate_for_extraction",
        "enforce_budget",
        "default_budget",
        "budget_from_cents",
        # Errors
        "OddExtractorError",
        "BudgetExceededError",
        "RegistryError",
        "StageError",
        # CLI
        "build_odd_extract_subcommand",
    }
    for name in expected_names:
        assert hasattr(m, name), f"missing public name: {name}"
        assert name in m.__all__, f"missing from __all__: {name}"
