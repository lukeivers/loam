"""AC.OSS-M6.8 — M2 partition manifest classifies `plugins/dev-sdlc/`.

Per plan §4 AC.OSS-M6.8 + §11 finding #1: M6a extends the partition
manifest's `audit_roots:` to include `plugins/` and adds a glob entry
for `plugins/dev-sdlc/**` under `dev_and_public:` (M6a baseline; M6b
reclassifies to `dev_only` per AC.OSS-M6.13 + D-build.M6.14).

Verification:
  - Every file under `plugins/dev-sdlc/` classifies (no unclassified
    leaves).
  - Each leaf classifies as `dev_and_public` (M6a baseline shape).
  - The canonical manifest at canonical HEAD reflects the
    extension.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam.publish_framework_only.partition import (
    PartitionClass,
    classify_path,
    load_manifest,
)


CANONICAL_REPO = Path(__file__).resolve().parents[4]
CANONICAL_MANIFEST = (
    CANONICAL_REPO
    / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml"
)


def _make_manifest(tmp_path: Path, body: str) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(body)
    return manifest


def test_canonical_manifest_admits_plugins_in_audit_roots() -> None:
    """The canonical manifest at HEAD includes `plugins/` under
    `audit_roots:`."""
    if not CANONICAL_MANIFEST.exists():
        import pytest

        pytest.skip("canonical manifest not at expected location")
    manifest = load_manifest(CANONICAL_MANIFEST)
    audit_roots = list(manifest.audit_roots)
    assert "plugins/" in audit_roots


def test_plugins_dev_sdlc_classifies_dev_and_public(
    tmp_path: Path,
) -> None:
    """A synthetic manifest matching M6a's extension classifies
    `plugins/dev-sdlc/**` as `dev_and_public`."""
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [plugins/]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "plugins/dev-sdlc/**"
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    sample_paths = [
        "plugins/dev-sdlc/pyproject.toml",
        "plugins/dev-sdlc/README.md",
        "plugins/dev-sdlc/src/loam/plugins/dev_sdlc/api.py",
        "plugins/dev-sdlc/src/loam/plugins/dev_sdlc/cli.py",
        "plugins/dev-sdlc/skills/start-project.md",
        "plugins/dev-sdlc/tests/test_AC_OSS_M6_2_new_project_scaffolds_odd_tree.py",
    ]
    for p in sample_paths:
        cls = classify_path(manifest, p)
        assert cls == PartitionClass.DEV_AND_PUBLIC, (
            f"{p} expected dev_and_public; got {cls}"
        )


def test_canonical_manifest_classifies_plugin_files() -> None:
    """Against the canonical manifest, every plugin file classifies
    (no None returns) according to the FBE.3 split-admit shape.

    Per FBE.3 (v0.1.0 reviewer foldback; parent plan §3 Decision B.2),
    the plugin source ships dev_and_public; the dev-discipline
    subtree stays dev_only. Per-subtree expected class is computed
    from the path prefix.
    """
    if not CANONICAL_MANIFEST.exists():
        import pytest

        pytest.skip("canonical manifest not at expected location")
    plugin_dir = CANONICAL_REPO / "plugins" / "dev-sdlc"
    if not plugin_dir.is_dir():
        import pytest

        pytest.skip("dev-sdlc plugin tree not yet authored")
    manifest = load_manifest(CANONICAL_MANIFEST)
    for f in plugin_dir.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(CANONICAL_REPO).as_posix()
        # Skip transient cache content (gitignored — git ls-tree
        # never sees these; the test skips them so a developer's
        # local cache state doesn't break the assertion).
        if (
            "__pycache__" in rel
            or rel.endswith(".pyc")
            or ".pytest_cache" in rel
            or ".egg-info" in rel
        ):
            continue
        cls = classify_path(manifest, rel)
        assert cls is not None, f"{rel} unclassified"
        # Per-subtree expected class.
        #
        # Pre-M6b.0 (M6a baseline): plugin paths classified
        # `dev_and_public` per AC.OSS-M6.8 (the plugin's user-facing
        # capabilities ship publicly so users could compose against
        # the harness extension protocol).
        # M6b.0: plugin paths RECLASSIFIED to `dev_only` per
        # AC.OSS-M6b0.9 + master plan D-build.M6.14 — the plugin
        # gained the dev-discipline corpus (CDCs, long-form ODD docs,
        # conventions, gate hooks, loam-mode tooling) so the BLANKET
        # `dev_only` placement was correct at M6b.0.
        # FBE.3 (v0.1.0 reviewer foldback; parent plan §3 Decision
        # B.2): SPLIT-ADMITTED. The user-facing plugin source (`src/`,
        # `pyproject.toml`, `README.md`) ships `dev_and_public`; the
        # dev-discipline subtree (`docs/`, `hooks/`, `templates/`,
        # `tools/`, `dev-mode-manifest.yaml`) STAYS `dev_only`. Pre-
        # existing universal `**/seals/**` + `**/tests/**` precedence
        # rules continue to win for those subtrees.
        if (
            rel == "plugins/dev-sdlc/pyproject.toml"
            or rel == "plugins/dev-sdlc/README.md"
            or rel.startswith("plugins/dev-sdlc/src/")
            or rel.startswith("plugins/dev-sdlc/skills/")
        ):
            expected = PartitionClass.DEV_AND_PUBLIC
        else:
            expected = PartitionClass.DEV_ONLY
        assert cls == expected, (
            f"{rel}: expected {expected} per FBE.3 split-admit "
            f"(parent plan §3 Decision B.2); got {cls}"
        )
