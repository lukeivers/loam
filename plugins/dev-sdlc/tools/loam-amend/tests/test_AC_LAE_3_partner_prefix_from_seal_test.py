"""AC.LAE.3 — partner-prefix derived from manifest's ``seal_test`` path.

Plan: ``docs/rebuild/plans/v0-1-2-loam-amend-ergonomics.md`` AC.LAE.3.
Per v0.1.2 item 6 (loam-amend ergonomics sweep). Fixes the latent
``plugins/<name>/``-located component mis-shape; framework-located
manifests' admissions are unchanged (modulo the dropped bare-
``<name>/`` admission, which was a D.1 vestigial back-compat hedge).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import yaml

from loam_amend.commands.apply import _partner_prefix
from loam_amend.commands.apply import run as apply_run


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _seed_at(
    repo: Path, base: str, name: str, baseline_value: str = "0000000"
) -> None:
    """Seed a component at <base>/<name>/ with seal-test + sidecar."""
    comp = repo / base / name
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text(
        "def foo():\n    return 1\n", encoding="utf-8"
    )
    (comp / "tests" / "SEAL_COMMIT").write_text(
        f"{baseline_value}\n", encoding="utf-8"
    )
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{baseline_value}"

            def test_x():
                allowed_prefixes = (
                    "{base}/{name}/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def test_partner_prefix_helper_framework_located() -> None:
    """Framework-located seal_test resolves to ``framework/<name>/``."""
    p = _partner_prefix(
        "framework/alpha/tests/test_no_sealed_amendments.py", "alpha"
    )
    assert p == "framework/alpha/", p


def test_partner_prefix_helper_plugins_located() -> None:
    """Plugins-located seal_test resolves to ``plugins/<name>/``."""
    p = _partner_prefix(
        "plugins/dev-sdlc/tests/test_no_sealed_amendments.py", "dev-sdlc"
    )
    assert p == "plugins/dev-sdlc/", p


def test_partner_prefix_helper_defensive_fallback() -> None:
    """Non-canonical seal_test path falls back to framework/<name>/."""
    p = _partner_prefix("weird/path.py", "weirdcomp")
    assert p == "framework/weirdcomp/", p


def test_mixed_fence_admissions_have_correct_shapes(
    scratch_repo: Path,
) -> None:
    """Mixed framework/ + plugins/ amendment admits both correct shapes."""
    repo = scratch_repo
    _seed_at(repo, "framework", "alpha", baseline_value="aaaaaaa")
    _seed_at(repo, "plugins", "beta", baseline_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha + beta")

    # Substantive edit on both so apply has work to do.
    (repo / "framework" / "alpha" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    (repo / "plugins" / "beta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit alpha + beta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 99,
                    "slug": "ac-lae-3-mixed",
                    "title": "mixed fence",
                },
                "baseline": baseline,
                "plan": "docs/rebuild/plans/ac-lae-3-mixed.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                    {
                        "name": "beta",
                        "seal_test": "plugins/beta/tests/test_no_sealed_amendments.py",
                        "sidecar": "plugins/beta/tests/SEAL_COMMIT",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest")

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0, "apply should succeed"

    # alpha's seal-test should now admit plugins/beta/ as cross-component
    # partner.
    alpha_test = (
        repo / "framework" / "alpha" / "tests" / "test_no_sealed_amendments.py"
    ).read_text(encoding="utf-8")
    assert "plugins/beta/" in alpha_test, (
        f"alpha should admit plugins/beta/ (partner from seal_test): "
        f"{alpha_test}"
    )
    # The buggy-shape admission must NOT appear.
    assert "framework/beta/" not in alpha_test, (
        f"alpha must not carry the wrong-shape framework/beta/ admission: "
        f"{alpha_test}"
    )

    # beta's seal-test should now admit framework/alpha/ as cross-component
    # partner.
    beta_test = (
        repo / "plugins" / "beta" / "tests" / "test_no_sealed_amendments.py"
    ).read_text(encoding="utf-8")
    assert "framework/alpha/" in beta_test, (
        f"beta should admit framework/alpha/ (partner from seal_test): "
        f"{beta_test}"
    )
    # Self-exclusion: beta should NOT admit its own plugins/beta/ in the
    # widened set (it already has it as its own primary fence).
    # The widening only adds partners; the seed already has plugins/beta/.
    # The widening must not duplicate plugins/beta/ (idempotency tested
    # by the byte-matching of plugins/beta/ count below: still 1).
    assert beta_test.count('"plugins/beta/"') == 1, (
        f"plugins/beta/ should appear once (self-exclusion intact): "
        f"{beta_test}"
    )
