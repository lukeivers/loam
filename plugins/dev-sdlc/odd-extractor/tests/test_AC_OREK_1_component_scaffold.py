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
    """src/, tests/ exist; pyproject.toml + README.md present.

    Seal-narrative sidecars land in the parent dev-sdlc plugin's
    seals/ directory (plugins/dev-sdlc/seals/SEAL_COMMIT.<slug>),
    not under odd-extractor/seals/ — the dev-sdlc plugin is the
    sealed-component fence and its seals/ is the canonical
    narrative location.
    """
    assert (_ROOT / "pyproject.toml").exists()
    assert (_ROOT / "README.md").exists()
    assert (_ROOT / "src" / "loam_odd_extractor" / "__init__.py").exists()
    assert (_ROOT / "tests").is_dir()
    # Parent plugin's seals dir is the canonical seal-narrative
    # location for this sub-tree.
    assert (_ROOT.parent / "seals").is_dir()


def test_pyproject_parses_and_declares_required_metadata() -> None:
    """pyproject.toml parses; declares name, version, requires-python.

    The version premise is DERIVED from ``docs/ACTIVE_MINOR`` at test
    time (broken-suite-family-fixes D-SUITEFIX.6): this pyproject is
    in the PCVR lockstep's IN_SCOPE_PYPROJECTS set, so its version
    equals the current shipped MINOR by structural enforcement
    (test_AC_PCVR_pyproject_version_lockstep.py). Pinning a literal
    here rots at every minor bump — the original "0.1.0" pin broke
    when the lockstep landed.
    """
    pp_path = _ROOT / "pyproject.toml"
    data = tomllib.loads(pp_path.read_text(encoding="utf-8"))
    assert data["project"]["name"] == "loam-odd-extractor"
    # _ROOT = plugins/dev-sdlc/odd-extractor → parents[2] = repo root.
    active_minor_path = _ROOT.parents[2] / "docs" / "ACTIVE_MINOR"
    active_minor = active_minor_path.read_text(encoding="utf-8").strip()
    assert data["project"]["version"] == active_minor, (
        f"odd-extractor pyproject version must track docs/ACTIVE_MINOR "
        f"({active_minor!r}) per the PCVR lockstep; got "
        f"{data['project']['version']!r}"
    )
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
