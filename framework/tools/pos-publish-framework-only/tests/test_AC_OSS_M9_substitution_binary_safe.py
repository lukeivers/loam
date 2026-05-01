"""AC.OSS-M9.4 — substitution pass skips binary blobs (UnicodeDecodeError).

Per oss-v0-1-0-publish-scrub.md §4 AC.OSS-M9.4: a fixture canonical
whose ``dev_and_public`` set includes a blob whose first 4 bytes are
``\\x89PNG`` (a real binary blob). The synthesis pass must preserve
that blob's SHA verbatim — the substitution pass attempted UTF-8
decode, raised ``UnicodeDecodeError``, and returned the input bytes
unchanged.

Also covers the ``apply_substitutions`` unit-level binary-flag
behaviour.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam.publish_framework_only.substitution import (
    SUBSTITUTION_TABLE,
    apply_substitutions,
)
from loam.publish_framework_only.synth import synthesise_framework_only


# 1x1 transparent PNG (binary blob; no UTF-8 decode possible because
# the IDAT chunk's compressed bytes carry 0xFF bytes that fail UTF-8
# decode). Generated once, kept inline for test determinism.
PNG_1x1_TRANSPARENT = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
    b"\x89\x00\x00\x00\rIDAT\x78\x9cc\xfc\xff\xff?\x00\x05\xfe\x02\xfe"
    b"\xa3\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_AC_OSS_M9_4_apply_substitutions_marks_binary() -> None:
    """Unit: apply_substitutions on PNG bytes returns binary=True,
    changed=False, content unchanged."""
    result = apply_substitutions(PNG_1x1_TRANSPARENT, SUBSTITUTION_TABLE)
    assert result.binary is True
    assert result.changed is False
    assert result.content == PNG_1x1_TRANSPARENT


def test_AC_OSS_M9_4_synth_preserves_binary_blob_sha(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """Integration: a binary blob in dev_and_public retains its source
    SHA in the synthetic tree."""
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
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        manifest_yaml=manifest_yaml,
    )
    # Add a binary PNG to docs/ (a docs/ asset path).
    img_path = canonical / "docs" / "assets" / "logo.png"
    img_path.parent.mkdir(parents=True, exist_ok=True)
    img_path.write_bytes(PNG_1x1_TRANSPARENT)
    git_run(["add", "-A"], cwd=canonical)
    git_run(["commit", "-m", "add binary PNG"], cwd=canonical)

    source_sha = git_run(
        ["rev-parse", "HEAD:docs/assets/logo.png"], cwd=canonical
    )

    result = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    assert result.framework_only_sha

    tree_listing = git_run(
        ["ls-tree", "-r", "refs/heads/framework-only"],
        cwd=canonical,
    )
    tree_entries: dict[str, str] = {}
    for line in tree_listing.split("\n"):
        if not line:
            continue
        head, _, name = line.partition("\t")
        _, _, sha = head.split(" ")
        tree_entries[name] = sha

    assert "docs/assets/logo.png" in tree_entries
    # Binary blob → SHA preserved verbatim.
    assert tree_entries["docs/assets/logo.png"] == source_sha
