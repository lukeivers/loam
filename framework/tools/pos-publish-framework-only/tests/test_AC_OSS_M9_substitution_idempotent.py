"""AC.OSS-M9.3 — substitution pass is idempotent across two-pass synthesis.

Per oss-v0-1-0-publish-scrub.md §4 AC.OSS-M9.3: synthesises twice on
the same source SHA + manifest. The second call must no-op (the
existing-tree-matches branch in ``synthesise_framework_only``); the
returned SHAs must match.

Determinism guarantee: the substitution table contains no entry where
the replacement is itself a substitution source (e.g. ``<workspace>/loam``
isn't a key), so the second pass finds zero tokens and produces an
identical synthetic tree-SHA.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam.publish_framework_only.synth import synthesise_framework_only


def test_AC_OSS_M9_3_two_pass_synthesis_is_idempotent(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """First synthesis advances framework-only; second is a no-op
    with the same SHA."""
    manifest_yaml = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots:
          - framework/
          - docs/
          - CLAUDE.md
          - CLAUDE.dev.md
          - README.md
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/**"
            exclude: ["framework/tools/pos-publish-framework-only/**"]
          - path: CLAUDE.md
          - path: README.md
          - glob: "docs/**"
        dev_only:
          - glob: "framework/tools/pos-publish-framework-only/**"
          - path: CLAUDE.dev.md
        excluded_from_publish: []
        """
    )
    files = {
        "framework/cost-governance/__init__.py": (
            '"""Author Luke Ivers — token in path '
            '/Users/lukeivers/ivers-corp-pos-v2/foo"""\n'
        ),
        "framework/workspace-bootstrap/README.md": (
            "Run from /Users/lukeivers/ivers-corp-pos-v2.\n"
            "GitHub: lukeivers/pos-v2\n"
        ),
        "CLAUDE.md": "# fixture CLAUDE.md\n",
        "CLAUDE.dev.md": "# fixture CLAUDE.dev.md\n",
        "README.md": "# fixture README.md\n",
        "docs/positioning.md": "# fixture\n",
    }
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        files=files,
        manifest_yaml=manifest_yaml,
    )

    result1 = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    assert not result1.no_op
    assert result1.framework_only_sha

    result2 = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    # Second pass MUST no-op (idempotence).
    assert result2.no_op
    assert result2.framework_only_sha == result1.framework_only_sha
