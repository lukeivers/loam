"""AC.BAFI.S — outcome-altitude smoke for Batch A (amendment #145).

Reads each of the five files touched by Batch A from the repo root
and asserts the corrected content is present + the stale content is
absent. Production-altitude file reads, no pre-arranged state, no
mocks. RED-on-regression: this test FAILS against the pre-amendment
tree (mutation proof — reverting any of the five edits flips the
matching assertion to red).

Per `feedback_test_outcome_altitude_required`: the AC set carries
≥1 `outcome-altitude: true` AC verified by a test invoking the
production entry-point (here, the filesystem read of the actual
committed files) with no pre-arranged state.

Maps strictly to AC.BAFI.S in
`docs/plans/loam-doc-consistency-batch-a.md` §4. Each assertion in
this file ladders up to the named AC.
"""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    """Walk upward from this file to the loam repo root.

    The repo root is the first ancestor containing `install-from-
    source.txt` AND `README.md` AND `plugins/loam-skills/`.
    """
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (
            (candidate / "install-from-source.txt").is_file()
            and (candidate / "README.md").is_file()
            and (candidate / "plugins" / "loam-skills").is_dir()
        ):
            return candidate
    raise RuntimeError(
        "Could not locate loam repo root from "
        f"{here} — no ancestor carries install-from-source.txt + README.md + plugins/loam-skills/"
    )


REPO = _repo_root()


def test_AC_BAFI_INSTALL_stale_binary_observation_harness_line_removed() -> None:
    """AC.BAFI.INSTALL — docs/install-from-source.md no longer
    enumerates the non-existent `framework/binary-observation-harness`
    component."""
    body = (REPO / "docs" / "install-from-source.md").read_text(encoding="utf-8")
    assert "binary-observation-harness" not in body, (
        "stale `pip install -e ./framework/binary-observation-harness` "
        "line still present in docs/install-from-source.md — "
        "AC.BAFI.INSTALL regressed."
    )


def test_AC_BAFI_ARCH_skills_section_reflects_current_reality() -> None:
    """AC.BAFI.ARCH — docs/architecture.md Skills section names the
    two SKILL-contributing plugins + the auto-symlink mechanism, and
    no longer carries the stale "loam does not ship skills directly"
    framing or the `start-project` reference."""
    body = (REPO / "docs" / "architecture.md").read_text(encoding="utf-8")
    # Stale framing absent.
    assert "loam does not ship skills directly" not in body, (
        "stale `loam does not ship skills directly` framing still "
        "present in docs/architecture.md — AC.BAFI.ARCH regressed."
    )
    assert "start-project" not in body, (
        "stale `start-project` reference still present in "
        "docs/architecture.md — AC.BAFI.ARCH regressed "
        "(D-BAFI.START-PROJECT removes it entirely)."
    )
    # Corrected framing present: both plugins named + symlink mechanism cited.
    assert "loam-skills" in body, (
        "AC.BAFI.ARCH rewrite must name the loam-skills plugin in "
        "docs/architecture.md Skills section."
    )
    assert "dev-sdlc" in body, (
        "AC.BAFI.ARCH rewrite must name the dev-sdlc plugin in "
        "docs/architecture.md Skills section."
    )
    assert "_symlink_plugin_skills" in body, (
        "AC.BAFI.ARCH rewrite must cite the `_symlink_plugin_skills` "
        "auto-discovery mechanism in docs/architecture.md."
    )


def test_AC_BAFI_PYPROJ_description_count_neutral() -> None:
    """AC.BAFI.PYPROJ — plugins/loam-skills/pyproject.toml description
    no longer claims "five SKILL.md packages" or enumerates the
    legacy five-name list; package metadata (name) preserved."""
    body = (REPO / "plugins" / "loam-skills" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "five SKILL" not in body, (
        "stale `five SKILL` count still present in "
        "plugins/loam-skills/pyproject.toml description — "
        "AC.BAFI.PYPROJ regressed."
    )
    # The legacy enumeration "(memory-recall, scope-decompose, ...)"
    # would re-stale as the corpus grows; the count-neutral rewrite
    # drops the enumeration entirely.
    assert "memory-recall, scope-decompose" not in body, (
        "stale legacy SKILL enumeration still present in "
        "plugins/loam-skills/pyproject.toml description — "
        "AC.BAFI.PYPROJ regressed (D-BAFI.PYPROJ-NEUTRAL drops it)."
    )
    # Package metadata preserved (sanity: pyproject still parseable
    # and the package name is unchanged).
    try:
        import tomllib  # py3.11+
    except ImportError:  # pragma: no cover — py3.13 baseline
        import tomli as tomllib  # type: ignore[no-redef]
    parsed = tomllib.loads(body)
    assert parsed["project"]["name"] == "loam-plugin-loam-skills", (
        "AC.BAFI.PYPROJ must preserve project.name — got "
        f"{parsed['project']['name']!r}"
    )


def test_AC_BAFI_QUICK_readme_quickstart_names_onboarding_ritual() -> None:
    """AC.BAFI.QUICK — README.md quickstart section carries a callout
    noting the interactive onboarding ritual + LOAM_ONBOARDING_SKIP=1
    skip env. Step numbering (1-4) preserved intact."""
    body = (REPO / "README.md").read_text(encoding="utf-8")
    assert "LOAM_ONBOARDING_SKIP" in body, (
        "README.md quickstart missing the LOAM_ONBOARDING_SKIP callout "
        "— AC.BAFI.QUICK regressed."
    )
    # Step numbering preserved: 1-4 still present as comments in the
    # quickstart fenced block.
    for step in ("# 1.", "# 2.", "# 3.", "# 4."):
        assert step in body, (
            f"README.md quickstart step marker {step!r} missing — "
            "AC.BAFI.QUICK must NOT renumber the 4 quickstart steps."
        )


def test_AC_BAFI_DOCS_readme_documentation_section_no_anachronistic_parenthetical() -> None:
    """AC.BAFI.DOCS — README.md Documentation section no longer
    contains the anachronistic "authored alongside this README in
    the v0.1.0 docs lane" parenthetical. Link targets preserved."""
    body = (REPO / "README.md").read_text(encoding="utf-8")
    assert "authored alongside this README in the v0.1.0 docs lane" not in body, (
        "stale `authored alongside this README in the v0.1.0 docs "
        "lane` parenthetical still present in README.md — "
        "AC.BAFI.DOCS regressed."
    )
    # Link targets preserved.
    assert "docs/architecture.md" in body, (
        "AC.BAFI.DOCS must preserve the docs/architecture.md link "
        "target in README.md."
    )
    assert "docs/getting-started.md" in body, (
        "AC.BAFI.DOCS must preserve the docs/getting-started.md link "
        "target in README.md."
    )
